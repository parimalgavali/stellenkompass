"""d.vinci job publications: https://{host}/jobPublication/list.json

The public JSON feed that d.vinci job widgets load (e.g. on kit.edu). `board` is the d.vinci
host. Apprenticeships and dual-study places are left out, as in the BA source.

An opening can be published in several languages (one publication id each). We keep one role per
opening, the English ad if there is one; the other ads add their text and become aliases.
"""

from __future__ import annotations

from ..http import Fetcher
from ..models import Job
from ..text import html_to_text, iso_date
from ._common import build_job, records

TEXT_FIELDS = ("introduction", "tasks", "profile", "weOffer")


def fetch(fetcher: Fetcher, board: str) -> list[dict]:
    return fetcher.get_json(f"https://{board}/jobPublication/list.json")


def _names(entries: list[dict] | None, key: str = "name") -> list[str]:
    return [e.get(key) or "" for e in entries or [] if isinstance(e, dict)]


def _by_opening(raw: list[dict]) -> list[list[dict]]:
    groups: dict[str, list[dict]] = {}
    for item in records(raw, None, "id"):
        key = str((item.get("jobOpening") or {}).get("id") or f"publication-{item['id']}")
        groups.setdefault(key, []).append(item)
    return [sorted(g, key=lambda i: i.get("language") != "en") for g in groups.values()]


def parse(raw: list[dict], board: str, company: str | None = None) -> list[Job]:
    jobs = []
    for group in _by_opening(raw):
        item = group[0]
        opening = item.get("jobOpening") or {}
        targets = _names(opening.get("targetGroups"), "internalName")
        if any(t.startswith("AUSBILDUNG") for t in targets):
            continue
        places = [p for p in opening.get("locations") or [] if isinstance(p, dict)]
        unit = (opening.get("company") or {}).get("name") or ""
        job = build_job(
            source="dvinci",
            board=board,
            job_id=str(item["id"]),
            title=item.get("position") or "",
            company=company or unit or board,
            locations=[(p.get("address") or {}).get("city") or p.get("name") or "" for p in places]
            or [opening.get("location") or ""],
            country_codes=[(p.get("country") or {}).get("isoA2") or "" for p in places],
            url=item.get("jobPublicationURL") or "",
            description=html_to_text(" ".join(i.get(k) or "" for i in group for k in TEXT_FIELDS)),
            type_hints=_names(opening.get("workingTimes")),
            posted_at=iso_date(item.get("startDate")),
            deadline=item.get("endDate") or "",
            tags=[unit, *_names(opening.get("categories"))],
            language=item.get("language"),
        )
        if job:
            if not job.city and places:
                job.city = (places[0].get("address") or {}).get("city") or ""
            job.aliases = [f"dvinci:{board}-{i['id']}" for i in group[1:]]
            jobs.append(job)
    return jobs
