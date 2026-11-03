"""Recruitee careers-site offers API: https://docs.recruitee.com/reference/offers"""

from __future__ import annotations

from ..http import Fetcher
from ..models import Job
from ..text import html_to_text, iso_date
from ._common import build_job, records


def fetch(fetcher: Fetcher, board: str) -> dict:
    return fetcher.get_json(f"https://{board}.recruitee.com/api/offers/")


def _workplace(item: dict) -> str | None:
    remote, hybrid, onsite = (bool(item.get(k)) for k in ("remote", "hybrid", "on_site"))
    if hybrid or (remote and onsite):
        return "hybrid"
    if remote:
        return "remote"
    return "onsite" if onsite else None


def parse(raw: dict, board: str, company: str | None = None) -> list[Job]:
    jobs = []
    for item in records(raw, "offers", "id"):
        places = item.get("locations") or [item]
        workplace = _workplace(item)
        locations = [p.get("city") or p.get("name") or p.get("location") or "" for p in places]
        if workplace == "remote":
            locations.append("Remote")
        job = build_job(
            source="recruitee",
            board=board,
            job_id=str(item["id"]),
            title=item.get("title", ""),
            company=company or item.get("company_name") or board,
            locations=locations,
            country_codes=[p.get("country_code") or p.get("country") or "" for p in places],
            workplace=workplace,
            url=item.get("careers_url", ""),
            description=html_to_text(
                (item.get("description") or "") + " " + (item.get("requirements") or "")
            ),
            type_hints=[item.get("employment_type_code") or ""],
            posted_at=iso_date((item.get("published_at") or "").replace(" UTC", "+00:00")),
            tags=[item.get("department") or ""],
        )
        if job:
            jobs.append(job)
    return jobs
