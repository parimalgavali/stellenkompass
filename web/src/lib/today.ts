import type { Job, Profile, TrackedJob, Tracker } from '../types'
import { matchJob } from './match'
import { daysBetween } from './time'

export type TodayKind = 'interview' | 'thank_you' | 'follow_up' | 'apply_or_close'

export interface TodayItem {
  kind: TodayKind
  job: TrackedJob
  text: string
}

export const FOLLOW_UP_DAYS = 7
export const INTERVIEW_AHEAD_DAYS = 7
export const STALE_SAVED_DAYS = 5

export function todayItems(tracker: Tracker, now: Date = new Date()): TodayItem[] {
  const items: TodayItem[] = []
  for (const job of Object.values(tracker)) {
    if (job.stage === 'interview' && job.interviewAt) {
      const ahead = daysBetween(now, job.interviewAt)
      if (ahead >= -0.5 && ahead <= INTERVIEW_AHEAD_DAYS) {
        const when = ahead < 1 ? 'today' : `in ${Math.ceil(ahead)} days`
        items.push({ kind: 'interview', job, text: `Interview ${when}. Prepare your questions.` })
      } else if (ahead < -0.5 && !job.thankYouSent) {
        items.push({ kind: 'thank_you', job, text: 'Interview done. Send a short thank-you note.' })
      }
    }
    if (job.stage === 'applied') {
      const idle = daysBetween(job.updatedAt || job.appliedAt || job.savedAt, now)
      if (idle >= FOLLOW_UP_DAYS) {
        items.push({ kind: 'follow_up', job, text: `No update for ${Math.floor(idle)} days. Send a follow-up.` })
      }
    }
    if (job.stage === 'saved') {
      const idle = daysBetween(job.savedAt, now)
      if (idle >= STALE_SAVED_DAYS) {
        items.push({ kind: 'apply_or_close', job, text: `Saved ${Math.floor(idle)} days ago. Apply or close it.` })
      }
    }
  }
  const order: TodayKind[] = ['interview', 'thank_you', 'follow_up', 'apply_or_close']
  return items.sort((a, b) => order.indexOf(a.kind) - order.indexOf(b.kind))
}

export function newMatches(jobs: Job[], profile: Profile, since: string | null): Job[] {
  if (!since) return []
  return jobs.filter((j) => j.first_seen > since && matchJob(j, profile))
}
