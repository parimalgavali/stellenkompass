import { useState } from 'react'
import { STAGES, STAGE_LABEL, type Stage, type TrackedJob, type Tracker } from '../types'
import { formatDate, fromDateInput, toDateInput } from '../lib/time'

interface Props {
  tracker: Tracker
  liveIds: Set<string>
  onUpdate: (id: string, patch: Partial<TrackedJob>) => void
  onRemove: (id: string) => void
}

export function TrackerPage({ tracker, liveIds, onUpdate, onRemove }: Props) {
  const [stage, setStage] = useState<Stage | ''>('')
  const all = Object.values(tracker).sort((a, b) => b.updatedAt.localeCompare(a.updatedAt))
  const shown = stage ? all.filter((j) => j.stage === stage) : all

  if (all.length === 0) {
    return <p className="empty">Nothing tracked yet. Press Save on a role to add it here.</p>
  }

  return (
    <section>
      <div className="tabs" role="tablist">
        <button role="tab" aria-selected={stage === ''} onClick={() => setStage('')}>
          All <span className="count">{all.length}</span>
        </button>
        {STAGES.map((s) => (
          <button key={s} role="tab" aria-selected={stage === s} onClick={() => setStage(s)}>
            {STAGE_LABEL[s]} <span className="count">{all.filter((j) => j.stage === s).length}</span>
          </button>
        ))}
      </div>
      <div className="list">
        {shown.map((job) => (
          <article key={job.id} className="card card-tracked">
            <div className="card-main">
              <a className="card-title" href={job.url} target="_blank" rel="noreferrer">
                {job.title}
              </a>
              <div className="card-meta">
                <span>{job.company}</span>
                <span>{job.city || job.location}</span>
                <span>Saved {formatDate(job.savedAt)}</span>
                {!liveIds.has(job.id) && <span className="gone">No longer in scan</span>}
              </div>
              <div className="tracked-fields">
                <label>
                  Stage
                  <select value={job.stage} onChange={(e) => onUpdate(job.id, { stage: e.target.value as Stage })}>
                    {STAGES.map((s) => (
                      <option key={s} value={s}>
                        {STAGE_LABEL[s]}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Applied
                  <input
                    type="date"
                    value={toDateInput(job.appliedAt)}
                    onChange={(e) => onUpdate(job.id, { appliedAt: fromDateInput(e.target.value) })}
                  />
                </label>
                <label>
                  Interview
                  <input
                    type="date"
                    value={toDateInput(job.interviewAt)}
                    onChange={(e) => onUpdate(job.id, { interviewAt: fromDateInput(e.target.value), thankYouSent: false })}
                  />
                </label>
              </div>
              <textarea
                placeholder="Notes: contact person, salary, next step…"
                defaultValue={job.notes}
                onBlur={(e) => e.target.value !== job.notes && onUpdate(job.id, { notes: e.target.value })}
                aria-label={`Notes for ${job.title}`}
              />
            </div>
            <button className="link danger" onClick={() => onRemove(job.id)} aria-label={`Remove ${job.title}`}>
              Remove
            </button>
          </article>
        ))}
      </div>
    </section>
  )
}
