"""Personio public XML job feed: https://{company}.jobs.personio.de/xml"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from ..http import Fetcher
from ..models import Job
from ..text import html_to_text, iso_date
from ._common import build_job


def fetch(fetcher: Fetcher, board: str) -> str:
    return fetcher.get_text(f"https://{board}.jobs.personio.de/xml")


def _text(node: ET.Element, tag: str) -> str:
    found = node.find(tag)
    return (found.text or "").strip() if found is not None and found.text else ""


def parse(raw: str, board: str, company: str | None = None) -> list[Job]:
    root = ET.fromstring(raw.encode())
    jobs = []
    for pos in root.iter("position"):
        job_id = _text(pos, "id")
        offices = [_text(pos, "office")] + [
            (o.text or "").strip() for o in pos.findall("additionalOffices/office")
        ]
        description = " ".join(
            html_to_text(_text(d, "value")) for d in pos.findall("jobDescriptions/jobDescription")
        )
        job = build_job(
            source="personio",
            board=board,
            job_id=job_id,
            title=_text(pos, "name"),
            company=company or _text(pos, "subcompany") or board,
            locations=offices,
            url=f"https://{board}.jobs.personio.de/job/{job_id}",
            description=description,
            type_hints=[_text(pos, "employmentType"), _text(pos, "schedule")],
            posted_at=iso_date(_text(pos, "createdAt")),
            tags=[_text(pos, "department")] + _text(pos, "keywords").split(",")[:5],
        )
        if job:
            jobs.append(job)
    return jobs
