import type { Job } from '../types'

export const NOW = new Date('2026-11-03T08:00:00Z')

export function job(over: Partial<Job> = {}): Job {
  return {
    id: 'greenhouse:acme-1',
    title: 'Data Engineer (m/w/d)',
    company: 'Acme',
    location: 'Berlin, Germany',
    url: 'https://example.com/1',
    source: 'greenhouse',
    city: 'Berlin',
    remote: false,
    job_type: 'full_time',
    language: 'en',
    posted_at: '2026-11-02T08:00:00Z',
    first_seen: '2026-11-02T08:00:00Z',
    tags: ['Python', 'SQL'],
    snippet: '',
    ...over,
  }
}

export const JOBS: Job[] = [
  job(),
  job({ id: 'ashby:x-2', title: 'Werkstudent Machine Learning', company: 'Parloa', city: 'Munich', language: 'de', job_type: 'working_student', source: 'ashby', tags: [], posted_at: '2026-10-01T08:00:00Z', first_seen: '2026-10-01T08:00:00Z' }),
  job({ id: 'lever:y-3', title: 'Frontend Developer', company: 'Pigment', city: 'Hamburg', remote: true, source: 'lever', tags: ['React'], posted_at: '2026-11-03T06:00:00Z', first_seen: '2026-11-03T06:00:00Z' }),
]
