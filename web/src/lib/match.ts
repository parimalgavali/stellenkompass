import type { Job, Profile } from '../types'

export interface Match {
  keywords: string[]
  company: boolean
}

const norm = (s: string) => s.toLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g, '')

function containsWord(haystack: string, needle: string): boolean {
  const escaped = needle.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  return new RegExp(`(^|[^a-z0-9])${escaped}($|[^a-z0-9])`).test(haystack)
}

export function matchJob(job: Job, profile: Profile): Match | null {
  const text = norm(`${job.title} ${job.tags.join(' ')} ${(job.skills ?? []).join(' ')}`)
  const keywords = profile.keywords.filter((k) => k.trim() && containsWord(text, norm(k.trim())))
  const company = norm(job.company)
  const followed = profile.companies.some((c) => {
    const n = norm(c.trim())
    return n !== '' && (company === n || containsWord(company, n))
  })
  return keywords.length || followed ? { keywords, company: followed } : null
}
