import type { Job, Profile, TrackedJob } from '../types'
import { JOB_TYPE_LABEL, SENIORITY_LABEL, STAGE_LABEL } from '../types'
import { matchJob } from '../lib/match'
import { fitScore } from '../lib/skills'
import { relativeTime } from '../lib/time'

interface Props {
  job: Job
  profile: Profile
  tracked?: TrackedJob
  onSave: (job: Job) => void
}

const MAX_SKILLS = 5

export function JobCard({ job, profile, tracked, onSave }: Props) {
  const match = matchJob(job, profile)
  const matched = new Set(match?.keywords.map((k) => k.toLowerCase()))
  const skills = (job.skills ?? []).filter((s) => !matched.has(s.toLowerCase())).slice(0, MAX_SKILLS)
  const mine = new Set((profile.skills ?? []).map((s) => s.toLowerCase()))
  const fit = fitScore(job, profile.skills ?? [])
  return (
    <article className="card">
      <div className="card-main">
        <a className="card-title" href={job.url} target="_blank" rel="noreferrer">
          {job.title}
        </a>
        <div className="card-meta">
          <span className={match?.company ? 'followed' : undefined}>{job.company}</span>
          <span>{job.city || job.location}</span>
          {job.posted_at && <span>{relativeTime(job.posted_at)}</span>}
        </div>
        <div className="chips">
          {fit !== null && (
            <span className="chip chip-fit" title="Share of this role's skills that are in your profile">
              Fit {fit}%
            </span>
          )}
          <span className="chip">{JOB_TYPE_LABEL[job.job_type]}</span>
          {job.seniority && <span className="chip">{SENIORITY_LABEL[job.seniority]}</span>}
          <span className="chip" title="Language of the job ad, not of the job">{job.language === 'de' ? 'German ad' : 'English ad'}</span>
          {job.remote && <span className="chip">Remote</span>}
          {job.workplace_type === 'hybrid' && <span className="chip">Hybrid</span>}
          {match?.keywords.map((k) => (
            <span key={k} className="chip chip-match">
              {k}
            </span>
          ))}
          {match?.company && <span className="chip chip-match">Followed</span>}
          {skills.map((s) => (
            <span key={s} className={mine.has(s.toLowerCase()) ? 'chip chip-skill chip-have' : 'chip chip-skill'}>
              {s}
            </span>
          ))}
        </div>
      </div>
      <button
        className={tracked ? 'btn btn-quiet' : 'btn'}
        onClick={() => onSave(job)}
        disabled={!!tracked}
        aria-label={tracked ? `In tracker: ${STAGE_LABEL[tracked.stage]}` : `Save ${job.title}`}
      >
        {tracked ? STAGE_LABEL[tracked.stage] : 'Save'}
      </button>
    </article>
  )
}
