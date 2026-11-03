# Data sources

All sources are public endpoints meant for listing open roles. The scanner reads them politely: one run per day, small pauses between requests, a clear User-Agent, and no scraping of sites that block bots.

## Common job format

Every adapter returns roles in this shape (see `scanner/stellenkompass_scanner/models.py`):

| Field | Meaning |
| --- | --- |
| `id` | Stable id: `{source}:{source_job_id}` |
| `title` | Job title |
| `company` | Company name |
| `location` | Location text as given by the source |
| `city` | Main German city if we can tell, else empty |
| `remote` | `true` if the posting says remote |
| `job_type` | `full_time`, `working_student`, `internship`, `part_time` or `other` |
| `language` | `en` or `de`: language the posting is written in |
| `url` | Link to the original posting (apply there) |
| `source` | `arbeitnow`, `bundesagentur`, `greenhouse`, `ashby`, `smartrecruiters`, `lever`, `personio`, `recruitee`, `teamtailor` |
| `posted_at` | ISO date if known |
| `tags` | Short tags from the source (skills, categories) |
| `skills` | Skills found in title + description by `skills.py` (curated list, max 12) |
| `snippet` | First ~300 characters of the description, plain text |
| `workplace_type` | `onsite` / `hybrid` / `remote` / `unknown`; `remote` is true only for fully remote |
| `source_board` | Company board slug (empty for aggregators) |
| `source_job_id` | The source's own id for the role |
| `aliases` | Earlier ids of this role and its copies on other sources (keeps tracker links and `first_seen`) |

## Sources

| Source | How we read it | Config |
| --- | --- | --- |
| Arbeitnow | Paginated public API | none |
| Bundesagentur für Arbeit | Jobsuche API v6, one search per term, `wo=Deutschland`, last 30 days | `scanner/companies.yaml` → `bundesagentur` (search terms) |
| Greenhouse | Public board API per company | `scanner/companies.yaml` → `greenhouse` |
| Ashby | Public posting API per company | `scanner/companies.yaml` → `ashby` |
| SmartRecruiters | Public postings API per company, `country=de`, plus each German posting's detail (`ref`) for the job text | `scanner/companies.yaml` → `smartrecruiters` |
| Lever | Public postings API per company, paged; `region: eu` for jobs.eu.lever.co | `scanner/companies.yaml` → `lever` |
| Personio | Public XML feed per company (`domain: jobs.personio.com`, `languages: [de, en]` optional) | `scanner/companies.yaml` → `personio` |
| Recruitee | Public offers API `https://<board>.recruitee.com/api/offers/` | `scanner/companies.yaml` → `recruitee` |
| Teamtailor | Public RSS `https://<host>/jobs.rss`, paged with `offset`/`per_page` (100 per page, max 20 pages) | `scanner/companies.yaml` → `teamtailor` |
| d.vinci | Public widget feed `https://<host>/jobPublication/list.json` (universities, research); Ausbildung skipped | `scanner/companies.yaml` → `dvinci`, see `docs/research/institutions.md` |
| Workday | Public CXS route `POST https://<tenant>.<wdN>.myworkdayjobs.com/wday/cxs/<tenant>/<site>/jobs`, filtered to Germany by facet; title and location only, no job text | `scanner/companies.yaml` → `workday` (`board`, `instance`, `site`) |
| SAP SuccessFactors | Career-site HTML fragment `https://<host>/tile-search-results/?startrow=N` (robots.txt allows it; `/services/` is disallowed); Germany facet where it works; Ausbildung skipped | `scanner/companies.yaml` → `successfactors` (`board` = host, optional `country: DE`) |

### Adding a company board
1. Open the company's careers page and click a role. The apply link shows the platform and board name:
   - `boards.greenhouse.io/<board>` or `job-boards.greenhouse.io/<board>` → `greenhouse`
   - `jobs.ashbyhq.com/<board>` → `ashby`
   - `jobs.lever.co/<board>` → `lever`
   - `jobs.smartrecruiters.com/<board>` → `smartrecruiters` (case-sensitive, e.g. `BoschGroup`)
   - `<board>.jobs.personio.de` → `personio`
   - `<board>.recruitee.com` → `recruitee`
   - `<board>.teamtailor.com` (or a custom careers host with a `/jobs.rss` feed) → `teamtailor`
2. Check that it has roles in Germany (from `scanner/`):
   ```bash
   uv run python -c "from stellenkompass_scanner.http import HttpFetcher; from stellenkompass_scanner.sources import greenhouse as s; print(len(s.parse(s.fetch(HttpFetcher(), 'n26'), 'n26')))"
   ```
3. Add `- { board: <board>, name: <Display name> }` under the platform in `scanner/companies.yaml`.

Add a verified board even if it has only one role in Germany; a board with zero roles today can stay too. (Boards once skipped by the old 3-role rule were re-checked and added: Wunderflats, kununu, KONUX, Dataiku (Greenhouse), HeyJobs (Ashby), Spotify (Lever), CLARK (Personio). Rasa stays out: its only role is "Worldwide · Remote".)

Candidate sources still to verify live in [research/source-catalog.json](research/source-catalog.json); never enable them in bulk.

### Bundesagentur für Arbeit (BA)
- Endpoint: `https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v6/jobs` with header `X-API-Key: jobboerse-jobsuche` (the public key the BA's own apps use; documented at github.com/bundesAPI/jobsuche-api).
- The old `pc/v4` path now answers `403 No match found for request`; that was the "403" we saw before, not an IP block.
- The BA has about 1 million postings, so we only ask for the search terms listed in `companies.yaml` (max 500 roles each). Add or remove terms there.
- Kept: `ARBEIT` and `PRAKTIKUM_TRAINEE` roles in Germany. Dropped: apprenticeships (`AUSBILDUNG`), self-employment, and roles abroad.
- The list API has no description, so skills come from the title only and language is set to `de`. Links go to the BA job page.
- Access caveat: this is the API the BA's own job search uses, not a data contract with us. Keep requests low (one daily scan) and switch it off in `aggregators` if the BA objects or changes its terms.

## Not used (yet)
- workingstudentjobs.de, LinkedIn, StepStone, Indeed: no public API, bot-protected or terms forbid scraping.
