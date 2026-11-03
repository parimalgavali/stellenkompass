# Decisions

Short records. Newest at the bottom. Format: context → decision → why.

## D1. Build our own, don't copy Arbeit49 (2026-11-03)
- Context: Arbeit49 is paid and closed. REA (Reverse Engineer Anything) can show how features work, but its disclaimer forbids copying proprietary code/assets and bypassing access controls.
- Decision: study public pages and public JS to understand features; write all code ourselves; use only public job sources. No logging into paid areas, no scraping their data, no copying their name or design.
- Why: legal and safe, and we end up with a tool we fully own.

## D2. No login, no payments, no limits (2026-11-03)
- Context: users are me and 4–5 friends.
- Decision: no accounts. Everyone sees the same scanned job list. Personal data (tracker, keywords, followed companies, notes) lives in each person's browser (localStorage) with JSON export/import for backup and moving devices.
- Why: accounts and billing add a backend, a database, security work and costs, for no real benefit at this size. Can be added later if the group grows.

## D3. Static site + scheduled scan (2026-11-03)
- Decision: Python scanner runs in GitHub Actions on a daily schedule and writes `jobs.json`; a React + Vite static site reads it; hosted on GitHub Pages.
- Why: free hosting, nothing to keep running, easy to debug (the data is a file in git).

## D4. Name: Stellenkompass (2026-11-03)
- "Stellen" (German: positions) + "Kompass". Unique, says what it does.

## D5. Web app keeps personal data in the browser (2026-11-03)
- Decision: static React app; profile (keywords, companies) and tracker live in `localStorage`. Profile → Backup exports/imports one JSON file (merge or replace).
- Why: no login and no server (D2, D3); a friend's data never leaves their browser. Tracked roles keep a copy of title, company and link, so they survive after the role leaves the scan.
- Also: hash routing (`#/jobs`, `#/today`, …) so GitHub Pages needs no rewrites; plain CSS with light/dark theme; vitest + Testing Library; oxlint.

## D6. A failed source keeps its last good roles (2026-11-03)
- Decision: when a source or board fails, the scanner copies that board's roles from the previous `jobs.json` and records `carried` in `scan_report.json`. 429s wait for `Retry-After` (max 60 s).
- Why: the first scan from GitHub Actions got HTTP 429 from Arbeitnow and dropped from 2,911 to 1,460 roles. Showing yesterday's roles beats showing none; roles that are really gone vanish after the next good scan.

## D7. Skill tags from a curated list (2026-11-03)
- Decision: `scanner/.../skills.py` holds 72 skills, each with regex aliases (EN + DE, e.g. "maschinelles Lernen" → Machine Learning). Each job gets `skills` from title + full description.
- Why: deterministic, fast and testable; no LLM or API key. It's also the base for the CV fit score: same list, CV skills ∩ role skills.
- Add a skill: one line in `_SKILLS` plus a test case in `tests/test_skills.py`, then `uv run python -m stellenkompass_scanner.skills` to update the web copy (D8).

## D8. CV fit score = share of a role's skills you have (2026-11-03)
- Decision: the CV is read in the browser (pdf.js for PDFs, loaded only when used) and run through the same skill list as the scanner. `web/src/lib/skills.json` is generated from `skills.py` (`uv run python -m stellenkompass_scanner.skills`); a scanner test fails if it drifts. Fit = role skills you have ÷ role skills. Only the skill list is stored (localStorage + backup), never the CV text.
- Why: no server, no upload, no API key, and the score is easy to explain ("you have 2 of its 3 skills"). Roles without skill tags get no score instead of a misleading 0%. An LLM-based score can come later with the apply kit.
