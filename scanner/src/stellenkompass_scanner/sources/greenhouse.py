"""Greenhouse job board API: https://developers.greenhouse.io/job-board.html"""

from __future__ import annotations

from ..http import Fetcher
from ..models import Job
from ..text import html_to_text, iso_date
from ._common import build_job, records


def fetch(fetcher: Fetcher, board: str) -> dict:
    return fetcher.get_json(
        f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs", params={"content": "true"}
    )


def parse(raw: dict, board: str, company: str | None = None) -> list[Job]:
    jobs = []
    for item in records(raw, "jobs", "id"):
        locations = [(item.get("location") or {}).get("name", "")]
        locations += [o.get("location") or o.get("name") or "" for o in item.get("offices") or []]
        hints = [str(m.get("value") or "") for m in item.get("metadata") or []]
        job = build_job(
            source="greenhouse",
            board=board,
            job_id=str(item["id"]),
            title=item.get("title", ""),
            company=company or item.get("company_name") or board,
            locations=locations,
            url=item.get("absolute_url", ""),
            description=html_to_text(item.get("content")),
            type_hints=hints,
            posted_at=iso_date(item.get("first_published") or item.get("updated_at")),
            tags=[d.get("name", "") for d in item.get("departments") or []],
        )
        if job:
            jobs.append(job)
    return jobs
