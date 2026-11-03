import { useEffect, useMemo, useState } from 'react'
import type { Job, JobsFile, Profile, ScanReport, TrackedJob, Tracker } from './types'
import { KEYS, readStored, useStored } from './lib/storage'
import { setStage, trackJob, untrack, updateTracked } from './lib/tracker'
import { newMatches, todayItems } from './lib/today'
import { relativeTime } from './lib/time'
import { JobsPage } from './components/JobsPage'
import { TodayPage } from './components/TodayPage'
import { TrackerPage } from './components/TrackerPage'
import { ProfilePage } from './components/ProfilePage'

const PAGES = ['jobs', 'today', 'tracker', 'profile'] as const
type Page = (typeof PAGES)[number]
const EMPTY_PROFILE: Profile = { keywords: [], companies: [] }

const pageFromHash = (): Page => {
  const h = window.location.hash.replace('#/', '') as Page
  return PAGES.includes(h) ? h : 'jobs'
}

async function getJson<T>(name: string): Promise<T> {
  const res = await fetch(`${import.meta.env.BASE_URL}data/${name}`)
  if (!res.ok) throw new Error(`${name}: HTTP ${res.status}`)
  return res.json() as Promise<T>
}

export default function App() {
  const [page, setPage] = useState<Page>(pageFromHash)
  const [jobsFile, setJobsFile] = useState<JobsFile | null>(null)
  const [report, setReport] = useState<ScanReport | null>(null)
  const [error, setError] = useState('')
  const [profile, setProfile] = useStored<Profile>(KEYS.profile, EMPTY_PROFILE)
  const [tracker, setTracker] = useStored<Tracker>(KEYS.tracker, {})
  const [theme, setTheme] = useStored<'light' | 'dark' | ''>(KEYS.theme, '')
  const [lastVisit] = useState<string | null>(() => readStored<string | null>(KEYS.lastVisit, null))

  useEffect(() => {
    const onHash = () => setPage(pageFromHash())
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [])

  useEffect(() => {
    getJson<JobsFile>('jobs.json')
      .then((data) => {
        setJobsFile(data)
        localStorage.setItem(KEYS.lastVisit, JSON.stringify(data.generated_at))
      })
      .catch((e: Error) => setError(e.message))
    getJson<ScanReport>('scan_report.json').then(setReport, () => setReport(null))
  }, [])

  useEffect(() => {
    if (theme) document.documentElement.dataset.theme = theme
    else delete document.documentElement.dataset.theme
  }, [theme])

  const jobs = useMemo(() => jobsFile?.jobs ?? [], [jobsFile])
  const liveIds = useMemo(() => new Set(jobs.map((j) => j.id)), [jobs])
  const fresh = useMemo(() => newMatches(jobs, profile, lastVisit), [jobs, profile, lastVisit])
  const dueCount = todayItems(tracker).length + fresh.length

  const save = (job: Job) => setTracker((t) => trackJob(t, job))
  const update = (id: string, patch: Partial<TrackedJob>) =>
    setTracker((t) => (patch.stage ? setStage(updateTracked(t, id, patch), id, patch.stage) : updateTracked(t, id, patch)))
  const remove = (id: string) => setTracker((t) => untrack(t, id))
  const isDark = theme === 'dark' || (!theme && window.matchMedia?.('(prefers-color-scheme: dark)').matches)

  const label: Record<Page, string> = {
    jobs: 'Jobs',
    today: dueCount ? `Today · ${dueCount}` : 'Today',
    tracker: Object.keys(tracker).length ? `Tracker · ${Object.keys(tracker).length}` : 'Tracker',
    profile: 'Profile',
  }

  return (
    <div className="app">
      <header className="header">
        <a className="brand" href="#/jobs">
          Stellenkompass
        </a>
        <nav>
          {PAGES.map((p) => (
            <a key={p} href={`#/${p}`} aria-current={page === p ? 'page' : undefined}>
              {label[p]}
            </a>
          ))}
        </nav>
        <button className="theme" onClick={() => setTheme(isDark ? 'light' : 'dark')} aria-label="Toggle dark mode">
          {isDark ? '☀' : '☾'}
        </button>
      </header>

      <main>
        {error && <p className="notice notice-error">Could not load jobs ({error}).</p>}
        {!jobsFile && !error && <p className="empty">Loading roles…</p>}
        {jobsFile && page === 'jobs' && <JobsPage jobs={jobs} profile={profile} tracker={tracker} onSave={save} />}
        {jobsFile && page === 'today' && (
          <TodayPage tracker={tracker} newMatches={fresh} profile={profile} onUpdate={update} onSave={save} />
        )}
        {page === 'tracker' && <TrackerPage tracker={tracker} liveIds={liveIds} onUpdate={update} onRemove={remove} />}
        {page === 'profile' && (
          <ProfilePage
            profile={profile}
            tracker={tracker}
            onProfile={setProfile}
            onRestore={(p, t) => {
              setProfile(p)
              setTracker(t)
            }}
          />
        )}
      </main>

      <footer className="footer">
        {jobsFile && (
          <span title={jobsFile.generated_at}>
            {jobsFile.count.toLocaleString('en')} roles · scanned {relativeTime(jobsFile.generated_at)}
          </span>
        )}
        {report && (
          <span>
            {Object.entries(report.sources)
              .map(([name, s]) => `${name} ${s.jobs}${s.errors.length ? ` (${s.errors.length} failed)` : ''}`)
              .join(' · ')}
          </span>
        )}
      </footer>
    </div>
  )
}
