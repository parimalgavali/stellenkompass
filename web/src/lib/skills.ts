import type { Job } from '../types'
import rows from './skills.json'

// Same list and patterns as scanner/src/stellenkompass_scanner/skills.py (generated from it).
const PATTERNS = rows.map((r) => ({ name: r.name, re: new RegExp(r.pattern, r.flags) }))
export const SKILL_NAMES = rows.map((r) => r.name)

export function extractSkills(text: string): string[] {
  return PATTERNS.filter((p) => p.re.test(text)).map((p) => p.name)
}

/** Known skill names get their canonical spelling; unknown entries are kept as typed. */
export function canonicalSkills(skills: string[]): string[] {
  const byLower = new Map(SKILL_NAMES.map((n) => [n.toLowerCase(), n]))
  return [...new Set(skills.map((s) => byLower.get(s.trim().toLowerCase()) ?? s.trim()))].filter(Boolean)
}

/** Share of the role's skills that you have, 0-100; null when either side has no skills. */
export function fitScore(job: Job, mySkills: string[]): number | null {
  const wanted = job.skills ?? []
  if (!wanted.length || !mySkills.length) return null
  const have = new Set(mySkills.map((s) => s.toLowerCase()))
  return Math.round((100 * wanted.filter((s) => have.has(s.toLowerCase())).length) / wanted.length)
}
