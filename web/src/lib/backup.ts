import { STAGES, type Profile, type Tracker } from '../types'

export interface Backup {
  app: 'stellenkompass'
  version: 1
  exportedAt: string
  profile: Profile
  tracker: Tracker
}

export function makeBackup(profile: Profile, tracker: Tracker, now: Date = new Date()): Backup {
  return { app: 'stellenkompass', version: 1, exportedAt: now.toISOString(), profile, tracker }
}

const isStringArray = (v: unknown): v is string[] => Array.isArray(v) && v.every((x) => typeof x === 'string')

export function parseBackup(text: string): Backup {
  let data: unknown
  try {
    data = JSON.parse(text)
  } catch {
    throw new Error('This file is not valid JSON.')
  }
  const d = data as Partial<Backup>
  if (!d || d.app !== 'stellenkompass' || d.version !== 1) {
    throw new Error('This is not a Stellenkompass backup file.')
  }
  if (!d.profile || !isStringArray(d.profile.keywords) || !isStringArray(d.profile.companies)) {
    throw new Error('The profile in this file is broken.')
  }
  if (d.profile.skills !== undefined && !isStringArray(d.profile.skills)) {
    throw new Error('The skills in this file are broken.')
  }
  if (!d.tracker || typeof d.tracker !== 'object') throw new Error('The tracker in this file is broken.')
  for (const [id, job] of Object.entries(d.tracker)) {
    if (!job || job.id !== id || typeof job.title !== 'string' || !STAGES.includes(job.stage)) {
      throw new Error(`Tracked role "${id}" in this file is broken.`)
    }
  }
  return d as Backup
}

const union = (a: string[], b: string[]) => {
  const seen = new Set(a.map((x) => x.toLowerCase()))
  return [...a, ...b.filter((x) => !seen.has(x.toLowerCase()))]
}

export function mergeBackup(profile: Profile, tracker: Tracker, incoming: Backup): { profile: Profile; tracker: Tracker } {
  const merged: Tracker = { ...tracker }
  for (const [id, job] of Object.entries(incoming.tracker)) {
    if (!merged[id] || job.updatedAt > merged[id].updatedAt) merged[id] = job
  }
  const skills = union(profile.skills ?? [], incoming.profile.skills ?? [])
  return {
    profile: {
      keywords: union(profile.keywords, incoming.profile.keywords),
      companies: union(profile.companies, incoming.profile.companies),
      ...(skills.length ? { skills } : {}),
    },
    tracker: merged,
  }
}
