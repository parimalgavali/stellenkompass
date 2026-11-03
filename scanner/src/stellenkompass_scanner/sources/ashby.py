"""Ashby public job posting API: https://developers.ashbyhq.com/docs/public-job-posting-api"""

from __future__ import annotations

from ..http import Fetcher
from ..models import Job
from ..text import iso_date
from ._common import build_job


def fetch(fetcher: Fetcher, board: str) -> dict:
    return fetcher.get_json(f"https://api.ashbyhq.com/posting-api/job-board/{board}")


def _country(entry: dict) -> str:
    return ((entry.get("address") or {}).get("postalAddress") or {}).get("addressCountry") or ""


def parse(raw: dict, board: str, company: str | None = None) -> list[Job]:
    jobs = []
    for item in raw.get("jobs", []):
        if item.get("isListed") is False:
            continue
        secondary = item.get("secondaryLocations") or []
        locations = [item.get("location", "")] + [s.get("location", "") for s in secondary]
        countries = [_country(item)] + [_country(s) for s in secondary]
        if item.get("isRemote") or item.get("workplaceType") == "Remote":
            locations.append("Remote")
        job = build_job(
            source="ashby",
            source_id=f"{board}-{item['id']}",
            title=item.get("title", ""),
            company=company or board,
            locations=locations,
            url=item.get("jobUrl", ""),
            description=item.get("descriptionPlain", ""),
            country_codes=countries,
            remote=bool(item.get("isRemote")) or item.get("workplaceType") == "Remote",
            type_hints=[item.get("employmentType", "")],
            posted_at=iso_date(item.get("publishedAt")),
            tags=[item.get("department", ""), item.get("workplaceType", "")],
        )
        if job:
            jobs.append(job)
    return jobs
