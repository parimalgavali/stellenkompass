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
- [ ] Enable Pages (Parimal: Settings → Pages → Source: GitHub Actions). Until then the deploy step fails with "Get Pages site failed"; the bot token can't enable it (HTTP 403).
- [x] Working loop documented → [WORKFLOW.md](WORKFLOW.md)
- [x] Scan health shown in the app (footer: last scan time + roles per source)

## Phase 4: Better matching (v2)
- [ ] CV upload (in browser) + fit score
- [ ] Skill tags per role
- [ ] More company boards
- [ ] Try Bundesagentur für Arbeit API from GitHub Actions

## Phase 5: AI help (v2, optional)
- [ ] Apply kit per role with the user's own LLM key
