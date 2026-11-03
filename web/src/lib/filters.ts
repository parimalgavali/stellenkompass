import type { Job, Profile } from '../types'
import { matchJob } from './match'
import { DAY } from './time'

export interface Filters {
  q: string
  language: '' | 'en' | 'de'
  city: string
  jobType: string
  remote: boolean
  source: string
  postedWithin: number
  matchesOnly: boolean
}

export const EMPTY_FILTERS: Filters = {
  q: '',
  language: '',
  city: '',
  jobType: '',
  remote: false,
  source: '',
  postedWithin: 0,
  matchesOnly: false,
}

export function filterJobs(jobs: Job[], f: Filters, profile: Profile, now: Date = new Date()): Job[] {
  const terms = f.q.toLowerCase().split(/\s+/).filter(Boolean)
  const cutoff = f.postedWithin ? now.getTime() - f.postedWithin * DAY : 0
  return jobs.filter((job) => {
    if (f.language && job.language !== f.language) return false
    if (f.city && job.city !== f.city) return false
    if (f.jobType && job.job_type !== f.jobType) return false
    if (f.remote && !job.remote) return false
    if (f.source && job.source !== f.source) return false
    if (cutoff && new Date(job.posted_at || job.first_seen).getTime() < cutoff) return false
    if (terms.length) {
      const text = `${job.title} ${job.company} ${job.tags.join(' ')}`.toLowerCase()
      if (!terms.every((t) => text.includes(t))) return false
    }
    if (f.matchesOnly && !matchJob(job, profile)) return false
    return true
  })
}

export function sortNewest(jobs: Job[]): Job[] {
  return [...jobs].sort((a, b) => (b.posted_at || b.first_seen).localeCompare(a.posted_at || a.first_seen))
}

export function topValues(jobs: Job[], pick: (j: Job) => string): [string, number][] {
  const counts = new Map<string, number>()
  for (const j of jobs) {
    const v = pick(j)
    if (v) counts.set(v, (counts.get(v) ?? 0) + 1)
  }
  return [...counts.entries()].sort((a, b) => b[1] - a[1])
}
