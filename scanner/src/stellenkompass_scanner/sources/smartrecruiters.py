"""SmartRecruiters public postings API: https://developers.smartrecruiters.com/docs/posting-api"""

from __future__ import annotations

from ..geo import STATE_CODES, STATES, city_of
from ..http import Fetcher
from ..models import Job
from ..text import iso_date
from ._common import Capped, build_job, records

PAGE = 100


def fetch(fetcher: Fetcher, board: str, max_pages: int = 20) -> dict:
    url = f"https://api.smartrecruiters.com/v1/companies/{board}/postings"
    content: list[dict] = []
    for page in range(max_pages):
        body = fetcher.get_json(url, params={"limit": PAGE, "offset": page * PAGE, "country": "de"})
        batch = records(body, "content", "id")
        content.extend(batch)
        if len(batch) < PAGE or len(content) >= body.get("totalFound", 0):
            return {"content": content}
    raise Capped({"content": content})


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
        if (loc.get("country") or "").lower() != "de" or not _german_region(loc):
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
            country_codes=["de"],
            remote=bool(loc.get("remote")),
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
            jobs.append(job)
    return jobs
