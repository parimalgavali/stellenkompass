"""Lever public postings API: https://github.com/lever/postings-api"""

from __future__ import annotations

from ..http import Fetcher
from ..models import Job
from ..text import iso_date
from ._common import Capped, build_job, records

HOSTS = {"global": "api.lever.co", "eu": "api.eu.lever.co"}
PAGE = 100


def fetch(fetcher: Fetcher, board: str, region: str = "global", max_pages: int = 20) -> list[dict]:
    """`region: eu` in companies.yaml for boards hosted on jobs.eu.lever.co."""
    url = f"https://{HOSTS[region]}/v0/postings/{board}"
    postings: list[dict] = []
    for page in range(max_pages):
        batch = fetcher.get_json(url, params={"mode": "json", "skip": page * PAGE, "limit": PAGE})
        postings.extend(records(batch, None, "id"))
        if len(batch) < PAGE:
            return postings
    raise Capped(postings)


def parse(raw: list[dict], board: str, company: str | None = None) -> list[Job]:
    jobs = []
    for item in records(raw, None, "id"):
        cats = item.get("categories") or {}
        locations = [cats.get("location", "")] + list(cats.get("allLocations") or [])
        workplace = (item.get("workplaceType") or "").lower()
        if workplace == "remote":
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
            workplace=workplace,
            type_hints=[cats.get("commitment", "")],
            posted_at=iso_date(item.get("createdAt")),
            tags=[cats.get("team", ""), cats.get("department", "")],
        )
        if job:
            jobs.append(job)
    return jobs
