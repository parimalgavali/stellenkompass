import type { Job, Profile, TrackedJob } from '../types'
import { JOB_TYPE_LABEL, STAGE_LABEL } from '../types'
import { matchJob } from '../lib/match'
import { relativeTime } from '../lib/time'

interface Props {
  job: Job
  profile: Profile
  tracked?: TrackedJob
  onSave: (job: Job) => void
}

export function JobCard({ job, profile, tracked, onSave }: Props) {
  const match = matchJob(job, profile)
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
          <span className="chip">{JOB_TYPE_LABEL[job.job_type]}</span>
          <span className="chip">{job.language === 'de' ? 'German' : 'English'}</span>
          {job.remote && <span className="chip">Remote</span>}
          {match?.keywords.map((k) => (
            <span key={k} className="chip chip-match">
              {k}
            </span>
          ))}
          {match?.company && <span className="chip chip-match">Followed</span>}
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
