"""Lever public postings API: https://github.com/lever/postings-api"""

from __future__ import annotations

from ..http import Fetcher
from ..models import Job
from ..text import iso_date
from ._common import build_job


def fetch(fetcher: Fetcher, board: str) -> list[dict]:
    return fetcher.get_json(f"https://api.lever.co/v0/postings/{board}", params={"mode": "json"})


def parse(raw: list[dict], board: str, company: str | None = None) -> list[Job]:
    jobs = []
    for item in raw:
        cats = item.get("categories") or {}
        locations = [cats.get("location", "")] + list(cats.get("allLocations") or [])
        remote = (item.get("workplaceType") or "").lower() == "remote"
        if remote:
            locations.append("Remote")
        job = build_job(
            source="lever",
            board=board,
            job_id=str(item["id"]),
            title=item.get("text", ""),
            company=company or board,
            locations=locations,
            url=item.get("hostedUrl", ""),
            description=item.get("descriptionPlain") or item.get("openingPlain") or "",
            country_codes=[item.get("country", "")],
            remote=remote,
            type_hints=[cats.get("commitment", "")],
            posted_at=iso_date(item.get("createdAt")),
            tags=[cats.get("team", ""), cats.get("department", "")],
        )
        if job:
            jobs.append(job)
    return jobs
