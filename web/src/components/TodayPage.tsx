import { findTracked } from '../lib/tracker'
import type { Job, Profile, TrackedJob, Tracker } from '../types'
import { todayItems, type TodayItem } from '../lib/today'
import { JobCard } from './JobCard'

interface Props {
  tracker: Tracker
  newMatches: Job[]
  profile: Profile
  onUpdate: (id: string, patch: Partial<TrackedJob>) => void
  onSave: (job: Job) => void
}

const TITLE: Record<TodayItem['kind'], string> = {
  interview: 'Upcoming interview',
  thank_you: 'Thank-you note',
  follow_up: 'Follow up',
  apply_or_close: 'Apply or close',
}

function Actions({ item, onUpdate }: { item: TodayItem; onUpdate: Props['onUpdate'] }) {
  const id = item.job.id
  switch (item.kind) {
    case 'follow_up':
      return <button className="btn" onClick={() => onUpdate(id, {})}>Followed up</button>
    case 'thank_you':
      return <button className="btn" onClick={() => onUpdate(id, { thankYouSent: true })}>Sent</button>
    case 'apply_or_close':
      return (
        <>
          <button className="btn" onClick={() => onUpdate(id, { stage: 'applied' })}>Applied</button>
          <button className="btn btn-quiet" onClick={() => onUpdate(id, { stage: 'closed' })}>Close</button>
        </>
      )
    default:
      return null
  }
}

export function TodayPage({ tracker, newMatches, profile, onUpdate, onSave }: Props) {
  const items = todayItems(tracker)
  return (
    <section>
      <h2>To do</h2>
      {items.length === 0 ? (
        <p className="empty">Nothing due today. Nice.</p>
      ) : (
        <div className="list">
          {items.map((item) => (
            <article key={`${item.kind}-${item.job.id}`} className="card">
              <div className="card-main">
                <div className="eyebrow">{TITLE[item.kind]}</div>
                <a className="card-title" href={item.job.url} target="_blank" rel="noreferrer">
                  {item.job.title}
                </a>
                <div className="card-meta">
                  <span>{item.job.company}</span>
                  <span>{item.text}</span>
                </div>
              </div>
              <div className="actions">
                <Actions item={item} onUpdate={onUpdate} />
              </div>
            </article>
          ))}
        </div>
      )}
      <h2>New matches since your last visit</h2>
      {newMatches.length === 0 ? (
        <p className="empty">
          {profile.keywords.length + profile.companies.length
            ? 'No new matches.'
            : 'Add keywords or companies in Profile to see new matches here.'}
        </p>
      ) : (
        <div className="list">
          {newMatches.slice(0, 30).map((job) => (
            <JobCard key={job.id} job={job} profile={profile} tracked={findTracked(tracker, job)} onSave={onSave} />
          ))}
        </div>
      )}
    </section>
  )
}
