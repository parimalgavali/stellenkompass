# Checklist

Updated after every PR. `[x]` = done and merged. How we work: [WORKFLOW.md](WORKFLOW.md).

## Phase 0: Research and setup
- [x] Read REA (Reverse Engineer Anything) and its responsible-use rules
- [x] Study Arbeit49, Arbeitnow, workingstudentjobs.de, Astra → [RESEARCH.md](RESEARCH.md)
- [x] Check which public job sources respond → [DATA_SOURCES.md](DATA_SOURCES.md)
- [x] Decide: no login, no payments, static site + daily scan → [DECISIONS.md](DECISIONS.md)
- [x] Create repo `parimalgavali/stellenkompass` with plan, research, decisions, checklist

## Phase 1: Scanner
- [x] Python project (`scanner/`), lint (ruff), tests (pytest), CI on GitHub Actions
- [x] Common job format + Germany filter + language and job-type detection
- [x] Adapter: Arbeitnow
- [x] Adapter: Greenhouse
- [x] Adapter: Ashby
- [x] Adapter: SmartRecruiters
- [x] Adapter: Lever
- [x] Adapter: Personio
- [x] Remove duplicates across sources
- [x] Write `data/jobs.json` + `data/scan_report.json` (counts and errors per source)


First real scan (2026-11-03): 2,911 roles in Germany from 27 boards + Arbeitnow, 113 duplicates removed, 0 source errors, about 1 minute.

## Phase 2: Web app v1
- [x] React + Vite + TypeScript app (`web/`), lint, tests
- [x] Jobs list with search and filters (language, city, job type, remote, source, posted)
- [x] My profile: keywords + followed companies (browser only), match highlight
- [x] Tracker: Saved → Applied → Interview → Offer / Rejected, dates, notes
- [x] Today view: follow-ups, interviews, new matches
- [x] Export / import personal data (JSON)
- [x] Light/dark theme, works on phone

## Phase 3: Daily automation and hosting
- [x] Daily scan workflow commits fresh `jobs.json` (`.github/workflows/daily.yml`, 05:15 Berlin)
- [x] Deploy to GitHub Pages workflow
- [x] Enable Pages (Parimal: Settings → Pages → Source: GitHub Actions; the bot token can't do it, HTTP 403)
- [x] Working loop documented → [WORKFLOW.md](WORKFLOW.md)
- [x] Scan health shown in the app (footer: last scan time + roles per source)
- [x] Failed source keeps last scan's roles; 429s honour `Retry-After` (first live scan lost all Arbeitnow roles to a 429)

## Phase 4: Better matching (v2)
- [x] CV upload (in browser) + fit score: Profile → "Your skills" → Load CV (PDF/text); cards show "Fit N%", jobs list sorts by best fit
- [x] Skill tags per role (scanner `skills.py`, 72 skills with EN/DE aliases; web skill filter + chips)
- [x] More company boards: 63 boards (+37: Trade Republic, Isar Aerospace, Enpal, Aleph Alpha, AUTO1, SIXT, Delivery Hero, 1KOMMA5°, …). Test scan: 4,283 roles, 0 errors, 2 min
- [x] Bundesagentur für Arbeit source (Jobsuche API v6, 16 search terms in `companies.yaml`). Test scan: 8,509 roles (+4,226 from the BA), 0 errors, 3.3 min

## Roadmap after the source review
Plan: [PLANS.md](PLANS.md) phases 5–12. Review: [research/source-expansion-handoff.md](research/source-expansion-handoff.md). Candidates: [research/source-catalog.json](research/source-catalog.json).
- [x] Import the review + catalog, rebuild plan and checklist, drop the "3 roles minimum" rule

### Phase 5: Job identity
- [x] Distinct openings with the same company/title/city survive dedupe
- [x] `source_board` + `source_job_id` on every role; carry-over by exact board (no `foo` vs `foo-bar` mix-up)
- [x] Tracker and `first_seen` survive a job moving to another source (aliases)

### Phase 6: Safe scans
- [x] Source `status` (complete / partial / failed) + `capped` boards in `scan_report.json`
- [x] Capped or failed boards never drop roles; wrong response shape = failure; records without an id are skipped
- [x] Validate before writing; atomic replace of `data/*.json`; `collected` / `carried` / `duplicates_removed` in the report

### Phase 7: Geography
- [ ] Country per location; explicit foreign country beats a city-name match
- [ ] Ashby secondary addresses; German small towns with country DE kept
- [ ] `workplace_type`: onsite / hybrid / remote

### Phase 8: UI discoverability
- [ ] Search includes location; city filter lists all cities
- [ ] Label "English ad" (posting language), not "English only"

### Phase 9: Onboarding + new platforms
- [ ] Re-check skipped boards (Wunderflats, kununu, KONUX, Dataiku, Rasa, HeyJobs, Spotify, Clark)
- [ ] Recruitee adapter
- [ ] Teamtailor adapter (RSS, paginated past 100)

### Phase 10: Adapter depth
- [ ] Lever EU host + pagination
- [ ] Personio `.com` + language variants
- [ ] SmartRecruiters full job text (cached)

### Phase 11: Universities and research
- [ ] Institution inventory (Hochschulkompass) + JobPosting JSON-LD extractor
- [ ] Pilot: TUM, KIT, RWTH, DFKI, Fraunhofer, Max Planck, Helmholtz

### Phase 12: Later sources
- [ ] Public sector (INTERAMT, service.bund.de)
- [ ] Adzuna / Jooble (API keys)
- [ ] Remote-Europe feeds with explicit Germany eligibility

## Phase 13: AI help (optional)
- [ ] Apply kit per role with the user's own LLM key
