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

## D9. Bundesagentur für Arbeit via search terms (2026-11-03)
- Decision: read the BA Jobsuche API v6 with a list of search terms in `companies.yaml` (tech, data, AI, Werkstudent, Praktikum, Abschlussarbeit), last 30 days, max 500 roles per term, Germany only. Keep regular jobs and internships; drop apprenticeships and self-employment. Language is `de`, link is the BA job page. Company boards win in dedupe.
- Why: the BA is the biggest German job board (~1M postings), so a full copy would bury the roles we care about and make `jobs.json` huge. Search terms keep it focused and are easy to change. The earlier "403" was the retired v4 path, not a block, so it works from GitHub Actions too.

## D10. Adopt the source review: fix correctness before adding sources (2026-11-03)
- Decision: follow [research/source-expansion-handoff.md](research/source-expansion-handoff.md). First job identity, safe scans, geography and UI search (Phases 5–8), then new boards and platforms. The catalog is a backlog; sources are enabled one at a time after verification. Drop the "3 roles minimum" rule.
- Deviations: (1) the BA source stays on (the review predates it); it uses the public key from the BA's own apps, with the caveat in DATA_SOURCES. (2) We start with a smaller state model than the review sketches: exact source ids + aliases + one compact scanner state file outside `data/`, and add freshness fields only when a feature needs them.
- Why: the review found real bugs we confirmed in code (dedupe merges distinct openings, prefix-based carry-over, output written before validation). Adding more sources on top would multiply them.

## D11. Job identity and aliases (2026-11-03)
- Ids stay `source:board-job_id` (aggregators `source:job_id`), so saved roles keep working. New fields: `source_board`, `source_job_id`, `aliases`.
- Dedupe: same id → one job. Same company/title/city on several sources → keep all jobs of the best-ranked source (different ids there are different openings); other sources' ids become `aliases`.
- Each scan merges the previous scan's id and aliases into `aliases`, and `first_seen` is the earliest date over them. The web app finds a tracker entry by id or alias.
- Carry-over of a failed board matches `source` + `source_board` exactly (old rows without `source_board` fall back to the id prefix once).
- Not yet: roles removed by dedupe are not stored, so a failed aggregator can't bring back copies that were only aliases (Phase 6 state file).

## D12. Safe scans (2026-11-03)
- A source fetcher raises `Capped(raw, carry)` when it stops at its page limit (Arbeitnow 30 pages, SmartRecruiters 20). The roles it got are kept, and last scan's roles from that board that are missing now are carried over, like a failed board.
- The BA is capped by design (`max_per_query` is a search sample), so its cap is reported but nothing is carried, or old BA roles would never expire.
- `records()` checks the response shape: a missing record list is a failure (and is carried over), not an empty board. Records without an id, title or URL are skipped.
- `write_outputs` validates (not empty, unique ids, title/url/source set) and writes via temp file + `os.replace`. On failure the scan exits 1 and the old files stay.
- Report: per-source `status` (complete / partial / failed) and `capped`; top-level `collected`, `carried`, `duplicates_removed`.

## D13. Country per location and workplace type (2026-11-03)
- `in_germany(locations, country_codes)`: `country_codes[i]` belongs to `locations[i]`. A coded location is decided by its code only (Frankfurt + US is out, an unlisted town + DE is in). Uncoded locations are still read as text (city list, "Germany", states). One German location is enough.
- Ashby reads the country from `address.postalAddress` or a flat `address` (secondary locations), and trusts `workplaceType` over `isRemote`.
- `workplace_type` comes from the source (Ashby, Lever, SmartRecruiters, Arbeitnow) or from "hybrid"/"remote" in the location text. BA "Homeoffice möglich" counts as hybrid. The web app shows a Hybrid chip; the Remote filter means fully remote.
- Effect (test scan): Ashby 422 → 388. The 34 dropped roles are "Remote · Europe"-style postings whose locations all carry non-German codes (ElevenLabs, Synthesia, Linear, Cohere). Remote roles scoped to "Europe/EMEA" without codes are still kept by text. Phase 12 adds explicit remote-Europe eligibility.
- Not yet: no municipality/postcode list for uncoded small towns.

## D14. Search and language labels (2026-11-03)
- Text search covers title, company, location, snippet, tags and skills, so towns outside our city list can be found by name. The city filter lists every city in the scan.
- The language filter and chips say "English ad" / "German ad": `language` is the posting's language, and an English ad can still require German.

## D15. Recruitee and Teamtailor (2026-11-03)
- Recruitee: `/api/offers/`; id = offer `id`, url = `careers_url`, one country code per entry in `locations`. Workplace from the `remote` / `hybrid` / `on_site` flags (hybrid, or remote + on-site → hybrid).
- Teamtailor: `jobs.rss`; id = RSS `guid` (never title/date), country per `tt:location`, `remoteStatus` fully / hybrid / none → remote / hybrid / onsite. Paged with `offset` + `per_page=100`; stopping at 20 pages raises `Capped`. The board is the careers host (`name` → `name.teamtailor.com`, or a custom host with a dot).
- Tenants: found by guessing and from links in Arbeitnow ads, then checked for roles in Germany. Few German tenants so far; add more as they are found (one role is enough).

## D16. Board options: Lever EU, Personio domain and languages (2026-11-03)
- Any key on a board entry besides `board` and `name` is passed to the adapter's `fetch` as a keyword option. Old entries need no change.
- Lever: `region: eu` → `api.eu.lever.co`. Postings are paged (`skip` + `limit=100`, max 20 pages → `Capped`).
- Personio: `domain` is `jobs.personio.de` (default) or `jobs.personio.com`; with `languages`, one feed per language is fetched and merged by position id (first language gives the title, all add description text, so ids don't change).
- No EU Lever tenant with German roles is configured yet; .de and .com serve the same Personio feed for today's boards.

## D17. SmartRecruiters job text from posting details, cached via last scan (2026-11-03)
- The list route has no job text, so German postings get their detail (`ref`, only on `api.smartrecruiters.com`); its `jobAd.sections` become the description (snippet, skills, fit score).
- Cache = last `jobs.json`: adapters with `USES_PREVIOUS` get last scan's jobs as `known`. Same id and same `releasedDate` → reuse snippet and skills, no request. No separate cache file.
- At most 150 new detail requests per board and run (`MAX_DETAILS`); the rest get text on later runs.
- A failed detail keeps the role and its previous text; failures are logged as a warning.

## D18. University/research pilot: inventory first, d.vinci for KIT (2026-11-03)
- `docs/research/institutions.md` records each pilot institution as `enabled`, `pending` or `blocked`. A portal without a working collector is never counted as covered.
- robots.txt and HTTP 403 are respected: TUM, Fraunhofer, DLR and DFKI stay `blocked`.
- d.vinci (`/jobPublication/list.json`) is the public feed its job widgets load. It isn't documented publicly, so it's treated like any public widget feed, and the adapter fails safely if the shape changes.
- Ausbildung/dual-study places are skipped (as in D9). Contact persons in the feed are never stored.
- One role per `jobOpening.id`: the English ad is kept if there is one; the other language ads add their text and become aliases.

## D19. Workday via its public CXS route (2026-11-03)
- Idea from career-ops (`docs/research/reference-projects.md`); our own code. The route is what the career site itself calls; robots.txt allows the site paths.
- Config: `board` = tenant, plus `instance` (`wd3`, …) and `site` from the careers URL.
- Germany: the `locationCountry`-style facet if the site has one, else every `locations` facet value naming Germany; those roles get country DE. Without either, all roles are read and decided by location text (capped at 50 pages, so big global tenants without a facet aren't added).
- No job text in the list (no detail requests for now), so skills come from the title only. "Posted 30+ Days Ago" gives no date.

## D20. SAP SuccessFactors via the tile route (2026-11-03)
- Idea from career-ops; our own code. `/tile-search-results/` is the fragment the site's search page loads and is not disallowed by robots.txt. The JSON search under `/services/` is disallowed, so it is never used (this keeps DLR and SAP out).
- `country: DE` per board sends the Germany facet; only set where the facet was checked to work (some sites ignore it). Otherwise the country comes from "City, DE, PLZ" fields, or the location text.
- Paging advances by the tiles returned and stops when a page adds no new ids. ZF and Volkswagen repeat pages, so they are not added.
- City falls back to the job URL slug. Ausbildung/dual study skipped (D9). No job text yet.

## D21. softgarden widget; join.com later (2026-11-03)
- softgarden: the job widget that company careers sites embed (`/de/widgets/jobs`), our own parser. No country field, so Germany comes from the city text. Title-only skills. Only RENK found so far (58 roles); tenants are added one by one.
- join.com: its public GraphQL route is allowed by robots.txt, but none of our or the reference list's companies use it, and its company sitemap (14k slugs) has no country. Deferred until we have German companies on it. Superseded by D26.

## D22. Seniority from the title (2026-11-03)
- Idea from the reference projects' level filters; our own rules in `classify.detect_seniority`.
- Levels: `lead` (Lead, Head of, Principal, Director, Staff engineer, Teamleiter/Leitung), `senior` (Senior, Sr.), `junior` (Junior, Jr.), `graduate` (Graduate, Trainee, Entry level, Berufseinsteiger, Absolvent, Direkteinstieg). First match wins in that order; empty when the title doesn't say (most roles).
- Title only: job text often mentions other levels ("you'll work with senior engineers"). The filter shows only roles with that exact level, so unlabelled roles are hidden when a level is picked.

## D23. Years of experience as a hint (2026-11-03)
- Idea from career-ops `jd-years`; our own rules in `classify.detect_experience_years`.
- Reads "3+ years of experience", "2-4 years … experience", "mindestens 3 Jahre Berufserfahrung", "Erfahrung von drei Jahren" (digits and one–eight / ein–sechs). The smallest match wins (the entry bar); values above 15 are ignored, since they are usually the company's age.
- Shown as a chip only; no role is dropped. Only roles with job text can have it (BA and SuccessFactors/softgarden lists have titles only).

## D24. Roles that left the scan (2026-11-03)
- Idea from career-ops liveness checks, done without extra requests: a Saved or Applied role whose id and aliases are not in the latest `jobs.json` shows on Today as "Role may have closed", with **Close** or **Still open** (`stillOpen` stops the reminder).
- Nothing is flagged while jobs are loading or failed to load. A source that failed keeps its roles by carry-over (D6), so a failed scan doesn't flag them either.

## D25. Application deadlines (2026-11-03)
- Idea from career-ops `closing-soon`; our own rules in `classify.detect_deadline` / `clean_deadline`.
- Source field first: d.vinci `endDate` (end of the publication, KIT). Otherwise the ad text: a cue (Bewerbungsfrist, Bewerbungsschluss, Application deadline, Closing date, "bewerben Sie sich bis", "apply by/before/until") followed within 40 characters by a date (30.11.2026, 2026-11-30, December 16, 2026, 15. Januar 2027).
- Past dates and dates over a year ahead are dropped. Few ads have one (about 0.5% of Greenhouse ads).
- Web: "Closes in N days" chip within 30 days; Today shows a saved role closing within 3 days as "Closing soon". The deadline is copied into the tracker when you save.

## D26. JOIN from public company pages (2026-11-03)
- Prompted by Firecrawl Alexandria listing JOIN as a job provider (`docs/research/alexandria.md`); our own code, no Firecrawl.
- `join.com/companies/<slug>?page=N` embeds the job list as Next.js page data (five per page, `pageData` or `initialState`). robots.txt only disallows `/*/lp/`, so the GraphQL route isn't needed.
- Each job has a country code, city, workplace type and employment type, so Germany is decided by the code (D13). Apprenticeships are skipped (D9). No ad text yet, so skills come from the title only.
- Boards come from the public company sitemap (13.5k companies, 9.7k with roles in Germany, mostly trades, care and retail). Only the 393 whose German roles on page 1 are all tech (software, IT, data, SAP, product) are added; that's about 450 requests, roughly 6 more minutes per daily scan.
