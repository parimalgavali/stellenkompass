import { describe, expect, it } from 'vitest'
import { EMPTY_FILTERS, filterJobs, sortByFit, sortNewest, topValues } from './filters'
import { matchJob } from './match'
import { newMatches, todayItems } from './today'
import { makeBackup, mergeBackup, parseBackup } from './backup'
import { canonicalSkills, extractSkills, fitScore } from './skills'
import { findTracked, liveIdSet, setStage, trackJob, updateTracked } from './tracker'
import { relativeTime } from './time'
import { JOBS, NOW, job } from '../test/data'
import type { Tracker } from '../types'

const noProfile = { keywords: [], companies: [] }
const days = (n: number) => new Date(NOW.getTime() - n * 86400000).toISOString()

describe('filters', () => {
  it('searches title, company and tags', () => {
    expect(filterJobs(JOBS, { ...EMPTY_FILTERS, q: 'react' }, noProfile, NOW).map((j) => j.company)).toEqual(['Pigment'])
    expect(filterJobs(JOBS, { ...EMPTY_FILTERS, q: 'parloa machine' }, noProfile, NOW)).toHaveLength(1)
  })
  it('combines filters', () => {
    const f = { ...EMPTY_FILTERS, language: 'en' as const, remote: true }
    expect(filterJobs(JOBS, f, noProfile, NOW).map((j) => j.id)).toEqual(['lever:y-3'])
    expect(filterJobs(JOBS, { ...EMPTY_FILTERS, postedWithin: 7 }, noProfile, NOW)).toHaveLength(2)
    expect(filterJobs(JOBS, { ...EMPTY_FILTERS, jobType: 'working_student' }, noProfile, NOW)[0].city).toBe('Munich')
  })

  it('filters by seniority and treats a missing level as unknown', () => {
    const jobs = [job({ id: 'a', seniority: 'senior' }), job({ id: 'b', seniority: '' }), job({ id: 'c' })]
    expect(filterJobs(jobs, { ...EMPTY_FILTERS, seniority: 'senior' }, noProfile, NOW).map((j) => j.id)).toEqual(['a'])
    expect(filterJobs(jobs, EMPTY_FILTERS, noProfile, NOW)).toHaveLength(3)
  })
  it('keeps only matches when asked', () => {
    const f = { ...EMPTY_FILTERS, matchesOnly: true }
    expect(filterJobs(JOBS, f, { keywords: ['machine learning'], companies: [] }, NOW)).toHaveLength(1)
  })
  it('filters by skill and searches skills', () => {
    expect(filterJobs(JOBS, { ...EMPTY_FILTERS, skill: 'Airflow' }, noProfile, NOW).map((j) => j.id)).toEqual(['greenhouse:acme-1'])
    expect(filterJobs(JOBS, { ...EMPTY_FILTERS, q: 'airflow' }, noProfile, NOW)).toHaveLength(1)
    expect(filterJobs([job({ skills: undefined })], { ...EMPTY_FILTERS, skill: 'Airflow' }, noProfile, NOW)).toHaveLength(0)
  })
  it('counts skills across roles', () => {
    expect(topValues([...JOBS, job({ id: 'b' })], (j) => j.skills ?? [])[0]).toEqual(['Python', 2])
  })
  it('sorts newest first', () => {
    expect(sortNewest(JOBS)[0].id).toBe('lever:y-3')
  })
})

describe('matchJob', () => {
  it('matches whole words, case- and accent-insensitive', () => {
    expect(matchJob(job(), { keywords: ['data engineer', 'sql'], companies: [] })?.keywords).toEqual(['data engineer', 'sql'])
    expect(matchJob(job({ title: 'Database admin', tags: [] }), { keywords: ['data'], companies: [] })).toBeNull()
    expect(matchJob(job({ title: 'Büro Manager', tags: [] }), { keywords: ['buro'], companies: [] })).not.toBeNull()
    expect(matchJob(job({ tags: [] }), { keywords: ['airflow'], companies: [] })?.keywords).toEqual(['airflow'])
  })
  it('matches followed companies', () => {
    expect(matchJob(job({ company: 'N26 GmbH' }), { keywords: [], companies: ['n26'] })?.company).toBe(true)
    expect(matchJob(job({ company: 'Acmeco' }), { keywords: [], companies: ['acme'] })).toBeNull()
  })
})

describe('tracker and today', () => {
  it('flags saved and applied roles that left the scan, unless you kept them', () => {
    let t = trackJob({}, job({ id: 'a' }), NOW)
    t = setStage(trackJob(t, job({ id: 'b' }), NOW), 'b', 'applied', NOW)
    t = updateTracked(trackJob(t, job({ id: 'c' }), NOW), 'c', { stillOpen: true }, NOW)
    t = trackJob(t, job({ id: 'd' }), NOW)
    const items = todayItems(t, NOW, new Set(['d']))
    expect(items.map((i) => `${i.kind}:${i.job.id}`).sort()).toEqual(['gone:a', 'gone:b'])
    expect(todayItems(t, NOW).some((i) => i.kind === 'gone')).toBe(false)
  })

  it('saves, sets applied date when stage becomes applied', () => {
    let t: Tracker = trackJob({}, job(), NOW)
    expect(t[job().id].stage).toBe('saved')
    t = setStage(t, job().id, 'applied', NOW)
    expect(t[job().id].appliedAt).toBe(NOW.toISOString())
  })

  it('lists follow-ups, interviews, thank-yous and stale saves', () => {
    const base = trackJob({}, job(), NOW)[job().id]
    const tracker: Tracker = {
      a: { ...base, id: 'a', stage: 'applied', appliedAt: days(10), updatedAt: days(10) },
      b: { ...base, id: 'b', stage: 'applied', appliedAt: days(3), updatedAt: days(3) },
      c: { ...base, id: 'c', stage: 'interview', interviewAt: days(-2) },
      d: { ...base, id: 'd', stage: 'interview', interviewAt: days(2) },
      e: { ...base, id: 'e', stage: 'interview', interviewAt: days(2), thankYouSent: true },
      f: { ...base, id: 'f', stage: 'saved', savedAt: days(6) },
      g: { ...base, id: 'g', stage: 'saved', savedAt: days(1) },
    }
    const items = todayItems(tracker, NOW).map((i) => `${i.kind}:${i.job.id}`)
    expect(items).toEqual(['interview:c', 'thank_you:d', 'follow_up:a', 'apply_or_close:f'])
  })

  it('follow-up resets after an update', () => {
    const t = { a: { ...trackJob({}, job(), NOW)[job().id], id: 'a', stage: 'applied' as const, updatedAt: days(10) } }
    expect(todayItems(updateTracked(t, 'a', {}, NOW), NOW)).toHaveLength(0)
  })

  it('finds new matches since the last visit', () => {
    const profile = { keywords: ['frontend', 'data'], companies: [] }
    expect(newMatches(JOBS, profile, '2026-11-02T12:00:00Z').map((j) => j.id)).toEqual(['lever:y-3'])
    expect(newMatches(JOBS, profile, null)).toEqual([])
  })
})

describe('backup', () => {
  const profile = { keywords: ['python'], companies: ['N26'] }
  const tracker = trackJob({}, job(), NOW)

  it('round-trips', () => {
    const b = parseBackup(JSON.stringify(makeBackup(profile, tracker, NOW)))
    expect(b.profile).toEqual(profile)
    expect(Object.keys(b.tracker)).toEqual([job().id])
  })

  it('rejects broken files', () => {
    expect(() => parseBackup('nope')).toThrow(/not valid JSON/)
    expect(() => parseBackup('{"app":"other"}')).toThrow(/not a Stellenkompass/)
    const bad = makeBackup(profile, { x: { ...tracker[job().id], stage: 'ghosted' as never } })
    expect(() => parseBackup(JSON.stringify(bad))).toThrow(/broken/)
  })

  it('merges without duplicates and keeps the newer role', () => {
    const newer = updateTracked(tracker, job().id, { notes: 'called' }, new Date(NOW.getTime() + 1000))
    const incoming = makeBackup({ keywords: ['Python', 'react'], companies: [] }, newer)
    const merged = mergeBackup(profile, tracker, incoming)
    expect(merged.profile.keywords).toEqual(['python', 'react'])
    expect(merged.tracker[job().id].notes).toBe('called')
  })
})

it('relativeTime', () => {
  expect(relativeTime(days(0.5), NOW)).toBe('12 h ago')
  expect(relativeTime(days(1), NOW)).toBe('yesterday')
  expect(relativeTime(days(5), NOW)).toBe('5 days ago')
})

describe('skills and fit', () => {
  it('reads skills from CV text with the scanner patterns', () => {
    const cv = 'Python, R and SQL. Built RESTful services in JavaScript. Maschinelles Lernen; R&D team; go-to-market.'
    expect(extractSkills(cv)).toEqual(['Python', 'JavaScript', 'R', 'SQL', 'Machine Learning', 'REST APIs'])
    expect(extractSkills('')).toEqual([])
  })

  it('uses canonical names for known skills', () => {
    expect(canonicalSkills([' python', 'PYTHON', 'Haskell', ''])).toEqual(['Python', 'Haskell'])
  })

  it('scores the share of role skills you have', () => {
    expect(fitScore(job(), ['python', 'SQL'])).toBe(67)
    expect(fitScore(job(), ['Python', 'SQL', 'Airflow', 'Docker'])).toBe(100)
    expect(fitScore(job(), [])).toBeNull()
    expect(fitScore(job({ skills: [] }), ['Python'])).toBeNull()
    expect(fitScore(job({ skills: undefined }), ['Python'])).toBeNull()
  })

  it('sorts best fit first and keeps unscored roles last', () => {
    const jobs = [...JOBS, job({ id: 'none', skills: [] })]
    expect(sortByFit(jobs, ['Machine Learning', 'Python']).map((j) => j.id)).toEqual(['ashby:x-2', 'greenhouse:acme-1', 'lever:y-3', 'none'])
  })

  it('keeps skills in backups', () => {
    const profile = { keywords: [], companies: [], skills: ['Python'] }
    expect(parseBackup(JSON.stringify(makeBackup(profile, {}))).profile.skills).toEqual(['Python'])
    expect(() => parseBackup(JSON.stringify(makeBackup({ ...profile, skills: [1] as never }, {})))).toThrow(/skills/)
    const merged = mergeBackup(profile, {}, makeBackup({ keywords: [], companies: [], skills: ['python', 'SQL'] }, {}))
    expect(merged.profile.skills).toEqual(['Python', 'SQL'])
    expect(mergeBackup({ keywords: [], companies: [] }, {}, makeBackup({ keywords: [], companies: [] }, {})).profile).not.toHaveProperty('skills')
  })
})

describe('job identity', () => {
  it('finds and keeps a saved role after it moves to another source', () => {
    const old = job()
    const t = trackJob({}, old, NOW)
    const moved = { ...old, id: 'greenhouse:acme-9', aliases: [old.id] }
    expect(findTracked(t, moved)?.id).toBe(old.id)
    expect(trackJob(t, moved, NOW)).toBe(t)
    expect(liveIdSet([moved]).has(old.id)).toBe(true)
  })
})

describe('search', () => {
  it('matches location and snippet text', () => {
    const jobs = [job({ id: 'a', location: 'Tettnang, Germany' }), job({ id: 'b', snippet: 'Wir nutzen Kubernetes' })]
    expect(filterJobs(jobs, { ...EMPTY_FILTERS, q: 'tettnang' }, noProfile).map((j) => j.id)).toEqual(['a'])
    expect(filterJobs(jobs, { ...EMPTY_FILTERS, q: 'kubernetes' }, noProfile).map((j) => j.id)).toEqual(['b'])
  })
})
