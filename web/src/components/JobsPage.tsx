import { useMemo, useState } from 'react'
import type { Job, Profile, Tracker } from '../types'
import { JOB_TYPE_LABEL } from '../types'
import { EMPTY_FILTERS, filterJobs, sortNewest, topValues, type Filters } from '../lib/filters'
import { JobCard } from './JobCard'

const PAGE = 50

interface Props {
  jobs: Job[]
  profile: Profile
  tracker: Tracker
  onSave: (job: Job) => void
}

export function JobsPage({ jobs, profile, tracker, onSave }: Props) {
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS)
  const [limit, setLimit] = useState(PAGE)
  const set = (patch: Partial<Filters>) => {
    setFilters((f) => ({ ...f, ...patch }))
    setLimit(PAGE)
  }

  const sorted = useMemo(() => sortNewest(jobs), [jobs])
  const cities = useMemo(() => topValues(jobs, (j) => j.city).slice(0, 40), [jobs])
  const sources = useMemo(() => topValues(jobs, (j) => j.source), [jobs])
  const results = useMemo(() => filterJobs(sorted, filters, profile), [sorted, filters, profile])
  const hasProfile = profile.keywords.length + profile.companies.length > 0
  const dirty = JSON.stringify(filters) !== JSON.stringify(EMPTY_FILTERS)

  return (
    <section>
      <input
        className="search"
        type="search"
        placeholder="Search title, company or skill"
        value={filters.q}
        onChange={(e) => set({ q: e.target.value })}
        aria-label="Search"
      />
      <div className="filters">
        <select value={filters.language} onChange={(e) => set({ language: e.target.value as Filters['language'] })} aria-label="Language">
          <option value="">Any language</option>
          <option value="en">English</option>
          <option value="de">German</option>
        </select>
        <select value={filters.city} onChange={(e) => set({ city: e.target.value })} aria-label="City">
          <option value="">All cities</option>
          {cities.map(([c, n]) => (
            <option key={c} value={c}>
              {c} ({n})
            </option>
          ))}
        </select>
        <select value={filters.jobType} onChange={(e) => set({ jobType: e.target.value })} aria-label="Job type">
          <option value="">Any type</option>
          {Object.entries(JOB_TYPE_LABEL).map(([v, l]) => (
            <option key={v} value={v}>
              {l}
            </option>
          ))}
        </select>
        <select value={filters.postedWithin} onChange={(e) => set({ postedWithin: Number(e.target.value) })} aria-label="Posted">
          <option value={0}>Any time</option>
          <option value={1}>Last 24 hours</option>
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
        </select>
        <select value={filters.source} onChange={(e) => set({ source: e.target.value })} aria-label="Source">
          <option value="">All sources</option>
          {sources.map(([s, n]) => (
            <option key={s} value={s}>
              {s} ({n})
            </option>
          ))}
        </select>
        <label className="toggle">
          <input type="checkbox" checked={filters.remote} onChange={(e) => set({ remote: e.target.checked })} />
          Remote
        </label>
        <label className="toggle" title={hasProfile ? '' : 'Add keywords or companies in Profile first'}>
          <input
            type="checkbox"
            checked={filters.matchesOnly}
            disabled={!hasProfile}
            onChange={(e) => set({ matchesOnly: e.target.checked })}
          />
          My matches
        </label>
      </div>
      <div className="results-bar">
        <span>{results.length.toLocaleString('en')} roles</span>
        {dirty && (
          <button className="link" onClick={() => set(EMPTY_FILTERS)}>
            Clear filters
          </button>
        )}
      </div>
      {results.length === 0 ? (
        <p className="empty">No roles match these filters.</p>
      ) : (
        <div className="list">
          {results.slice(0, limit).map((job) => (
            <JobCard key={job.id} job={job} profile={profile} tracked={tracker[job.id]} onSave={onSave} />
          ))}
        </div>
      )}
      {results.length > limit && (
        <button className="btn btn-wide" onClick={() => setLimit((l) => l + PAGE)}>
          Show more
        </button>
      )}
    </section>
  )
}
