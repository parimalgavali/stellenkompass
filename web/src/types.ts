export type JobType = 'full_time' | 'part_time' | 'working_student' | 'internship' | 'thesis' | 'other'

export type Seniority = 'graduate' | 'junior' | 'senior' | 'lead'

export interface Job {
  id: string
  title: string
  company: string
  location: string
  url: string
  source: string
  city: string
  remote: boolean
  workplace_type?: 'onsite' | 'hybrid' | 'remote' | 'unknown'
  job_type: JobType
  /** From the title; missing when it doesn't say. */
  seniority?: Seniority | ''
  /** Smallest number of years of experience the ad asks for. */
  experience_years?: number | null
  language: 'en' | 'de'
  posted_at: string
  first_seen: string
  tags: string[]
  skills?: string[]
  snippet: string
  source_board?: string
  source_job_id?: string
  /** Earlier ids of this role, or its copies on other sources. */
  aliases?: string[]
}

export interface JobsFile {
  generated_at: string
  count: number
  jobs: Job[]
}

export interface SourceReport {
  boards: number
  jobs: number
  errors: { board: string; error: string }[]
  carried?: number
  capped?: { board: string; carry: boolean }[]
  status?: 'complete' | 'partial' | 'failed'
  seconds: number
}

export interface ScanReport {
  generated_at: string
  total_jobs: number
  collected?: number
  carried?: number
  duplicates_removed?: number
  sources: Record<string, SourceReport>
}

export interface Profile {
  keywords: string[]
  companies: string[]
  /** Your skills, usually read from your CV; drives the fit score. */
  skills?: string[]
}

export const STAGES = ['saved', 'applied', 'interview', 'offer', 'rejected', 'closed'] as const
export type Stage = (typeof STAGES)[number]

export interface TrackedJob {
  id: string
  title: string
  company: string
  city: string
  location: string
  url: string
  stage: Stage
  savedAt: string
  updatedAt: string
  appliedAt?: string
  interviewAt?: string
  thankYouSent?: boolean
  /** You checked: still open although it left the scan. */
  stillOpen?: boolean
  notes: string
}

export type Tracker = Record<string, TrackedJob>

export const JOB_TYPE_LABEL: Record<JobType, string> = {
  full_time: 'Full-time',
  part_time: 'Part-time',
  working_student: 'Working student',
  internship: 'Internship',
  thesis: 'Thesis',
  other: 'Other',
}

export const SENIORITY_LABEL: Record<Seniority, string> = {
  graduate: 'Graduate / Trainee',
  junior: 'Junior',
  senior: 'Senior',
  lead: 'Lead / Head',
}

export const STAGE_LABEL: Record<Stage, string> = {
  saved: 'Saved',
  applied: 'Applied',
  interview: 'Interview',
  offer: 'Offer',
  rejected: 'Rejected',
  closed: 'Closed',
}
