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
| `source` | `arbeitnow`, `greenhouse`, `ashby`, `smartrecruiters`, `lever`, `personio` |
| `posted_at` | ISO date if known |
| `tags` | Short tags from the source (skills, categories) |
| `snippet` | First ~300 characters of the description, plain text |

## Sources

| Source | How we read it | Config |
| --- | --- | --- |
| Arbeitnow | Paginated public API | none |
| Greenhouse | Public board API per company | `scanner/companies.yaml` → `greenhouse` |
| Ashby | Public posting API per company | `scanner/companies.yaml` → `ashby` |
| SmartRecruiters | Public postings API per company, `country=de` | `scanner/companies.yaml` → `smartrecruiters` |
| Lever | Public postings API per company | `scanner/companies.yaml` → `lever` |
| Personio | Public XML feed per company | `scanner/companies.yaml` → `personio` |

To follow a new company: find which job platform its careers page uses, then add its board name under that platform in `scanner/companies.yaml`.

## Not used (yet)
- Bundesagentur für Arbeit Jobsuche API: returned 403 from our dev machine. Retry from GitHub Actions in Phase 4.
- workingstudentjobs.de, LinkedIn, StepStone, Indeed: no public API, bot-protected or terms forbid scraping.
