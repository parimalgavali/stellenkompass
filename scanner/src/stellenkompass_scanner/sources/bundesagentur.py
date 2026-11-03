"""Bundesagentur für Arbeit Jobsuche API (v6), the job board of the German employment agency.

The API key is the public one the BA's own web and mobile apps send; it is documented at
https://github.com/bundesAPI/jobsuche-api and is not a secret.
"""

from __future__ import annotations

from ..http import Fetcher
from ..models import Job
from ..text import iso_date
from ._common import build_job

URL = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v6/jobs"
HEADERS = {"X-API-Key": "jobboerse-jobsuche"}
DETAIL_URL = "https://www.arbeitsagentur.de/jobsuche/jobdetail/{}"
PAGE_SIZE = 100
DEFAULTS = {"queries": ["Data Scientist"], "days": 30, "max_per_query": 500}

# Regular jobs and internships / working-student roles; skip apprenticeships and self-employment.
_KEEP = {"ARBEIT", "PRAKTIKUM_TRAINEE"}
_TYPE_HINT = {"PRAKTIKUM_TRAINEE": "praktikum"}


def fetch(fetcher: Fetcher, options: dict | None = None) -> list[dict]:
    """Search each configured term in Germany; one item per reference number."""
    opts = {**DEFAULTS, **(options or {})}
    pages = max(1, -(-int(opts["max_per_query"]) // PAGE_SIZE))
    found: dict[str, dict] = {}
    for query in opts["queries"]:
        for page in range(1, pages + 1):
            params = {
                "was": query,
                "wo": "Deutschland",
                "veroeffentlichtseit": opts["days"],
                "size": PAGE_SIZE,
                "page": page,
            }
            body = fetcher.get_json(URL, params=params, headers=HEADERS)
            items = body.get("ergebnisliste") or []
            for item in items:
                found.setdefault(item["referenznummer"], item)
            if len(items) < PAGE_SIZE or page * PAGE_SIZE >= (body.get("maxErgebnisse") or 0):
                break
    return list(found.values())


def _hints(item: dict) -> list[str]:
    hints = [_TYPE_HINT.get(item.get("stellenangebotsart", ""), "")]
    if item.get("istGeringfuegigeBeschaeftigung"):
        hints.append("minijob")
    elif not item.get("arbeitszeitVollzeit", True) and any(
        item.get(k) for k in item if k.startswith("arbeitszeitTeilzeit")
    ):
        hints.append("teilzeit")
    return hints


def parse(items: list[dict]) -> list[Job]:
    jobs = []
    for item in items:
        if item.get("stellenangebotsart") not in _KEEP:
            continue
        places = [(loc.get("adresse") or {}) for loc in item.get("stellenlokationen") or []]
        places = [p for p in places if p.get("land") == "DEUTSCHLAND"]
        if not places:
            continue
        refnr = item["referenznummer"]
        job = build_job(
            source="bundesagentur",
            source_id=refnr,
            title=item.get("stellenangebotsTitel", ""),
            company=item.get("firma", ""),
            locations=[p.get("ort") or "Germany" for p in places],
            url=DETAIL_URL.format(refnr),
            country_codes=["de"],
            remote=bool(item.get("homeofficemoeglich")),
            type_hints=_hints(item),
            posted_at=iso_date(item.get("datumErsteVeroeffentlichung")),
            tags=item.get("alleBerufe") or [],
            # BA postings are almost always German; the list API has no text to check.
            language="de",
        )
        if job:
            jobs.append(job)
    return jobs
