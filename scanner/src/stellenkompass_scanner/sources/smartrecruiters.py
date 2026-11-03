"""SmartRecruiters public postings API: https://developers.smartrecruiters.com/docs/posting-api

The list has no job text, so German postings also get their detail (`ref`). Details are only
fetched for new or re-released postings: otherwise last scan's snippet and skills are reused.
"""

from __future__ import annotations

import logging

from ..geo import STATE_CODES, STATES, city_of
from ..http import Fetcher
from ..models import Job
from ..text import html_to_text, iso_date
from ._common import Capped, build_job, records

PAGE = 100
DETAIL_HOST = "https://api.smartrecruiters.com/"
MAX_DETAILS = 150  # new detail requests per board and run; the rest follow on later runs
USES_PREVIOUS = True
log = logging.getLogger(__name__)


def fetch(
    fetcher: Fetcher, board: str, max_pages: int = 20, known: dict[str, dict] | None = None
) -> dict:
    """`known` maps last scan's job ids to their saved fields."""
    url = f"https://api.smartrecruiters.com/v1/companies/{board}/postings"
    content: list[dict] = []
    for page in range(max_pages):
        body = fetcher.get_json(url, params={"limit": PAGE, "offset": page * PAGE, "country": "de"})
        batch = records(body, "content", "id")
        content.extend(batch)
        if len(batch) < PAGE or len(content) >= body.get("totalFound", 0):
            return {"content": _add_details(fetcher, board, content, known or {})}
    raise Capped({"content": _add_details(fetcher, board, content, known or {})})


def _add_details(fetcher: Fetcher, board: str, content: list[dict], known: dict) -> list[dict]:
    fetched = failed = 0
    for item in content:
        if not _wanted(item.get("location") or {}):
            continue
        prev = known.get(f"smartrecruiters:{board}-{item['id']}") or {}
        if not prev.get("snippet"):
            prev = {}
        if prev and prev.get("posted_at") == iso_date(item.get("releasedDate")):
            item["_cached"] = prev
            continue
        ref = item.get("ref") or ""
        if fetched >= MAX_DETAILS or not ref.startswith(DETAIL_HOST):
            item["_cached"] = prev
            continue
        fetched += 1
        try:
            sections = (fetcher.get_json(ref).get("jobAd") or {}).get("sections") or {}
            item["_description"] = " ".join(
                html_to_text(s.get("text") or "") for s in sections.values() if isinstance(s, dict)
            )
        except Exception:  # noqa: BLE001 - keep the summary and the old text
            failed += 1
            item["_cached"] = prev
    if failed:
        log.warning("smartrecruiters/%s: %d detail requests failed", board, failed)
    return content


def _wanted(location: dict) -> bool:
    return (location.get("country") or "").lower() == "de" and _german_region(location)


def _german_region(location: dict) -> bool:
    """The API's country=de filter also returns some foreign sites, so check region or city."""
    region = (location.get("region") or "").lower()
    if region in STATE_CODES or any(s in region for s in STATES):
        return True
    return not region or city_of(location.get("city") or "") != ""


def parse(raw: dict, board: str, company: str | None = None) -> list[Job]:
    jobs = []
    for item in raw.get("content", []):
        loc = item.get("location") or {}
        if not _wanted(loc):
            continue
        city = loc.get("city") or ""
        language = ((item.get("language") or {}).get("code") or "")[:2]
        job = build_job(
            source="smartrecruiters",
            board=board,
            job_id=str(item["id"]),
            title=item.get("name", ""),
            company=company or (item.get("company") or {}).get("name") or board,
            locations=[f"{city}, Germany" if city else "Germany"]
            + (["Remote"] if loc.get("remote") else []),
            url=f"https://jobs.smartrecruiters.com/{board}/{item['id']}",
            description=item.get("_description", ""),
            country_codes=["de"],
            workplace="remote" if loc.get("remote") else "hybrid" if loc.get("hybrid") else None,
            type_hints=[
                (item.get("typeOfEmployment") or {}).get("label", ""),
                (item.get("experienceLevel") or {}).get("label", ""),
            ],
            posted_at=iso_date(item.get("releasedDate")),
            tags=[(item.get("function") or {}).get("label", "")],
            language=language,
        )
        if job:
            if city and not job.city:
                job.city = city
            cached = item.get("_cached") or {}
            if not job.snippet and cached:
                job.snippet = cached.get("snippet") or ""
                job.skills = cached.get("skills") or job.skills
            jobs.append(job)
    return jobs
