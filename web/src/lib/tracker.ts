import type { Job, Stage, TrackedJob, Tracker } from '../types'

/** The tracker entry for a job, also when it was saved under an older id or another source. */
export function findTracked(tracker: Tracker, job: Job): TrackedJob | undefined {
  for (const id of [job.id, ...(job.aliases ?? [])]) if (tracker[id]) return tracker[id]
  return undefined
}

/** Every id under which a role in the current scan can be tracked. */
export function liveIdSet(jobs: Job[]): Set<string> {
  return new Set(jobs.flatMap((j) => [j.id, ...(j.aliases ?? [])]))
}

export function trackJob(tracker: Tracker, job: Job, now: Date = new Date()): Tracker {
  if (findTracked(tracker, job)) return tracker
  const at = now.toISOString()
  const entry: TrackedJob = {
    id: job.id,
    title: job.title,
    company: job.company,
    city: job.city,
    location: job.location,
    url: job.url,
    stage: 'saved',
    savedAt: at,
    updatedAt: at,
    notes: '',
    ...(job.deadline ? { deadline: job.deadline } : {}),
  }
  return { ...tracker, [job.id]: entry }
}

export function updateTracked(tracker: Tracker, id: string, patch: Partial<TrackedJob>, now: Date = new Date()): Tracker {
  const current = tracker[id]
  if (!current) return tracker
  const next: TrackedJob = { ...current, ...patch, updatedAt: now.toISOString() }
  if (patch.stage === 'applied' && !next.appliedAt) next.appliedAt = now.toISOString()
  return { ...tracker, [id]: next }
}

export function setStage(tracker: Tracker, id: string, stage: Stage, now: Date = new Date()): Tracker {
  return updateTracked(tracker, id, { stage }, now)
}

export function untrack(tracker: Tracker, id: string): Tracker {
  const next = { ...tracker }
  delete next[id]
  return next
}
