"""JOIN company pages: GET https://join.com/companies/{board}?page=N

The public page embeds its job list as Next.js page data (`__NEXT_DATA__`, under
`pageData` or `initialState`), five roles per page. robots.txt only disallows `/*/lp/`.
There's no cross-company search, so boards are listed in companies.yaml. The list has no
ad text. Apprenticeships are left out (D9).
"""

from __future__ import annotations

import json
import re

from ..http import Fetcher
from ..models import Job
from ._common import Capped, build_job, records

MAX_PAGES = 20
WORKPLACE = {"ONSITE": "onsite", "HYBRID": "hybrid", "REMOTE": "remote"}
_DATA = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)
_TRAINING = re.compile(r"\b(Ausbildung|Auszubildende|Duales Studium|Azubi)", re.I)
# Titles only, so German words in them mark a German ad (too short for detect_language).
_GERMAN = re.compile(
    r"[mwd]/[mwd]/[dmwx]|\w[:*]in\b|entwickl|berater|mitarbeit|leiter|werkstudent|praktik"
    r"|fachinformatik|kaufm|referent|sachbearbeit|ingenieur|festanstellung|betreuer",
    re.I,
)


def _page_data(html: str) -> dict:
    match = _DATA.search(html)
    if not match:
        raise ValueError("no __NEXT_DATA__ on the page")
    props = json.loads(match.group(1))["props"]["pageProps"]
    return props.get("pageData") or props["initialState"]  # pages use either name


def fetch(fetcher: Fetcher, board: str) -> list[dict]:
    pages: list[dict] = []
    for n in range(1, MAX_PAGES + 1):
        url = f"https://join.com/companies/{board}"
        data = _page_data(fetcher.get_text(url, params={"page": n} if n > 1 else None))
        pages.append({"company": data.get("company") or {}, "jobs": data.get("jobs") or {}})
        if n >= ((data.get("jobs") or {}).get("pagination") or {}).get("pageCount", 0):
            return pages
    raise Capped(pages)


def parse(raw: list[dict], board: str, company: str | None = None) -> list[Job]:
    jobs: list[Job] = []
    seen: set[str] = set()
    for page in raw:
        page_name = (page.get("company") or {}).get("name")
        name = (company if company and company != board else None) or page_name or board
        for item in records(page.get("jobs") or {}, "items", "id"):
            job_id, title = str(item["id"]), item.get("title") or ""
            kind = (item.get("employmentType") or {}).get("name") or ""
            if job_id in seen or kind == "Apprenticeship" or _TRAINING.search(title):
                continue
            seen.add(job_id)
            workplace = WORKPLACE.get(item.get("workplaceType") or "")
            city = (item.get("city") or {}).get("cityName") or ""
            job = build_job(
                source="join",
                board=board,
                job_id=job_id,
                title=title,
                company=name,
                locations=[city + (" (Remote)" if workplace == "remote" else "")],
                country_codes=[(item.get("country") or {}).get("iso3166") or ""],
                workplace=workplace,
                url=f"https://join.com/companies/{board}/{item.get('idParam') or job_id}",
                type_hints=[kind],
                posted_at=item.get("createdAt") or "",
                tags=[(item.get("category") or {}).get("name") or ""],
                language="de" if _GERMAN.search(title) else None,
            )
            if job:
                jobs.append(job)
    return jobs
