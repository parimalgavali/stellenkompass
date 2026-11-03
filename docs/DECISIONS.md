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

## D5: Web app keeps personal data in the browser

- **Decision:** the web app is a static React app. Profile (keywords, companies) and tracker live in
  `localStorage`. Profile → Backup exports and imports them as one JSON file (merge or replace).
- **Why:** no login and no server (D2, D3). A friend's data never leaves their browser. Tracked roles
  keep a copy of the title, company and link, so they stay after the role drops out of the scan.
- **Also:** hash routing (`#/jobs`, `#/today`, …) so GitHub Pages needs no rewrite rules; plain CSS
  with light/dark themes; vitest + Testing Library for tests; oxlint for lint.
