# Checklist

Updated after every PR. `[x]` = done and merged.

## Phase 0: Research and setup
- [x] Read REA (Reverse Engineer Anything) and its responsible-use rules
- [x] Study Arbeit49, Arbeitnow, workingstudentjobs.de, Astra → [RESEARCH.md](RESEARCH.md)
- [x] Check which public job sources respond → [DATA_SOURCES.md](DATA_SOURCES.md)
- [x] Decide: no login, no payments, static site + daily scan → [DECISIONS.md](DECISIONS.md)
- [x] Create repo `parimalgavali/stellenkompass` with plan, research, decisions, checklist

## Phase 1: Scanner
- [ ] Python project (`scanner/`), lint (ruff), tests (pytest), CI on GitHub Actions
- [ ] Common job format + Germany filter + language and job-type detection
- [ ] Adapter: Arbeitnow
- [ ] Adapter: Greenhouse
- [ ] Adapter: Ashby
- [ ] Adapter: SmartRecruiters
- [ ] Adapter: Lever
- [ ] Adapter: Personio
- [ ] Remove duplicates across sources
- [ ] Write `data/jobs.json` + `data/scan_report.json` (counts and errors per source)

## Phase 2: Web app v1
- [x] React + Vite + TypeScript app (`web/`), lint, tests
- [x] Jobs list with search and filters (language, city, job type, remote, source, posted)
- [x] My profile: keywords + followed companies (browser only), match highlight
- [x] Tracker: Saved → Applied → Interview → Offer / Rejected, dates, notes
- [x] Today view: follow-ups, interviews, new matches
- [x] Export / import personal data (JSON)
- [x] Light/dark theme, works on phone

## Phase 3: Daily automation and hosting
- [ ] Daily scan workflow commits fresh `jobs.json`
- [ ] Deploy to GitHub Pages (Parimal enables Pages: Settings → Pages → Source: GitHub Actions)
- [ ] Scan health shown in the app

## Phase 4: Better matching (v2)
- [ ] CV upload (in browser) + fit score
- [ ] Skill tags per role
- [ ] More company boards
- [ ] Try Bundesagentur für Arbeit API from GitHub Actions

## Phase 5: AI help (v2, optional)
- [ ] Apply kit per role with the user's own LLM key
