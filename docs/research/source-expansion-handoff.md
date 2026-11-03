# Stellenkompass: Germany job-source expansion and implementation handoff

Prepared for Parimal and Devin AI (“Davin” in the request). Review date: 3 November 2026.

Repository: https://github.com/parimalgavali/stellenkompass  
Reviewed main commit: [8ec1f37487bf5405b719d2299b1c4b7afb413b0d](https://github.com/parimalgavali/stellenkompass/commit/8ec1f37487bf5405b719d2299b1c4b7afb413b0d)  
Companion inventory: [stellenkompass-source-catalog.json](stellenkompass-source-catalog.json)

## 1. What to do first

Keep the existing Python scanner, React/Vite frontend, daily GitHub Actions run, and static JSON delivery. The current architecture is a reasonable starting point for a personal Germany job radar. Source expansion does not yet justify a new backend, database service, message queue, plugin framework, or AI-based crawler.

Implement in this order:

1. Stop excluding employers because they have fewer than three German vacancies.
2. Fix vacancy identity, geographic evidence, incomplete scans, and freshness reporting.
3. Add more verified employer boards to the five existing company adapters.
4. Add Recruitee and Teamtailor adapters, with fixtures and complete pagination.
5. Discover all German higher-education institutions from a maintained directory; pilot central careers portals, university IT pages, and department pages.
6. Add research institutes and public-sector sources.
7. Evaluate credentialed aggregator APIs and enterprise careers systems one at a time.
8. Expand remote-Europe eligibility after Germany collection is reliable.

The companion JSON contains **138 candidate source records and the 63 employer-board entries already configured**. These are different kinds of records: platforms, directories, job boards, institutions, agencies, and employer seeds. They do not represent 201 functioning collectors or independently verified live feeds.

**Candidate records are a research backlog, not scanner configuration. Never copy the whole catalog into an enabled scan.** No new candidate tenant was live-validated in this review.

## 2. Scope and evidence

### Reviewed

- Existing repository documentation and source configuration.
- Every scanner source adapter and the shared normalization, geography, HTTP, classification, deduplication, output, and carry-over paths.
- Scanner test coverage and fixtures relevant to those paths.
- Frontend job types, filters, cards, tracker identity, JSON loading, and build/deployment integration.
- Official documentation for the principal proposed feeds and APIs.
- The open PR list solely to identify the concurrent CV-fit work.

[PR #20: Add CV fit score per role](https://github.com/parimalgavali/stellenkompass/pull/20) was open when inspected. Its implementation was not reviewed. Rebase later implementation work against current main and coordinate changes to shared job types, skills, filtering, profile, and backup code.

### Executed

Against a local read-only-purpose snapshot of the pinned commit:

```bash
cd scanner
PYTHONPATH=src python3 -m pytest -q \
  tests/test_sources.py tests/test_geo.py tests/test_classify.py \
  tests/test_http.py tests/test_skills.py
```

Result: **55 passed** under local Python 3.14.3.

Three additional assert-based checks reproduced:

- Two distinct Greenhouse IDs sharing employer, title, and city become one result.
- An explicit US country code is overridden by a German city-name match.
- An Ashby job with a German secondary address in the documented flat shape, in an unlisted town, is rejected.

These checks establish specific behavior, not the frequency of those problems in production.

### Not executed

- Full scanner suite: the local environment lacked PyYAML and uv. Installing PyYAML in a temporary directory failed because package-index DNS/network access was unavailable. In particular, the run/config/output tests were inspected but not executed.
- Ruff, frontend tests, frontend build, full live scan, browser QA, production deployment, or end-to-end source access checks.
- A separate audit of CV matching, security, accessibility, or all application-tracker features.
- A live enumeration of every German employer, university, or vacancy.

No repository code was changed, no PR was opened, and no jobs were applied to.

## 3. How the current implementation works

### 3.1 Repository map

| File or area | Current responsibility | Expansion work belongs here |
| --- | --- | --- |
| [scanner/companies.yaml](https://github.com/parimalgavali/stellenkompass/blob/8ec1f37487bf5405b719d2299b1c4b7afb413b0d/scanner/companies.yaml) | Employer board identifiers grouped by platform | Add verified boards; later add a small amount of endpoint metadata |
| [scanner/src/stellenkompass_scanner/sources/__init__.py](https://github.com/parimalgavali/stellenkompass/blob/8ec1f37487bf5405b719d2299b1c4b7afb413b0d/scanner/src/stellenkompass_scanner/sources/__init__.py) | PER_COMPANY and AGGREGATORS registries | Register each new source explicitly |
| [scanner/src/stellenkompass_scanner/sources/_common.py](https://github.com/parimalgavali/stellenkompass/blob/8ec1f37487bf5405b719d2299b1c4b7afb413b0d/scanner/src/stellenkompass_scanner/sources/_common.py) | build_job: Germany gate, normalization, skills, snippet | Preserve geographic evidence and additive normalized fields |
| [scanner/src/stellenkompass_scanner/models.py](https://github.com/parimalgavali/stellenkompass/blob/8ec1f37487bf5405b719d2299b1c4b7afb413b0d/scanner/src/stellenkompass_scanner/models.py) | Shared Python Job dataclass | Add optional fields with safe defaults |
| [scanner/src/stellenkompass_scanner/run.py](https://github.com/parimalgavali/stellenkompass/blob/8ec1f37487bf5405b719d2299b1c4b7afb413b0d/scanner/src/stellenkompass_scanner/run.py) | Config, scan loop, carry-over, first_seen, output | Board outcomes, complete/partial semantics, validation and publication |
| [scanner/src/stellenkompass_scanner/http.py](https://github.com/parimalgavali/stellenkompass/blob/8ec1f37487bf5405b719d2299b1c4b7afb413b0d/scanner/src/stellenkompass_scanner/http.py) | Shared httpx client, pauses, retries | Host-aware limits and source-specific headers/auth when needed |
| [scanner/src/stellenkompass_scanner/geo.py](https://github.com/parimalgavali/stellenkompass/blob/8ec1f37487bf5405b719d2299b1c4b7afb413b0d/scanner/src/stellenkompass_scanner/geo.py) | Country/city matching and remote inclusion | Structured evidence, small-town coverage, eligibility uncertainty |
| [scanner/src/stellenkompass_scanner/dedupe.py](https://github.com/parimalgavali/stellenkompass/blob/8ec1f37487bf5405b719d2299b1c4b7afb413b0d/scanner/src/stellenkompass_scanner/dedupe.py) | Same company/title/city collapse | Preserve distinct requisitions and tracker identity |
| [scanner/src/stellenkompass_scanner/classify.py](https://github.com/parimalgavali/stellenkompass/blob/8ec1f37487bf5405b719d2299b1c4b7afb413b0d/scanner/src/stellenkompass_scanner/classify.py) | Posting language and employment type heuristics | Unknowns, research/contract distinctions as justified |
| [scanner/tests](https://github.com/parimalgavali/stellenkompass/tree/8ec1f37487bf5405b719d2299b1c4b7afb413b0d/scanner/tests) | Offline parser and pipeline tests | Add fixtures and regressions alongside each change |
| [web/src/types.ts](https://github.com/parimalgavali/stellenkompass/blob/8ec1f37487bf5405b719d2299b1c4b7afb413b0d/web/src/types.ts) | Frontend Job and scan report contracts | Match additive Python fields |
| [web/src/lib/filters.ts](https://github.com/parimalgavali/stellenkompass/blob/8ec1f37487bf5405b719d2299b1c4b7afb413b0d/web/src/lib/filters.ts) | Search/filter/sort behavior | Multi-location, freshness, workplace and eligibility filters |
| [web/src/components/JobsPage.tsx](https://github.com/parimalgavali/stellenkompass/blob/8ec1f37487bf5405b719d2299b1c4b7afb413b0d/web/src/components/JobsPage.tsx) | Filter controls and visible list | Reach small towns and new source types |
| [web/src/lib/tracker.ts](https://github.com/parimalgavali/stellenkompass/blob/8ec1f37487bf5405b719d2299b1c4b7afb413b0d/web/src/lib/tracker.ts) | Saved applications keyed by Job.id | Preserve old IDs and matching aliases |
| [web/vite.config.ts](https://github.com/parimalgavali/stellenkompass/blob/8ec1f37487bf5405b719d2299b1c4b7afb413b0d/web/vite.config.ts) | Copies data/*.json into public build | Keep private/internal state out of data/ |
| [.github/workflows/daily.yml](https://github.com/parimalgavali/stellenkompass/blob/8ec1f37487bf5405b719d2299b1c4b7afb413b0d/.github/workflows/daily.yml) | Daily scan, data commit and Pages deployment | Persist approved scan state; preserve data on unsuccessful runs |

The source documentation currently refers to a shortened model path. The actual package is under scanner/src/stellenkompass_scanner/.

### 3.2 Current pipeline

1. run.load_config reads companies.yaml.
2. scan invokes enabled aggregators and each configured employer board.
3. Each adapter fetches raw data and calls parse.
4. parse normally delegates each vacancy to build_job.
5. build_job rejects locations outside the present Germany/remote heuristic and creates Job.
6. Failed boards can recover their prior entries from the previous **deduplicated** jobs.json.
7. dedupe chooses one record per normalized employer/title/city.
8. carry_first_seen preserves timestamps only when the selected Job.id is unchanged.
9. write_outputs writes jobs.json and scan_report.json.
10. React downloads the complete jobs file; filters run in the browser. Personal profiles and application records remain in localStorage.

### 3.3 Current source support

- Aggregator: Arbeitnow.
- Company adapters: Greenhouse, Ashby, SmartRecruiters, Lever, Personio.
- Configuration contains 63 employer boards. The exact inventory is in Appendix B.
- The committed report records 4,283 published roles at 2026-11-03T06:09:57Z, with no recorded source errors. This is a historical repository snapshot, not a fresh measurement by this review. See [data/scan_report.json](https://github.com/parimalgavali/stellenkompass/blob/8ec1f37487bf5405b719d2299b1c4b7afb413b0d/data/scan_report.json).
- Collection is not limited to technology occupations. A board can contribute finance, retail, operations, and other roles. Decide whether to classify these in the UI; do not silently remove them simply because they have no recognized programming skill.

The daily workflow uses UTC cron 04:15: 05:15 Berlin in winter, 06:15 in summer. Scanner-only configuration/code changes do not trigger an immediate scan through its current push path filter; use workflow_dispatch or wait for the schedule.

### 3.4 Current fetching routes and normalization limits

These are the routes implemented at the reviewed commit, not promises of future access:

| Adapter | Implemented route | Important current behavior |
| --- | --- | --- |
| Arbeitnow | `https://www.arbeitnow.com/api/job-board-api?page={page}` | Up to 30 pages; uses slug as identity; no explicit capped outcome |
| Greenhouse | `https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true` | Includes description and offices; may use updated_at as posted_at |
| Ashby | `https://api.ashbyhq.com/posting-api/job-board/{board}` | Excludes unlisted jobs; primary-address helper is reused incorrectly for documented secondary address shape |
| SmartRecruiters | `https://api.smartrecruiters.com/v1/companies/{board}/postings?country=de&limit=100&offset={offset}` | Up to 20 pages; summaries only; extra region/city check preserves a known foreign-location regression |
| Lever | `https://api.lever.co/v0/postings/{board}?mode=json` | Global host only; no explicit paging loop; copies one combined description field |
| Personio | `https://{board}.jobs.personio.de/xml` | .de only; default feed language; constructs original job URL on that same domain |

Description-to-skills extraction is centralized in build_job. The existing source module registry means a new employer on one of these platforms can be onboarded through configuration, while a new provider needs an adapter plus registry/tests/docs updates.

[Greenhouse official Job Board API](https://docs.greenhouse.io/job-board.html), [Arbeitnow API information](https://www.arbeitnow.com/blog/job-board-api). Other provider documentation is linked in the relevant adapter sections below.

### 3.5 What is already good

The adapters are small, transport is shared, normalization has one entry point, fixtures work offline, one failing board does not stop others, and local tracker records preserve their own title/company/link after a listing disappears. Keep those properties.

## 4. Findings to address before large expansion

### F1. Distinct vacancies can be deleted by deduplication — fix first

Evidence: [scanner/src/stellenkompass_scanner/dedupe.py:26](https://github.com/parimalgavali/stellenkompass/blob/8ec1f37487bf5405b719d2299b1c4b7afb413b0d/scanner/src/stellenkompass_scanner/dedupe.py#L26).

The key is normalized employer + title + one city. Two different Software Engineer requisitions in Berlin from the same employer collapse even if their source IDs differ. This was reproduced.

Required behavior:

- Collapse repeated copies of the exact same provider/board/job ID.
- Preserve different requisition IDs unless there is explicit evidence that they are the same vacancy.
- For cross-source duplicates, prefer an original posting URL, provider identity, or employer requisition identifier.
- A same-title/location match is a possible duplicate, not sufficient proof for deletion.
- Retain all contributing source references when a confident merge occurs.
- New direct adapters must receive appropriate source priority: the current unknown-source rank is 9, below Arbeitnow at rank 1.

Acceptance: two distinct same-board IDs with the same title and city survive; a true aggregator copy of an original job is displayed once.

### F2. Saved applications and first_seen can lose continuity when source preference changes

Evidence: [scanner/src/stellenkompass_scanner/run.py:99](https://github.com/parimalgavali/stellenkompass/blob/8ec1f37487bf5405b719d2299b1c4b7afb413b0d/scanner/src/stellenkompass_scanner/run.py#L99), [web/src/lib/tracker.ts:3](https://github.com/parimalgavali/stellenkompass/blob/8ec1f37487bf5405b719d2299b1c4b7afb413b0d/web/src/lib/tracker.ts#L3), [web/src/App.tsx](https://github.com/parimalgavali/stellenkompass/blob/8ec1f37487bf5405b719d2299b1c4b7afb413b0d/web/src/App.tsx), [web/src/components/TrackerPage.tsx](https://github.com/parimalgavali/stellenkompass/blob/8ec1f37487bf5405b719d2299b1c4b7afb413b0d/web/src/components/TrackerPage.tsx).

If a job was first discovered through Arbeitnow and later through a newly added employer board, the selected provider ID changes. first_seen resets; a saved old ID appears absent from the current scan even when the vacancy is still present.

Required behavior:

- Keep a persistent display identity when a new source joins an already identified vacancy.
- Preserve source IDs as aliases; do not replace every existing ID in a migration.
- Include aliases in the frontend's live/tracked lookups.
- Saving a role already tracked under an alias must not create a second application.
- Keep all tracker stages, dates and notes intact.
- Persist first_seen independently of provider ranking.

A small identity/alias map is enough initially. Do not infer identity from title alone.

### F3. Geography can both exclude real German jobs and include foreign ones

Evidence: [scanner/src/stellenkompass_scanner/geo.py:122](https://github.com/parimalgavali/stellenkompass/blob/8ec1f37487bf5405b719d2299b1c4b7afb413b0d/scanner/src/stellenkompass_scanner/geo.py#L122), [scanner/src/stellenkompass_scanner/sources/_common.py:28](https://github.com/parimalgavali/stellenkompass/blob/8ec1f37487bf5405b719d2299b1c4b7afb413b0d/scanner/src/stellenkompass_scanner/sources/_common.py#L28).

Country-code evidence currently accepts DE but does not stop a later city-name match from accepting explicit foreign locations. Some sources have no structured country code and rely on a fixed city list. Small towns without “Germany” in the location can be dropped.

Required behavior:

- Associate country with each location, rather than pooling independent city and country strings.
- An explicit non-German location must not become German through a city-name coincidence.
- A multi-location posting is included when at least one actual location is in Germany.
- Prefer structured country codes over free text.
- Use a maintained municipality/postcode reference only where structured evidence is missing; document and test the chosen dataset.
- Preserve unresolved candidates for diagnosis or clearly label them for review. Do not call unknown locations “Germany”.
- Treat DACH/EMEA/Europe as regional evidence, not proof of German residence eligibility.

Acceptance includes an unlisted German town with country DE, foreign Frankfurt, multi-country postings, missing country, and explicit exclusion of German residents.

### F4. Ashby secondary address and remote handling need correction

Evidence: [scanner/src/stellenkompass_scanner/sources/ashby.py:15](https://github.com/parimalgavali/stellenkompass/blob/8ec1f37487bf5405b719d2299b1c4b7afb413b0d/scanner/src/stellenkompass_scanner/sources/ashby.py#L15).

_country expects address.postalAddress.addressCountry for both primary and secondary locations. The official example documents flat country information within a secondary location's address. A German secondary location in a small unlisted town can therefore be rejected; this was reproduced.

Also, isRemote can cover hybrid work. Preserve workplaceType rather than presenting every positive isRemote as fully remote.

Acceptance: primary and secondary address shapes both work; German secondary locations survive; hybrid and fully remote remain distinguishable; isListed=false stays excluded. [Official Ashby documentation](https://developers.ashbyhq.com/docs/public-job-posting-api)

### F5. SmartRecruiters descriptions are not fetched

Evidence: [scanner/src/stellenkompass_scanner/sources/smartrecruiters.py:34](https://github.com/parimalgavali/stellenkompass/blob/8ec1f37487bf5405b719d2299b1c4b7afb413b0d/scanner/src/stellenkompass_scanner/sources/smartrecruiters.py#L34).

Only summary listings are fetched, and parse never supplies description to build_job. This limits snippets, skill extraction, meaningful content search, and future requirement extraction.

Required behavior:

- Fetch posting details through the documented detail route/ref for new or changed postings.
- Extract description sections into plain text and pass them to build_job.
- Cache the parsed detail using a provider update signal when available; otherwise use an explicit detail-refresh interval.
- On a transient detail failure, preserve prior verified content and mark the detail stale; do not drop the summary silently or call it a complete content refresh.
- Validate any followed detail URL against expected source hosts.

Keep the existing foreign-site fixture: do not remove _german_region without replacing its demonstrated protection with better evidence. Also test valid German locations whose region format is unfamiliar.

[SmartRecruiters list/detail documentation](https://developers.smartrecruiters.com/docs/endpoints)

### F6. Pagination caps can masquerade as complete snapshots

Evidence: Arbeitnow max_pages=30; SmartRecruiters max_pages=20 at 100 entries per request. See [scanner/src/stellenkompass_scanner/sources/arbeitnow.py:13](https://github.com/parimalgavali/stellenkompass/blob/8ec1f37487bf5405b719d2299b1c4b7afb413b0d/scanner/src/stellenkompass_scanner/sources/arbeitnow.py#L13) and [scanner/src/stellenkompass_scanner/sources/smartrecruiters.py:14](https://github.com/parimalgavali/stellenkompass/blob/8ec1f37487bf5405b719d2299b1c4b7afb413b0d/scanner/src/stellenkompass_scanner/sources/smartrecruiters.py#L14).

If more results remain after a safety cap, the adapter returns the partial list without reporting incompleteness. Omitted prior jobs can disappear as if they closed.

Required behavior:

- Report exhausted, capped, failed, and partial outcomes separately.
- A cap is a safety boundary, not proof of completeness.
- Detect repeated cursors/pages and duplicate-only pages.
- If the provider exposes a result-window limit, partition documented queries or report the coverage limit; simply increasing a cap may not solve it.
- Never close unseen jobs from an incomplete scan.
- Test a failure on page two and a still-present next page at the cap.

### F7. Carry-over needs explicit board identity and freshness

Evidence: [scanner/src/stellenkompass_scanner/run.py:80](https://github.com/parimalgavali/stellenkompass/blob/8ec1f37487bf5405b719d2299b1c4b7afb413b0d/scanner/src/stellenkompass_scanner/run.py#L80).

Carry-over matches string ID prefixes from the previous deduplicated output. Board “foo” can prefix-match IDs belonging to “foo-bar”. Previous deduplication can also have discarded the secondary source copy needed for later recovery. Repeated failures can keep stale roles indefinitely without a per-job freshness indicator.

Required behavior:

- Add explicit source_board and source_job_id fields.
- Recover by exact source/board identity.
- Keep a compact per-board latest-success state before cross-source deduplication.
- Record last_verified and stale/unknown availability separately from the current scan timestamp.
- Preserve role history/identity when an explicitly confirmed closed job leaves the active list.
- Make any maximum stale-display period an explicit policy. Repeated source failures do not prove closure.

### F8. Empty/malformed responses must not erase valid jobs

Evidence: multiple parsers use raw.get("jobs", []) or analogous defaults; exceptions are caught at board level in run.scan.

A 200 response with an unexpected schema can look like a valid empty board. A malformed record can also abort the entire board.

Required behavior:

- Validate top-level response structure before accepting an empty result.
- Separate individual record errors from transport/board errors.
- Keep valid records when one record is bad.
- Treat a parse-error-containing snapshot as incomplete for closure decisions.
- Flag unexpected large count drops for inspection; do not impose a rule that zero can never be valid.
- Validate outputs before replacing the last good output. Write temporary files, then atomically replace approved outputs.

The current CLI writes outputs before its final zero-jobs error return. The Actions workflow does not commit if that step fails, but local output files can already be replaced. Protect the writer itself.

### F9. English posting language is not English-only job eligibility

Evidence: [scanner/src/stellenkompass_scanner/classify.py:19](https://github.com/parimalgavali/stellenkompass/blob/8ec1f37487bf5405b719d2299b1c4b7afb413b0d/scanner/src/stellenkompass_scanner/classify.py#L19).

The current en/de guess describes the text. An English advertisement may still require fluent German; an empty description defaults to English.

Required behavior: keep posting language and explicit required languages separate. Unknown must remain unknown. Display “English advertisement” until stronger eligibility extraction is available. Do not market the existing flag as “German not required”.

### F10. Small-job coverage is explicitly restricted by current onboarding policy

Evidence: [docs/DATA_SOURCES.md](https://github.com/parimalgavali/stellenkompass/blob/8ec1f37487bf5405b719d2299b1c4b7afb413b0d/docs/DATA_SOURCES.md) says boards with fewer than three German roles were excluded, listing Wunderflats, kununu, KONUX, Dataiku, Rasa, HeyJobs, Spotify (Lever), and Clark.

Required behavior: revisit these candidates and discover their **current** careers systems. Add valid boards even if they have one relevant vacancy. Keep validated zero-result boards available for later scans, with a lower polling frequency if useful. Do not assume an old provider slug is still correct.

### F11. Smaller cities are hard to discover in the UI

Evidence: [web/src/components/JobsPage.tsx:25](https://github.com/parimalgavali/stellenkompass/blob/8ec1f37487bf5405b719d2299b1c4b7afb413b0d/web/src/components/JobsPage.tsx#L25) limits city options to the top 40. Each Job also has only one primary city, and text search excludes location/snippet.

Required behavior: include location in search, expose all cities through a searchable or modestly expanded control, and match all normalized German locations once the multi-location model lands.

### F12. Reporting needs to distinguish collection from publication

Evidence: [scanner/src/stellenkompass_scanner/run.py:148](https://github.com/parimalgavali/stellenkompass/blob/8ec1f37487bf5405b719d2299b1c4b7afb413b0d/scanner/src/stellenkompass_scanner/run.py#L148) adds duplicates_removed after scan_report.json was written. Current per-source counts are before cross-source deduplication.

Required behavior: compute summary fields before serialization and label counts accurately. A successful HTTP request is not equivalent to complete coverage or successful content parsing.

## 5. Add employers to existing adapters today

This is the smallest expansion and requires no new platform module.

1. Start at the employer's official website.
2. Follow its careers link and a public vacancy.
3. Record provider, exact board identifier, careers URL, display name, and evidence date.
4. Verify a sample employer identity and at least one location. Do not guess the employer from a slug.
5. Fetch using the corresponding current adapter.
6. Check raw count versus accepted German count and explain rejected examples.
7. Add one config entry, even if there is only one relevant job.
8. Run a targeted scan and inspect IDs, URLs, location, language, type and skills.
9. Update DATA_SOURCES.md and source inventory evidence.
10. Commit through the repository's existing issue → branch → PR workflow.

Current supported configuration shape:

```yaml
aggregators:
  arbeitnow: true

greenhouse:
  - { board: "<verified-board-token>", name: "Employer display name" }

ashby:
  - { board: "<verified-board-name>", name: "Employer display name" }

lever:
  - { board: "<verified-site-name>", name: "Employer display name" }

smartrecruiters:
  - { board: "<verified-case-sensitive-identifier>", name: "Employer display name" }

personio:
  - { board: "<verified-account>", name: "Employer display name" }
```

The placeholders above are illustrative, not valid tenants.

To exercise one existing adapter without changing production config:

```python
from stellenkompass_scanner.http import HttpFetcher
from stellenkompass_scanner.sources import greenhouse

fetcher = HttpFetcher()
try:
    board = "<verified-board-token>"
    raw = greenhouse.fetch(fetcher, board)
    jobs = greenhouse.parse(raw, board, company="Employer display name")
    print(len(jobs))
    for job in jobs[:5]:
        print(job.id, job.title, job.location, job.url)
finally:
    fetcher.close()
```

Run from scanner/ in the project's uv environment. A zero parsed count needs investigation: it can mean no current German jobs, incorrect geographic extraction, an obsolete slug, or malformed data.

### Expand the existing adapters themselves

- **Lever:** current fetch supports only api.lever.co. Add explicit EU host selection and documented pagination. Preserve the old config form. Include complete description sections, not only a potentially partial opening. [Lever documentation](https://github.com/lever/postings-api)
- **Personio:** current fetch supports only .jobs.personio.de and the default language. Support verified .com hosts and configured language variants; merge translated versions by board/job ID. Preserve alternate-language content without resetting identity. [Personio XML setup](https://support.personio.de/hc/en-us/articles/207576365-Integrate-jobs-from-Personio-into-your-website-via-XML)
- **Ashby:** fix address and workplace semantics first; compensation is optional future enrichment.
- **Greenhouse:** distinguish last-update timestamps from original publication dates; keep the existing stable source IDs.
- **SmartRecruiters:** add details and completeness reporting before expanding very large boards.
- **Arbeitnow:** retain pagination and backoff; add explicit cap/partial reporting. Do not count its employer coverage as additional unique coverage without deduplication.

## 6. Minimal configuration evolution

Do not replace companies.yaml with a configuration service. Extend its existing entry format only when an adapter needs more information.

Proposed future examples, **not supported by the reviewed code**:

```yaml
lever:
  - board: "<verified-site>"
    name: "Employer"
    region: eu
    enabled: true

personio:
  - board: "<verified-account>"
    name: "Employer"
    domain: jobs.personio.com
    languages: [de, en]
    enabled: true

recruitee:
  - board: "<verified-subdomain>"
    name: "Employer"
    enabled: true

teamtailor:
  - board: "<stable-local-key>"
    name: "Employer"
    careers_url: "https://<verified-careers-domain>"
    enabled: true
```

Implementation implications:

- _boards currently strips every key except board/name. Simply adding these fields to YAML does nothing.
- Preserve old string and board/name entries while validating new options.
- Validate known provider options and unique source/board keys before network requests.
- Unknown provider names and unsupported keys should produce actionable config errors.
- Registry definition should identify company-board versus aggregator kind; do not make every new source an aggregator.
- Store discovery evidence and non-runtime notes in a separate inventory rather than overloading runtime config.
- Credentials belong in environment variables/GitHub Actions secrets; avoid query-string secrets in logs and reports.
- Add --source/--board or an equivalent targeted scan command as a small developer convenience. These flags do not exist yet.

## 7. Add new platform adapters

### 7.1 Recruitee — first new JSON adapter

Official documented route:

```text
GET https://{company}.recruitee.com/api/offers/
```

[Official offers documentation](https://docs.recruitee.com/reference/offers)

Implementation:

- Create sources/recruitee.py; register in PER_COMPANY.
- Fetch published jobs through the careers-site offers endpoint.
- Use actual documented offer IDs, original careers URLs, all locations, employment metadata and descriptions.
- Inspect the real response for location arrays and translations; do not invent field names from another ATS.
- Use structured country evidence where present.
- Follow documented pagination if returned by the actual route. Never assume an uninspected response is complete.
- Keep one source identity for translated copies of the same offer.
- Do not use the authenticated company-management /c/{company_id}/offers endpoint as if it were the public careers feed.
- Add fixtures for German small town, multi-location, translation, empty board, malformed record and non-German-only job.

### 7.2 Teamtailor — first new RSS adapter

Official route:

```text
https://<actual-employer-careers-domain>/jobs.rss
```

Custom employer domains work at the careers-site level. The official documentation says the default feed contains the first 100 jobs, with offset and per_page parameters for additional results. Implement and test pagination rather than reading only the initial feed. [Teamtailor RSS documentation](https://support.teamtailor.com/en/articles/11171756-rss-feed-how-to-guide)

Implementation:

- Create sources/teamtailor.py; register in PER_COMPANY.
- Use the recorded careers URL, not a guessed company subdomain.
- Use RSS GUID/provider identity; title/date must not become the job ID.
- Parse namespaces and available metadata from real fixtures.
- Normalize title, description, original URL, publication date, remote/workplace metadata, and all location fields.
- XML parsing is already a project capability; add a feed library only if actual namespace/date/format complexity warrants it.
- Stop on exhaustion and detect repeated pages/GUIDs.
- Test more than one page, custom domain, missing GUID, malformed XML, unknown location and legitimate zero entries.

### 7.3 German and enterprise platforms — one measured pilot at a time

Investigate softgarden, rexx, d.vinci, BITE, HR4YOU, Workable, Workday, SAP careers systems, Oracle and iCIMS using a few real German employer tenants.

For each pilot, document:

1. Employer-owned careers link and verified hosting/provider evidence.
2. Actual public fetching route and whether it is officially supported.
3. Access/display conditions, credentials if any, and provider limits.
4. Pagination, filters, complete-result boundaries and detail requests.
5. Stable ID/requisition identity.
6. Germany/location/remote evidence.
7. Closed-job and change-detection semantics.
8. A saved fixture and expected normalized output.
9. A fallback that reports failure without erasing last good jobs.

A JSON endpoint used by a careers website is not automatically a supported public API. Keep undocumented endpoints explicitly marked and isolated. Do not create a generic “all Workday companies” integration without tenant and site discovery.

## 8. German university coverage

### 8.1 Build a maintained institution inventory

Use [Hochschulkompass](https://www.hochschulkompass.de/) as the institution-discovery starting point. Its information is maintained by institutions; it is not a jobs feed. [Official description](https://www.hochschulkompass.de/ueber-uns.html)

Include universities, universities of applied sciences, and other recognized higher-education institutions. Keep university hospitals and research centres as related but separately identified employers where appropriate.

Minimal inventory record:

```yaml
institution_id: "<stable-local-id>"
name: "<official-name>"
institution_type: "<university-or-other>"
state: "<German-state>"
official_url: "https://<official-domain>"
careers_urls: []
department_job_urls: []
it_centre_job_urls: []
student_job_urls: []
hospital_careers_urls: []
provider: null
board: null
discovered_from: "https://www.hochschulkompass.de/"
last_checked: null
status: needs_discovery
```

This is a proposed research record, not an enabled scanner entry.

### 8.2 Discovery procedure

For every institution:

- Find the central employment portal.
- Follow IT centre/Rechenzentrum and computer-science faculty job links.
- Inspect research-group and laboratory vacancy pages where central coverage is incomplete.
- Identify student-assistant/HiWi pages and career-service external-employer boards.
- Identify hospital vacancies separately.
- Record PDF-based advertisements and their parent page.
- Detect existing ATSs and reuse those adapters wherever possible.
- Otherwise prefer documented feeds, then embedded JobPosting JSON-LD, then a narrowly scoped HTML parser.
- Keep feeds/pages with zero current roles in the registry.
- Recheck provider changes and broken pages periodically.

Do not label the sample universities in the catalog “all universities”. Track institution inventory coverage explicitly, including those still awaiting discovery.

### 8.3 Useful source groups

- Central academic boards: EURAXESS, academics, Academic Positions, DUZ.
- Doctoral discovery: DAAD PhDGermany; distinguish employment from scholarships/programmes.
- Student jobs: stellenwerk and accessible JobTeaser listings.
- Research networks: Fraunhofer, Max Planck, Helmholtz, Leibniz.
- Individual employers: DLR, DFKI, DESY, Forschungszentrum Jülich and centres discovered through network directories.

Pilot with the university and research entries in the companion catalog, then extend institution by institution. A large shared portal is useful but does not eliminate the need to check individual institute pages.

### 8.4 Scope and taxonomy

For tech searches include research software engineering, HPC, scientific computing, data engineering, research data management, systems/network administration, cybersecurity, laboratory software, and embedded systems.

Search terms include Stellenangebote, Stellenausschreibungen, wissenschaftliche Mitarbeit, studentische Hilfskraft, wissenschaftliche Hilfskraft, HiWi, Rechenzentrum, Hochschul-IT, Forschungssoftware, Werkstudent, Praktikum, Bachelorarbeit and Masterarbeit.

Do not equate:

- A PhD programme with a salaried vacancy.
- A scholarship with employment.
- All university research with IT.
- All student assistants with the same employment arrangement.

Preserve source titles and contract evidence; add a small taxonomy only where the UI needs it. Retain unknowns.

## 9. Shared data and identity contract

### 9.1 Preserve the present contract first

Keep existing required fields, stable legacy IDs and the browser-only profile/tracker design. New fields should initially be additive and optional in TypeScript, with defaults in Python.

Implement these fields when their corresponding feature lands:

| Field | Purpose |
| --- | --- |
| source_board, source_job_id | Exact recovery, provenance and source identity |
| locations | Per-location city/region/country evidence; retain location and city for compatibility |
| workplace_type | onsite, hybrid, remote, or unknown |
| geography_status | German location, explicitly Germany-eligible remote, or unresolved |
| eligibility_evidence | Short source evidence supporting the country decision |
| apply_url | Application link if distinct; retain url for original listing |
| first_seen | Preserve earliest discovery across confidently linked sources |
| last_seen, last_verified | Observation time versus last successful verification |
| availability | active, stale, unknown or closed, governed by verified evidence |
| expires_at | Source-provided deadline/expiry when available |
| aliases / source_refs | Prior display IDs and exact source identities |
| posting_language / required_languages | Separate text language from requirements when implemented |
| description_status | Complete, summary-only, unavailable, or stale |

Do not add every field in a single migration. Introduce identity/completeness/freshness first, then location/workplace support, then richer content and language requirements.

Full descriptions may remain scanner-side initially. Extract skills and a snippet before producing the public file; inspect feed permissions before storing or redistributing full content.

### 9.2 Source identity versus displayed vacancy

Represent source identity as a tuple, not by splitting an old ID:

```text
(provider, board, provider_job_id)
```

A displayed vacancy can reference multiple such tuples. Reuse an existing display ID when a confident link joins it to another source. Keep distinct requisitions separate, even if names match. Translations and location variants need explicit identity evidence.

### 9.3 Normalization and validation

At the boundary of each adapter:

- Require usable title, source identity, employer evidence, and a valid HTTP(S) original URL.
- Preserve provider text before deriving display values.
- Keep known unknowns rather than defaulting everything to full-time/English/remote.
- Preserve all relevant locations; do not make the first matching city the entire geography.
- Sanitize extracted text; do not inject raw third-party HTML into React.
- Keep advertised salary separate from inferred/predicted salary if salary enrichment is added.
- Preserve application URLs required by provider terms.
- Keep skills extraction compatible with the concurrent CV-fit changes; changing the scoring vocabulary is out of scope.

## 10. Complete, partial, failed and stale scans

Introduce a small per-board outcome model inside the existing runner. No worker framework is required.

A board result needs: provider, exact board, success state, completeness, pages/requests, fetched/accepted/rejected counts, error details, and verification time. Parsing can continue on valid records while the outcome remains partial.

| Outcome | New valid observations | Previously unseen jobs |
| --- | --- | --- |
| Complete, valid snapshot | Update jobs and verification time | May become closure candidates under documented source semantics |
| Partial/capped scan | Update observed jobs | Retain as unverified/stale; do not infer closure |
| Transport or schema failure | Keep last good observations | Retain with previous verification timestamp |
| Valid, complete zero result | Record a successful empty snapshot | Apply explicit disappearance policy; do not confuse this with parse failure |
| Explicit provider closed/expired result | Record closure evidence | Remove from active listing while retaining identity/history |

For disappearance without explicit provider closure, a proposed cautious default is confirmation across two complete successful scans. Make the policy per source where provider semantics differ. Do not force feed/window-based aggregators into full-employer-snapshot semantics.

### Persistence

A previous deduplicated jobs.json is insufficient as the only recovery state. Initially persist compact, normalized per-board last-good observations and an identity/alias map in a dedicated scanner state location.

- Keep internal state **outside data/**: Vite currently copies every JSON there into the public site.
- Explicitly update the workflow to restore/persist the chosen state. Files left only in a runner's workspace disappear after the run.
- A small reviewed versioned state file is the simplest initial option only when its data is permitted to be public. If rights require private state, use an appropriately persistent private artifact/store instead and handle absence/retention deliberately.
- No CVs, credentials, personal application notes, or applicant data belong in shared scan state.
- Avoid archiving every raw HTTP response in Git.
- Document recovery/bootstrap when state is absent or invalid.
- Disabled/removed boards need explicit treatment; disabling polling is not evidence that all their jobs closed.

## 11. More sites: how to prioritize and integrate

The source catalog includes a broad list, but access quality varies.

### Documented public feeds/APIs

Recruitee, Teamtailor, Himalayas, We Work Remotely, Remotive and Remote OK have documented public interfaces worth investigating.

Important source-specific conditions:

- Teamtailor: RSS pagination is required beyond its default first 100 entries.
- Himalayas: use cursor pagination, preserve the supplied application link and attribution, remove expired listings, and check redistribution restrictions before publishing a downloadable dataset. A static public JSON application needs to be assessed against those terms.
- We Work Remotely: attribute links to the provider.
- Remotive: the public feed is delayed by 24 hours and has attribution/display conditions.
- Remote OK: read metadata/terms; the first array item is not a vacancy.
- Adzuna: credentials required; official documentation notes descriptions can be snippets.
- Jooble: API-key request required.

Sources: [Himalayas](https://himalayas.app/api), [WWR](https://weworkremotely.com/remote-job-rss-feed), [Remotive](https://github.com/remotive-com/remote-jobs-api), [Remote OK](https://remoteok.com/api), [Adzuna](https://developer.adzuna.com/docs/search), [Jooble](https://jooble.org/api/about).

### Large boards and Bundesagentur für Arbeit

Use Stepstone, Indeed, LinkedIn, XING, Jobware and others for employer/source discovery and investigate supported data arrangements. This document does not establish unrestricted fetching rights or a current free global listing API for them.

The repository's note to retry the BA endpoint from Actions should become an access investigation, not an assumption that changing the execution host makes access appropriate. BA's HR-BA-XML page describes employer submission and cooperation models, not a universal unauthenticated vacancy download service. [Official BA information](https://www.arbeitsagentur.de/unternehmen/arbeitskraefte/hr-ba-xml-schnittstelle)

### Recruitment agencies

Collect client job listings rather than only agency-internal recruiting vacancies. Do not invent an end-client name when it is undisclosed. Do not auto-merge two agency advertisements solely because descriptions look similar.

### Employer discovery loop

After every scan, extract candidate original employer/careers links where permitted. Put new candidates in a reviewable inventory. Validate identity/provider/route before enabling them.

Supplement with:

- Academic and research institution directories.
- Regional employer and startup ecosystem directories.
- Employer lists on specialist job boards.
- Employer-owned sitemaps and careers-page links.
- A documented search service or manual search to discover careers URLs.

Search-engine discovery is not exhaustive and may have its own access/cost limits. Use it to seed a registry, not as proof that every employer has been found.

### Generic JobPosting fallback

For approved public career pages without a usable existing adapter, implement a bounded JSON-LD extractor:

- Parse application/ld+json blocks.
- Handle single objects, arrays and @graph.
- Select JobPosting records and resolve relative URLs.
- Read identifier, hiringOrganization, jobLocation, datePosted, validThrough, employmentType and remote eligibility fields where present.
- Keep document discovery separate from parsing one job page.
- Use explicit domain/URL/path limits and visit deduplication.
- Missing structured data should produce an actionable unsupported result, not a fabricated empty employer snapshot.
- Add fixtures before site-specific HTML fallback.

[Official JobPosting field documentation](https://developers.google.com/search/docs/appearance/structured-data/job-posting)

## 12. Operations, reporting, and static-site growth

Keep the current daily cadence initially. Add host-aware request spacing, jitter/backoff and explicit per-source budgets as demand requires them. Thousands of concurrent requests are not the first scaling step.

Report per provider and board:

- Configured, enabled, checked, successful, partial, failed and zero-result status.
- Raw fetched, accepted, rejected with reason, and invalid-record counts.
- Published unique jobs, duplicate links, last-good carried jobs, and stale jobs.
- Requests, pages, elapsed time and cap/result-window warnings.
- Last attempt and last successful complete verification.
- Source contribution after deduplication, with unknown identity matches tracked separately.
- Institutions discovered versus institutions with verified collection routes.

Show an understandable freshness status in the UI. “Scanned today” must not imply that a carried job was verified today.

Do not add the reported per-source raw counts and present that sum as the number of unique jobs. Record a consistent scan/run ID in both public output files so mismatched artifacts can be detected.

### Growth boundaries

Before changing architecture, measure:

- Compressed public JSON transfer size.
- Browser parse/filter/render time on a modest phone.
- Scan duration and request budget.
- Git growth from committed snapshots.
- Failure recovery and data freshness.

The frontend currently downloads the entire jobs file even though it renders 50 cards initially. If payload size becomes problematic, split a compact manifest and list data into static chunks, keep verbose descriptions elsewhere when permitted, and add a search index only if measured filtering cost warrants it.

Do not introduce a public database service just because the catalog contains many source names.

## 13. Implementation backlog for Devin

Follow the existing repository workflow: issue with acceptance criteria → one branch from current main → tests/lint → PR → docs updates. These are proposed work items; no issues or PRs were created by this review.

### Work item 1 — Coverage and identity regressions

Files: dedupe.py, run.py, models.py; tracker/live identity consumers only as needed.

Acceptance:

- Different same-board requisitions with the same title/city survive.
- True source copies link without losing prior display IDs.
- first_seen and saved tracker continuity survive new source preference.
- Exact source/board recovery handles hyphenated board names.
- New direct adapter priority is explicit.
- Regression fixtures cover all of the above.

### Work item 2 — Geographic evidence and workplace types

Files: geo.py, _common.py, ashby.py, models.py, web types/filter/card code.

Acceptance:

- Structured foreign country is not overridden by city coincidence.
- Primary and secondary Ashby address formats work.
- German small-town location with DE survives.
- Multiple locations remain searchable.
- Hybrid is not shown as fully remote.
- Regional remote evidence remains distinguishable from confirmed Germany eligibility.

### Work item 3 — Complete scans, state and freshness

Files: run.py, HTTP helpers only as needed, all adapters affected by result handling, daily workflow, report types/footer.

Acceptance:

- Capped or failed page-two scans do not close unseen jobs.
- Schema errors do not appear as successful empty boards.
- Valid records survive isolated malformed records.
- Atomic output validation protects the last good data.
- Per-board state persists across Actions runs.
- Stale roles retain their actual last verification time.
- duplicates_removed and completeness metrics are written to the report.

### Work item 4 — Existing adapter coverage

Files: Lever, Personio, SmartRecruiters, config handling and fixtures.

Acceptance:

- Global/EU Lever host selection and pagination.
- Personio .de/.com plus configured languages with shared job identity.
- SmartRecruiters detail enrichment, cached refresh and failure handling.
- Relevant metadata reaches build_job without changing the CV scoring rules.

### Work item 5 — Employer onboarding and low-volume boards

Files: companies.yaml, DATA_SOURCES.md, optional discovery inventory and targeted scan command.

Acceptance:

- Revisit previously excluded low-volume candidates.
- Every newly enabled entry has verified employer/provider/board evidence.
- One-job boards qualify; validated zero-result boards remain discoverable.
- A config-only addition to an existing provider does not require frontend edits.
- Provider migrations retire stale board configuration explicitly.

### Work item 6 — Recruitee

Files: new adapter, registry, fixtures/tests, config/docs.

Acceptance: published offers, all locations, translations, stable IDs and completeness tested against saved real response structure.

### Work item 7 — Teamtailor

Files: new adapter, registry, fixtures/tests, config/docs.

Acceptance: custom careers domains, RSS GUIDs, multiple pages beyond the default first 100, XML namespace handling, and correct zero/partial/failure outcomes.

### Work item 8 — University and research pilot

Files: institution inventory, existing ATS config where reusable, bounded JSON-LD/site adapters as necessary.

Acceptance:

- Directory-based inventory procedure is documented.
- Pilot central portal, IT-centre, student-assistant and department examples.
- Research networks and selected individual institutes included.
- A portal with no usable collector stays visibly pending, not falsely “covered”.
- PDF-only cases are tracked; extraction is a separate tested task if needed.
- Scholarships/programmes do not masquerade as ordinary employment.

### Work item 9 — Public sector, specialist sources and APIs

Acceptance:

- Pilot public-sector employers and at least one specialist discovery source.
- Evaluate Adzuna/Jooble only after access is established.
- A source activation records pagination, terms, attribution, freshness and geographic evidence.
- No guessed public API or bypass of blocked pages.

### Work item 10 — Frontend discoverability and remote-Europe expansion

Acceptance:

- Location text is searchable, including smaller towns.
- Multiple locations and freshness/workplace states display correctly.
- Existing trackers/backups and the concurrent CV-fit feature remain compatible.
- Germany-first results and broader Europe-remote candidates have explicit eligibility semantics.

Do not bundle these into one giant rewrite.

## 14. Required checks before each implementation PR

Run the repository's documented checks in its supported environment:

```bash
cd scanner
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run pytest -q
```

For changes touching frontend types, UI, data loading, tracker identity or filters:

```bash
cd web
npm ci
npx oxlint
npm test
npm run build
```

Also verify a small live sample of the newly enabled source after offline fixtures pass. Keep network verification separate from deterministic CI tests.

Minimum source acceptance checklist:

- [ ] Employer/site identity confirmed from official careers navigation.
- [ ] Collection and public-display conditions documented.
- [ ] Stable source/board/job IDs.
- [ ] Complete pagination or an explicit incomplete outcome.
- [ ] Description/detail availability stated.
- [ ] All relevant locations/countries preserved.
- [ ] Remote/hybrid and German eligibility evidence separated.
- [ ] Original/application URLs valid and attribution preserved.
- [ ] Legitimate empty, malformed response, individual bad record, 429 and page-two failure tested.
- [ ] No loss of prior jobs from partial/failing scans.
- [ ] first_seen and tracker identity preserved.
- [ ] Added provider classified as direct/aggregator explicitly.
- [ ] Fixture, scan report, source docs and checklist updated.
- [ ] Internal state cannot leak through data/*.json copying.
- [ ] Freshness and duplicate outcomes inspected.

## 15. Copyable brief for Devin

> Expand Stellenkompass job-source coverage for Germany using this handoff and its companion source catalog. Start from current main, inspect the pinned-review differences and coordinate with the existing CV-fit PR. Keep the Python scanner + static React/GitHub Pages design. First fix conservative deduplication/identity continuity, country evidence/Ashby secondary addresses, partial-scan safety and freshness. Then improve Lever EU, Personio variants and SmartRecruiters descriptions, add verified low-volume employer boards, and implement Recruitee and Teamtailor with offline fixtures and complete pagination. Build a university/research institution discovery inventory rather than claiming the sample institutions cover Germany. Treat catalog entries as disabled research candidates until their actual feed, identity, permissions and Germany coverage are verified. Preserve existing Job IDs, saved tracker data and skills/CV compatibility. Use focused issues/PRs with the repository's checks and documentation updates; do not replace the app architecture or implement automated applications as part of this expansion.

## Appendix A. Source-catalog status definitions

- **P1:** first discovery/implementation wave, after the core correctness fixes.
- **P2:** second wave or selective pilots after the shared pipeline is safe.
- **P3:** later, access/partnership dependent, or driven by measured gaps.
- **documented_public_interface:** official documentation was reviewed; each actual tenant and current conditions still need validation.
- **documented_credentialed_interface:** API documented; credentials/access still required.
- **discovery_candidate:** official/site seed only; no functioning machine interface is claimed.
- **present_in_reviewed_config:** found in the pinned repository config; not independently live-tested in this review.

The following inventory is deliberately broader than the immediate implementation backlog. Platforms and directories are discovery multipliers, not job feeds in themselves.


### Recruiting platforms

Default investigation route: Employer-specific documented public API or RSS; validate each actual tenant before activation.

| Source | Priority | Evidence / next step |
| --- | --- | --- |
| [Tellent Recruitee](https://recruitee.com/) | P1 | Documented interface; validate actual feed; Fetch published offers, handle multiple locations and translations. [Documentation](https://docs.recruitee.com/reference/offers) |
| [Teamtailor](https://www.teamtailor.com/) | P1 | Documented interface; validate actual feed; RSS defaults to 100 entries; paginate with offset/per_page; custom careers domains. [Documentation](https://support.teamtailor.com/en/articles/11171756-rss-feed-how-to-guide) |
| [softgarden](https://softgarden.com/) | P2 | Discovery candidate. |
| [rexx systems](https://www.rexx-systems.com/) | P2 | Discovery candidate. |
| [d.vinci](https://www.dvinci.de/) | P2 | Discovery candidate. |
| [BITE](https://www.b-ite.de/) | P2 | Discovery candidate. |
| [HR4YOU](https://www.hr4you.de/) | P2 | Discovery candidate. |
| [onlyfy / Prescreen](https://onlyfy.com/) | P2 | Discovery candidate. |
| [Workable](https://www.workable.com/) | P2 | Discovery candidate; Assess public careers/widget route separately from authenticated customer APIs. |
| [Workday](https://www.workday.com/) | P2 | Discovery candidate; Tenant/site-specific; website endpoints are not a guaranteed supported public API. |
| [SAP SuccessFactors](https://www.sap.com/products/hcm/recruiting-software.html) | P2 | Discovery candidate; Keep legacy careers-system detection distinct from current SmartRecruiters branding. |
| [Oracle Recruiting / Taleo](https://www.oracle.com/human-capital-management/recruiting/) | P2 | Discovery candidate. |
| [iCIMS](https://www.icims.com/) | P2 | Discovery candidate. |
| [BambooHR](https://www.bamboohr.com/) | P3 | Discovery candidate. |
| [Breezy HR](https://breezy.hr/) | P3 | Discovery candidate. |
| [Pinpoint](https://www.pinpointhq.com/) | P3 | Discovery candidate. |
| [Jobvite](https://www.jobvite.com/) | P3 | Discovery candidate. |
| [Spark Hire Recruit / Comeet](https://www.comeet.com/) | P3 | Discovery candidate. |
| [Abacus Umantis](https://umantis.com/) | P3 | Discovery candidate. |
| [Persis / Atoria](https://atoria-software.com/de) | P3 | Discovery candidate. |
| [coveto](https://www.coveto.de/) | P3 | Discovery candidate. |
| [Connectoor](https://www.connectoor.com/) | P3 | Discovery candidate. |
| [Talention](https://www.talention.de/) | P3 | Discovery candidate. |
| [talentsconnect](https://www.talentsconnect.com/) | P3 | Discovery candidate. |
| [Fountain](https://www.fountain.com/) | P3 | Discovery candidate. |

### Credentialed aggregator APIs

Default investigation route: Documented job-search API; credential and permitted-use validation required.

| Source | Priority | Evidence / next step |
| --- | --- | --- |
| [Adzuna](https://www.adzuna.de/) | P2 | Documented API; obtain access; Credentials required; assess pagination/query caps; descriptions may be snippets. [Documentation](https://developer.adzuna.com/docs/search) |
| [Jooble](https://de.jooble.org/) | P2 | Documented API; obtain access; Request an API key and confirm Germany access/redisplay terms. [Documentation](https://jooble.org/api/about) |

### Documented remote feeds

Default investigation route: Documented public feed/API; confirm Germany eligibility and provider display conditions.

| Source | Priority | Evidence / next step |
| --- | --- | --- |
| [Himalayas](https://himalayas.app/) | P2 | Documented interface; validate actual feed; Cursor pagination; preserve applicationLink, attribution and expiry; public data redistribution needs careful review. [Documentation](https://himalayas.app/api) |
| [We Work Remotely](https://weworkremotely.com/) | P2 | Documented interface; validate actual feed; Public RSS with attribution; inspect geographic restrictions. [Documentation](https://weworkremotely.com/remote-job-rss-feed) |
| [Remotive](https://remotive.com/) | P2 | Documented interface; validate actual feed; Public results delayed 24 hours; attribution and restrictions apply. [Documentation](https://github.com/remotive-com/remote-jobs-api) |
| [Remote OK](https://remoteok.com/) | P2 | Documented interface; validate actual feed; API response starts with metadata/terms; skip metadata as a job, retain attribution. [Documentation](https://remoteok.com/api) |

### General German job boards

Default investigation route: Employer discovery; investigate provider-supported access/partnership before automated collection.

| Source | Priority | Evidence / next step |
| --- | --- | --- |
| [Bundesagentur für Arbeit Jobsuche](https://www.arbeitsagentur.de/jobsuche/) | P3 | Discovery candidate; Official access/cooperation investigation; do not treat 403 as permission to bypass. |
| [Stepstone](https://www.stepstone.de/) | P3 | Discovery candidate. |
| [Indeed Germany](https://de.indeed.com/) | P3 | Discovery candidate. |
| [LinkedIn Jobs](https://www.linkedin.com/jobs/) | P3 | Discovery candidate. |
| [XING Jobs](https://www.xing.com/jobs) | P3 | Discovery candidate. |
| [stellenanzeigen.de](https://www.stellenanzeigen.de/) | P3 | Discovery candidate. |
| [Jobware](https://www.jobware.de/) | P3 | Discovery candidate. |
| [Yourfirm](https://www.yourfirm.de/) | P3 | Discovery candidate. |
| [meinestadt Jobs](https://jobs.meinestadt.de/) | P3 | Discovery candidate. |
| [kimeta](https://www.kimeta.de/) | P3 | Discovery candidate. |
| [Regio-Jobanzeiger](https://www.regio-jobanzeiger.de/) | P3 | Discovery candidate. |
| [FAZ Stellenmarkt](https://stellenmarkt.faz.net/) | P3 | Discovery candidate. |
| [Süddeutsche Stellenmarkt](https://stellenmarkt.sueddeutsche.de/) | P3 | Discovery candidate. |

### Tech, startup and specialist boards

Default investigation route: Discovery plus site-specific access assessment; official page is a seed, not a verified machine feed.

| Source | Priority | Evidence / next step |
| --- | --- | --- |
| [GermanTechJobs](https://germantechjobs.de/) | P2 | Discovery candidate. |
| [get in IT](https://www.get-in-it.de/) | P2 | Discovery candidate. |
| [heise jobs](https://jobs.heise.de/) | P2 | Discovery candidate. |
| [ictjob.de](https://www.ictjob.de/) | P2 | Discovery candidate. |
| [IT-Jobs.de](https://www.it-jobs.de/) | P2 | Discovery candidate. |
| [jobvector](https://www.jobvector.de/) | P2 | Discovery candidate. |
| [Berlin Startup Jobs](https://berlinstartupjobs.com/) | P2 | Discovery candidate. |
| [Wellfound](https://wellfound.com/location/berlin) | P2 | Discovery candidate. |
| [Instaffo](https://www.instaffo.com/) | P2 | Discovery candidate. |
| [JOIN](https://join.com/) | P2 | Discovery candidate; Employer pages, not an assumed global public jobs API. |
| [Workwise](https://www.workwise.io/) | P2 | Discovery candidate. |
| [EnglishJobs Germany](https://englishjobs.de/) | P2 | Discovery candidate. |
| [GoodJobs](https://goodjobs.eu/) | P2 | Discovery candidate. |
| [greenjobs](https://www.greenjobs.de/) | P2 | Discovery candidate. |
| [dasauge jobs](https://dasauge.de/jobs/) | P2 | Discovery candidate. |
| [ingenieur.de](https://www.ingenieur.de/karriere/stellenangebote/) | P2 | Discovery candidate. |

### Student and early-career sources

Default investigation route: Discover accessible public vacancies and original employer pages; respect institution/login boundaries.

| Source | Priority | Evidence / next step |
| --- | --- | --- |
| [stellenwerk](https://www.stellenwerk.de/) | P2 | Discovery candidate. |
| [JobTeaser](https://www.jobteaser.com/) | P2 | Discovery candidate. |
| [Absolventa](https://www.absolventa.de/) | P2 | Discovery candidate. |
| [UNICUM Karriere](https://karriere.unicum.de/) | P2 | Discovery candidate. |

### Academic boards

Default investigation route: Academic discovery; inspect supported export/feed or public listing route per provider.

| Source | Priority | Evidence / next step |
| --- | --- | --- |
| [EURAXESS](https://euraxess.ec.europa.eu/jobs) | P1 | Discovery candidate. |
| [academics](https://www.academics.de/) | P1 | Discovery candidate. |
| [Academic Positions](https://academicpositions.com/de) | P1 | Discovery candidate. |
| [DUZ Wissenschaftskarriere](https://wissenschaftskarriere.duz.de/) | P1 | Discovery candidate. |
| [DAAD PhDGermany](https://www.daad.de/en/studying-in-germany/phd-studies-research/phd-germany/) | P1 | Discovery candidate; Distinguish salaried PhD positions from scholarships and programmes. |

### Discovery directories

Default investigation route: Use to identify institutions and their official domains; no assumed bulk vacancy API.

| Source | Priority | Evidence / next step |
| --- | --- | --- |
| [Hochschulkompass](https://www.hochschulkompass.de/) | P1 | Discovery candidate; Institution inventory, not a vacancy feed. |
| [Research in Germany](https://www.research-in-germany.org/your-goal/research-position/find-a-job.html) | P1 | Discovery candidate; Research employer/source discovery. |
| [Jobbörsen-Verzeichnis](https://www.jobboersen-verzeichnis.de/) | P3 | Discovery candidate; Candidate discovery only; check for stale sites. |

### Research organizations

Default investigation route: Discover employer-specific careers page and assess public feed/structured data; do not assume an open API.

| Source | Priority | Evidence / next step |
| --- | --- | --- |
| [Fraunhofer](https://jobs.fraunhofer.de/) | P1 | Discovery candidate. |
| [Max Planck Society](https://www.mpg.de/jobboard) | P1 | Discovery candidate. |
| [Helmholtz Association](https://www.helmholtz.de/karriere/) | P1 | Discovery candidate. |
| [Leibniz Association](https://www.leibniz-gemeinschaft.de/karriere/stellenportal) | P1 | Discovery candidate; Inspect German and English versions. |
| [DLR](https://www.dlr.de/de/karriere) | P1 | Discovery candidate. |
| [Forschungszentrum Jülich](https://www.fz-juelich.de/de/karriere) | P1 | Discovery candidate. |
| [DESY](https://www.desy.de/career/) | P1 | Discovery candidate. |
| [DFKI](https://www.dfki.de/web/karriere) | P1 | Discovery candidate. |

### University pilot sources

Default investigation route: Discover employer-specific careers page and assess public feed/structured data; do not assume an open API.

| Source | Priority | Evidence / next step |
| --- | --- | --- |
| [Technical University of Munich](https://www.tum.de/ueber-die-tum/karriere-und-jobs/stellenangebote) | P1 | Discovery candidate. |
| [RWTH Aachen](https://beesite-f.zhv.rwth-aachen.de/index.php?ac=start) | P1 | Discovery candidate. |
| [RWTH Aachen IT Center](https://www.itc.rwth-aachen.de/cms/it-center/karriere/arbeiten-am-it-center/~eput/stellenangebote/) | P1 | Discovery candidate. |
| [Karlsruhe Institute of Technology](https://www.kit.edu/karriere/) | P1 | Discovery candidate. |
| [TU Dresden](https://tu-dresden.de/tu-dresden/arbeiten-an-der-tud/stellenangebote/) | P1 | Discovery candidate. |
| [University of Hamburg](https://www.uni-hamburg.de/stellenangebote.html) | P1 | Discovery candidate. |
| [University of Bonn](https://www.uni-bonn.de/de/universitaet/arbeiten-an-der-uni/stellenangebote) | P1 | Discovery candidate. |

### Public-sector sources

Default investigation route: Discover employer-specific careers page and assess public feed/structured data; do not assume an open API.

| Source | Priority | Evidence / next step |
| --- | --- | --- |
| [INTERAMT](https://interamt.de/) | P2 | Discovery candidate. |
| [service.bund.de](https://www.service.bund.de/) | P2 | Discovery candidate. |
| [Federal careers portal](https://karriere.bund.de/) | P2 | Discovery candidate. |
| [Berlin public careers](https://www.berlin.de/karriereportal/) | P2 | Discovery candidate. |
| [Hamburg public careers](https://www.karriere.hamburg/) | P2 | Discovery candidate. |
| [Lower Saxony public careers](https://karriere.niedersachsen.de/) | P2 | Discovery candidate. |
| [Saxony public careers](https://www.karriere.sachsen.de/) | P2 | Discovery candidate. |
| [Hesse public careers](https://karriere.hessen.de/) | P2 | Discovery candidate. |
| [North Rhine-Westphalia careers](https://karriere.nrw/) | P2 | Discovery candidate. |
| [Dataport](https://www.dataport.de/karriere/) | P2 | Discovery candidate. |
| [BWI](https://www.bwi.de/karriere) | P2 | Discovery candidate. |
| [ITZBund](https://www.itzbund.de/) | P2 | Discovery candidate. |

### Recruitment agencies

Default investigation route: Find client vacancies; assess public collection method; preserve undisclosed-client uncertainty.

| Source | Priority | Evidence / next step |
| --- | --- | --- |
| [Hays](https://www.hays.de/jobsuche) | P2 | Discovery candidate. |
| [Computer Futures](https://www.computerfutures.com/de-de/) | P2 | Discovery candidate. |
| [Optimus Search](https://www.optimussearch.com/) | P2 | Discovery candidate. |
| [Ratbacher](https://www.ratbacher.com/de/) | P2 | Discovery candidate. |
| [Michael Page](https://www.michaelpage.de/) | P2 | Discovery candidate. |
| [Robert Half](https://www.roberthalf.com/de/de) | P2 | Discovery candidate. |
| [Amadeus Fire](https://www.amadeus-fire.de/) | P2 | Discovery candidate. |
| [APRIORI](https://www.apriori.de/) | P2 | Discovery candidate. |
| [auteega](https://www.auteega.com/) | P2 | Discovery candidate. |
| [GULP / Randstad Professional](https://www.gulp.de/) | P2 | Discovery candidate. |
| [FERCHAU](https://www.ferchau.com/) | P2 | Discovery candidate. |
| [Randstad Digital](https://www.randstaddigital.com/) | P2 | Discovery candidate. |

### Freelance projects

Default investigation route: Public project discovery/access assessment; keep contract projects separate from salaried vacancies.

| Source | Priority | Evidence / next step |
| --- | --- | --- |
| [freelancermap](https://www.freelancermap.de/) | P3 | Discovery candidate. |
| [freelance.de](https://www.freelance.de/) | P3 | Discovery candidate. |
| [SOLCOM](https://www.solcom.de/) | P3 | Discovery candidate. |

### Additional remote/Europe boards

Default investigation route: Assess public access and residence restrictions; remote does not establish Germany eligibility.

| Source | Priority | Evidence / next step |
| --- | --- | --- |
| [EU Remote Jobs](https://euremotejobs.com/) | P3 | Discovery candidate. |
| [Remote Rocketship](https://www.remoterocketship.com/) | P3 | Discovery candidate. |
| [remotely.de](https://www.remotely.de/) | P3 | Discovery candidate. |
| [Just Join IT](https://justjoin.it/) | P3 | Discovery candidate. |
| [No Fluff Jobs](https://nofluffjobs.com/) | P3 | Discovery candidate. |

### Commercial data suppliers

Default investigation route: Commercial feed/API evaluation only; request German sample, redistribution terms and coverage evidence.

| Source | Priority | Evidence / next step |
| --- | --- | --- |
| [TheirStack](https://theirstack.com/en/job-posting-api) | P3 | Discovery candidate. |
| [LinkUp](https://www.linkup.com/) | P3 | Discovery candidate. |

### Additional employer careers-page seeds

Default investigation route: Discover current ATS/feed from official careers page; verify Germany vacancies; no guessed board slugs.

| Source | Priority | Evidence / next step |
| --- | --- | --- |
| [SAP](https://jobs.sap.com/) | P1 | Discovery candidate. |
| [Siemens](https://jobs.siemens.com/) | P1 | Discovery candidate. |
| [Deutsche Telekom](https://careers.telekom.com/) | P1 | Discovery candidate. |
| [Deutsche Bahn / DB Systel](https://db.jobs/) | P1 | Discovery candidate. |
| [BMW Group](https://www.bmwgroup.jobs/de/de.html) | P1 | Discovery candidate. |
| [Mercedes-Benz](https://group.mercedes-benz.com/karriere/) | P1 | Discovery candidate. |
| [Infineon](https://www.infineon.com/careers) | P1 | Discovery candidate. |
| [DATEV](https://karriere.datev.de/) | P1 | Discovery candidate. |
| [Bechtle](https://www.bechtle.com/karriere) | P1 | Discovery candidate. |
| [secunet](https://www.secunet.com/ueber-uns/karriere) | P1 | Discovery candidate. |
| [adesso](https://www.adesso.de/de/karriere/index.jsp) | P1 | Discovery candidate. |
| [Materna](https://www.materna.de/) | P1 | Discovery candidate. |
| [Allianz](https://careers.allianz.com/) | P1 | Discovery candidate. |
| [DHL](https://careers.dhl.com/) | P1 | Discovery candidate. |
| [Schwarz Corporate Solutions](https://jobs.schwarz/) | P1 | Discovery candidate. |
| [Amazon / AWS](https://www.amazon.jobs/) | P1 | Discovery candidate. |
| [Zalando](https://jobs.zalando.com/) | P1 | Discovery candidate. |

## Appendix B. Employer boards already configured

Copied from companies.yaml at the pinned commit. These entries are already implemented through existing adapters; they are not newly validated tenant recommendations. Links below are discovery URLs derived from the configured provider/identifier and may redirect or change. Verify before editing provider assignments.

| Employer | Adapter | Configured board | Derived careers URL |
| --- | --- | --- | --- |
| N26 | greenhouse | `n26` | [Careers](https://job-boards.greenhouse.io/n26) |
| Celonis | greenhouse | `celonis` | [Careers](https://job-boards.greenhouse.io/celonis) |
| GetYourGuide | greenhouse | `getyourguide` | [Careers](https://job-boards.greenhouse.io/getyourguide) |
| Helsing | greenhouse | `helsing` | [Careers](https://job-boards.greenhouse.io/helsing) |
| Contentful | greenhouse | `contentful` | [Careers](https://job-boards.greenhouse.io/contentful) |
| HelloFresh | greenhouse | `hellofresh` | [Careers](https://job-boards.greenhouse.io/hellofresh) |
| SumUp | greenhouse | `sumup` | [Careers](https://job-boards.greenhouse.io/sumup) |
| Raisin | greenhouse | `raisin` | [Careers](https://job-boards.greenhouse.io/raisin) |
| commercetools | greenhouse | `commercetools` | [Careers](https://job-boards.greenhouse.io/commercetools) |
| Flix | greenhouse | `flix` | [Careers](https://job-boards.greenhouse.io/flix) |
| Solaris | greenhouse | `solarisbank` | [Careers](https://job-boards.greenhouse.io/solarisbank) |
| MOIA | greenhouse | `moia` | [Careers](https://job-boards.greenhouse.io/moia) |
| Trade Republic | greenhouse | `traderepublicbank` | [Careers](https://job-boards.greenhouse.io/traderepublicbank) |
| Isar Aerospace | greenhouse | `isaraerospace` | [Careers](https://job-boards.greenhouse.io/isaraerospace) |
| IONOS | greenhouse | `ionos` | [Careers](https://job-boards.greenhouse.io/ionos) |
| trivago | greenhouse | `trivago` | [Careers](https://job-boards.greenhouse.io/trivago) |
| Staffbase | greenhouse | `staffbase` | [Careers](https://job-boards.greenhouse.io/staffbase) |
| Moonfare | greenhouse | `moonfare` | [Careers](https://job-boards.greenhouse.io/moonfare) |
| FREENOW | greenhouse | `freenow` | [Careers](https://job-boards.greenhouse.io/freenow) |
| Databricks | greenhouse | `databricks` | [Careers](https://job-boards.greenhouse.io/databricks) |
| Stripe | greenhouse | `stripe` | [Careers](https://job-boards.greenhouse.io/stripe) |
| Cloudflare | greenhouse | `cloudflare` | [Careers](https://job-boards.greenhouse.io/cloudflare) |
| GitLab | greenhouse | `gitlab` | [Careers](https://job-boards.greenhouse.io/gitlab) |
| MongoDB | greenhouse | `mongodb` | [Careers](https://job-boards.greenhouse.io/mongodb) |
| Elastic | greenhouse | `elastic` | [Careers](https://job-boards.greenhouse.io/elastic) |
| Datadog | greenhouse | `datadog` | [Careers](https://job-boards.greenhouse.io/datadog) |
| Figma | greenhouse | `figma` | [Careers](https://job-boards.greenhouse.io/figma) |
| Okta | greenhouse | `okta` | [Careers](https://job-boards.greenhouse.io/okta) |
| Parloa | ashby | `parloa` | [Careers](https://jobs.ashbyhq.com/parloa) |
| n8n | ashby | `n8n` | [Careers](https://jobs.ashbyhq.com/n8n) |
| Forto | ashby | `forto` | [Careers](https://jobs.ashbyhq.com/forto) |
| Billie | ashby | `billie` | [Careers](https://jobs.ashbyhq.com/billie) |
| Pliant | ashby | `pliant` | [Careers](https://jobs.ashbyhq.com/pliant) |
| Wayve | ashby | `wayve` | [Careers](https://jobs.ashbyhq.com/wayve) |
| DeepL | ashby | `deepl` | [Careers](https://jobs.ashbyhq.com/deepl) |
| Aleph Alpha | ashby | `alephalpha` | [Careers](https://jobs.ashbyhq.com/alephalpha) |
| Black Forest Labs | ashby | `black-forest-labs` | [Careers](https://jobs.ashbyhq.com/black-forest-labs) |
| tacto | ashby | `tacto` | [Careers](https://jobs.ashbyhq.com/tacto) |
| Enpal | ashby | `enpal` | [Careers](https://jobs.ashbyhq.com/enpal) |
| Moss | ashby | `moss` | [Careers](https://jobs.ashbyhq.com/moss) |
| Buena | ashby | `buena` | [Careers](https://jobs.ashbyhq.com/buena) |
| Ostrom | ashby | `ostrom` | [Careers](https://jobs.ashbyhq.com/ostrom) |
| Knowunity | ashby | `knowunity` | [Careers](https://jobs.ashbyhq.com/knowunity) |
| OpenAI | ashby | `openai` | [Careers](https://jobs.ashbyhq.com/openai) |
| Cohere | ashby | `cohere` | [Careers](https://jobs.ashbyhq.com/cohere) |
| ElevenLabs | ashby | `elevenlabs` | [Careers](https://jobs.ashbyhq.com/elevenlabs) |
| Synthesia | ashby | `synthesia` | [Careers](https://jobs.ashbyhq.com/synthesia) |
| Perplexity | ashby | `perplexity` | [Careers](https://jobs.ashbyhq.com/perplexity) |
| Linear | ashby | `linear` | [Careers](https://jobs.ashbyhq.com/linear) |
| Notion | ashby | `notion` | [Careers](https://jobs.ashbyhq.com/notion) |
| Supabase | ashby | `supabase` | [Careers](https://jobs.ashbyhq.com/supabase) |
| Pigment | lever | `pigment` | [Careers](https://jobs.lever.co/pigment) |
| Agicap | lever | `agicap` | [Careers](https://jobs.lever.co/agicap) |
| Contentsquare | lever | `contentsquare` | [Careers](https://jobs.lever.co/contentsquare) |
| Bosch | smartrecruiters | `BoschGroup` | [Careers](https://jobs.smartrecruiters.com/BoschGroup) |
| Continental | smartrecruiters | `Continental` | [Careers](https://jobs.smartrecruiters.com/Continental) |
| Delivery Hero | smartrecruiters | `DeliveryHero` | [Careers](https://jobs.smartrecruiters.com/DeliveryHero) |
| AUTO1 Group | smartrecruiters | `Auto1` | [Careers](https://jobs.smartrecruiters.com/Auto1) |
| SIXT | smartrecruiters | `Sixt` | [Careers](https://jobs.smartrecruiters.com/Sixt) |
| tado° | personio | `tado` | [Careers](https://tado.jobs.personio.de) |
| ottonova | personio | `ottonova` | [Careers](https://ottonova.jobs.personio.de) |
| 1KOMMA5° | personio | `1komma5grad` | [Careers](https://1komma5grad.jobs.personio.de) |
| Everphone | personio | `everphone` | [Careers](https://everphone.jobs.personio.de) |

## Appendix C. How to maintain this documentation

1. Revalidate the current repository commit before implementation; generated daily data commits will move main even without code changes.
2. Update runtime config only for verified source instances.
3. Keep candidate discovery records separate from operational state and credentials.
4. For each activated source, record official docs, actual tenant URL, last validation date, sample IDs, pagination, coverage limitations, freshness and display conditions.
5. Update DATA_SOURCES.md, CHECKLIST.md and DECISIONS.md through the repository's existing workflow.
6. Record why a candidate was deferred: no current relevant jobs, unknown provider, blocked access, unsupported export, insufficient permission, duplicate coverage, or maintenance cost. A small job count alone is not a reason to exclude it.
7. Never describe this inventory as all German employers or all vacancies. Directory discovery and ongoing source maintenance are part of the product.

This is an implementation handoff grounded in the reviewed code, with a broad research inventory. Its live-source and test limitations are listed in Section 2.

