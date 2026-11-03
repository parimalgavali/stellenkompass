"""Arbeitnow free public job API: https://www.arbeitnow.com/api/job-board-api"""

from __future__ import annotations

from ..http import Fetcher
from ..models import Job
from ..text import html_to_text, iso_date
from ._common import Capped, build_job, records

URL = "https://www.arbeitnow.com/api/job-board-api"


def fetch(fetcher: Fetcher, options: dict | None = None, max_pages: int = 30) -> list[dict]:
    items: list[dict] = []
    for page in range(1, max_pages + 1):
        body = fetcher.get_json(URL, params={"page": page})
        data = records(body, "data", "slug")
        items.extend(data)
        if not data or not (body.get("links") or {}).get("next"):
            return items
    raise Capped(items)


def parse(items: list[dict]) -> list[Job]:
    jobs = []
    for item in items:
        job = build_job(
            source="arbeitnow",
            job_id=item["slug"],
            title=item.get("title", ""),
            company=item.get("company_name", ""),
            locations=[item.get("location", "")] + (["Remote"] if item.get("remote") else []),
            url=item.get("url", ""),
            description=html_to_text(item.get("description")),
            remote=bool(item.get("remote")),
            type_hints=item.get("job_types") or [],
            posted_at=iso_date(item.get("created_at")),
            tags=item.get("tags") or [],
        )
        if job:
            jobs.append(job)
    return jobs
