# Scanner

Collects open roles in Germany from public job sources and writes `data/jobs.json`.

## Run

```bash
cd scanner
uv sync
uv run stellenkompass-scan --out ../data      # full scan, about 1 minute
uv run pytest                                   # tests (no network)
uv run ruff check . && uv run ruff format --check .
```

## Add a company

Open `companies.yaml` and add the company's board name under its platform
(Greenhouse, Ashby, Lever, SmartRecruiters or Personio). The file explains how
to find the board name from the company's careers page.

## How it works

1. Each adapter in `src/stellenkompass_scanner/sources/` fetches one platform and
   turns its postings into the common `Job` format (`models.py`).
2. `geo.py` keeps only roles in Germany, or remote roles open to Germany/EU.
3. `classify.py` detects the posting language (en/de) and the job type; `skills.py` tags
   skills (Python, React, SQL, …) from title + description, and
   (full-time, working student, internship, thesis, part-time).
4. `dedupe.py` removes the same role posted on several sources (company board wins).
5. `run.py` writes `data/jobs.json` and `data/scan_report.json` (counts, errors and
   time per source). A failing board is recorded in the report, and its jobs from the last scan are
   kept (`carried` in the report), so one rate limit doesn't empty the list. 429s wait for
   `Retry-After` (max 60 s) before retrying.
