"""Workday career sites, via the public CXS endpoint the site itself calls:
POST https://{board}.{instance}.myworkdayjobs.com/wday/cxs/{board}/{site}/jobs

The list has no job text, only title, location and a relative "Posted N Days Ago".
When the site has a Germany country facet, or location facets naming Germany, we ask for
those roles only and treat them as country DE; otherwise we read every role and decide by
location text. `total` is only sent with the first page.
"""

from __future__ import annotations

import re
from datetime import UTC, date, datetime, timedelta

from ..http import Fetcher
from ..models import Job
from ._common import Capped, build_job

PAGE = 20  # the CXS maximum
MAX_PAGES = 50
COUNTRY_FACETS = ("locationCountry", "locationHierarchy1", "Location_Country")
GERMANY = ("Germany", "Deutschland")
_NAMES_GERMANY = re.compile(r"\b(Germany|Deutschland)\b")
_POSTED = re.compile(r"posted (today|yesterday|(\d+) days? ago)", re.I)


def _base(board: str, instance: str) -> str:
    return f"https://{board}.{instance}.myworkdayjobs.com"


def _germany_facet(facets: list[dict]) -> dict[str, list[str]]:
    for facet in facets:
        values = facet.get("values") or []
        if facet.get("facetParameter") in COUNTRY_FACETS:
            ids = [v["id"] for v in values if v.get("descriptor") in GERMANY and v.get("id")]
            if ids:
                return {facet["facetParameter"]: ids}
        nested = _germany_facet([v for v in values if "facetParameter" in v])
        if nested:
            return nested
    return {}


def _germany_locations(facets: list[dict]) -> dict[str, list[str]]:
    for facet in facets:
        values = facet.get("values") or []
        if facet.get("facetParameter") == "locations":
            ids = [v["id"] for v in values if _NAMES_GERMANY.search(v.get("descriptor") or "")]
            return {"locations": ids} if ids else {}
        nested = _germany_locations([v for v in values if "facetParameter" in v])
        if nested:
            return nested
    return {}


def fetch(fetcher: Fetcher, board: str, instance: str, site: str) -> dict:
    url = f"{_base(board, instance)}/wday/cxs/{board}/{site}/jobs"
    first = fetcher.post_json(url, {"appliedFacets": {}, "limit": 1, "offset": 0, "searchText": ""})
    facets = _germany_facet(first.get("facets") or []) or _germany_locations(
        first.get("facets") or []
    )
    total = 0
    raw = {"site": site, "instance": instance, "germany": bool(facets), "pages": []}
    for n in range(MAX_PAGES):
        page = fetcher.post_json(
            url, {"appliedFacets": facets, "limit": PAGE, "offset": n * PAGE, "searchText": ""}
        )
        raw["pages"].append(page)
        total = total or page.get("total") or 0
        if len(page.get("jobPostings") or []) < PAGE or (n + 1) * PAGE >= total:
            return raw
    raise Capped(raw)


def _posted(label: str, today: date) -> str:
    m = _POSTED.search(label or "")
    if not m:
        return ""  # "Posted 30+ Days Ago" gives no date
    days = 0 if m.group(1).lower() == "today" else 1 if m.group(2) is None else int(m.group(2))
    return f"{today - timedelta(days=days):%Y-%m-%d}T00:00:00Z"


def _location(posting: dict) -> str:
    text = posting.get("locationsText") or ""
    if text and not re.fullmatch(r"\d+ Locations?", text):
        return text
    m = re.match(r"/job/([^/]+)/", posting.get("externalPath") or "")
    return " - ".join(p.replace("-", " ") for p in m.group(1).split("---")) if m else ""


def parse(
    raw: dict, board: str, company: str | None = None, today: date | None = None
) -> list[Job]:
    today = today or datetime.now(UTC).date()
    base = f"{_base(board, raw['instance'])}/{raw['site']}"
    jobs: list[Job] = []
    seen: set[str] = set()
    for page in raw["pages"]:
        for posting in page.get("jobPostings") or []:
            path = posting.get("externalPath") or ""
            job_id = path.rsplit("_", 1)[-1] if "_" in path else ""
            if not job_id or job_id in seen:
                continue
            seen.add(job_id)
            location = _location(posting)
            job = build_job(
                source="workday",
                board=board,
                job_id=job_id,
                title=(posting.get("title") or "").strip(),
                company=company or board,
                locations=[location],
                country_codes=["DE"] if raw["germany"] else None,
                url=f"{base}{path}",
                posted_at=_posted(posting.get("postedOn") or "", today),
            )
            if job:
                jobs.append(job)
    return jobs
