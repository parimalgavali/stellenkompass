"""Personio public XML job feed: https://{company}.jobs.personio.de/xml (or jobs.personio.com).

With `languages`, one feed per language is fetched and merged by position id: the first
language gives the title, all languages add description text.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from ..http import Fetcher
from ..models import Job
from ..text import html_to_text, iso_date
from ._common import build_job

DOMAINS = ("jobs.personio.de", "jobs.personio.com")


def fetch(
    fetcher: Fetcher, board: str, domain: str = DOMAINS[0], languages: list[str] | None = None
) -> dict:
    if domain not in DOMAINS:
        raise ValueError(f"unknown Personio domain {domain!r}")
    url = f"https://{board}.{domain}/xml"
    feeds = [fetcher.get_text(url, params={"language": lang}) for lang in languages or []]
    return {"domain": domain, "feeds": feeds or [fetcher.get_text(url)]}


def _text(node: ET.Element, tag: str) -> str:
    found = node.find(tag)
    return (found.text or "").strip() if found is not None and found.text else ""


def _descriptions(pos: ET.Element) -> str:
    return " ".join(
        html_to_text(_text(d, "value")) for d in pos.findall("jobDescriptions/jobDescription")
    )


def parse(raw: dict | str, board: str, company: str | None = None) -> list[Job]:
    if isinstance(raw, str):
        raw = {"domain": DOMAINS[0], "feeds": [raw]}
    roots = [ET.fromstring(feed.encode()) for feed in raw["feeds"]]
    extra: dict[str, list[str]] = {}
    for root in roots[1:]:
        for pos in root.iter("position"):
            extra.setdefault(_text(pos, "id"), []).append(_descriptions(pos))
    jobs = []
    for pos in roots[0].iter("position"):
        job_id = _text(pos, "id")
        offices = [_text(pos, "office")] + [
            (o.text or "").strip() for o in pos.findall("additionalOffices/office")
        ]
        description = " ".join([_descriptions(pos), *extra.get(job_id, [])])
        job = build_job(
            source="personio",
            board=board,
            job_id=job_id,
            title=_text(pos, "name"),
            company=company or _text(pos, "subcompany") or board,
            locations=offices,
            url=f"https://{board}.{raw['domain']}/job/{job_id}",
            description=description,
            type_hints=[_text(pos, "employmentType"), _text(pos, "schedule")],
            posted_at=iso_date(_text(pos, "createdAt")),
            tags=[_text(pos, "department")] + _text(pos, "keywords").split(",")[:5],
        )
        if job:
            jobs.append(job)
    return jobs
