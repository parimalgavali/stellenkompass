"""Ashby public job posting API: https://developers.ashbyhq.com/docs/public-job-posting-api"""

from __future__ import annotations

from ..http import Fetcher
from ..models import Job
from ..text import iso_date
from ._common import build_job, records


def fetch(fetcher: Fetcher, board: str) -> dict:
    return fetcher.get_json(f"https://api.ashbyhq.com/posting-api/job-board/{board}")


def _country(entry: dict) -> str:
    """Primary locations nest the country in postalAddress; secondary ones may not."""
    address = entry.get("address") or {}
    return (address.get("postalAddress") or address).get("addressCountry") or ""


def _workplace(item: dict) -> str | None:
    kind = (item.get("workplaceType") or "").lower()
    if kind in ("onsite", "hybrid", "remote"):
        return kind
    return "remote" if item.get("isRemote") else None


def parse(raw: dict, board: str, company: str | None = None) -> list[Job]:
    jobs = []
    for item in records(raw, "jobs", "id"):
        if item.get("isListed") is False:
            continue
        secondary = item.get("secondaryLocations") or []
        locations = [item.get("location", "")] + [s.get("location", "") for s in secondary]
        countries = [_country(item)] + [_country(s) for s in secondary]
        workplace = _workplace(item)
        if workplace == "remote":
            locations.append("Remote")
        job = build_job(
            source="ashby",
            board=board,
            job_id=str(item["id"]),
            title=item.get("title", ""),
            company=company or board,
            locations=locations,
            url=item.get("jobUrl", ""),
            description=item.get("descriptionPlain", ""),
            country_codes=countries,
            workplace=workplace,
            type_hints=[item.get("employmentType", "")],
            posted_at=iso_date(item.get("publishedAt")),
            tags=[item.get("department", ""), item.get("workplaceType", "")],
        )
        if job:
            jobs.append(job)
    return jobs
