"""softgarden career widgets: GET https://{board}.softgarden.io/de/widgets/jobs

The page the company's own careers site embeds; it lists every open role on one page.
robots.txt disallows the apply, API and HR paths, not the widgets. There is no country
field, so Germany is decided by the city text. Apprenticeships are left out (D9).
"""

from __future__ import annotations

import html
import re
from datetime import datetime

from ..http import Fetcher
from ..models import Job
from ._common import build_job

_BLOCK = '<div class="matchElement" id="job_id_'
_LINK = re.compile(r'<a href="(?:\.\./)*(job/[^"?]+)[^"]*"[^>]*>([\s\S]*?)</a>')
_DATE = re.compile(r'class="matchValue date">\s*([\d.]+)\s*<')
_AUDIENCE = re.compile(r'class="matchValue audience">([\s\S]*?)</div>')
_CITY = re.compile(r'class="location-view-item">\s*([^<]+?)\s*<')
_TRAINING = re.compile(r"\b(Ausbildung|Auszubildende|Duales Studium|Azubi|Schüler)", re.I)


def fetch(fetcher: Fetcher, board: str) -> str:
    return fetcher.get_text(f"https://{board}.softgarden.io/de/widgets/jobs")


def _date(value: str) -> str:
    try:
        return datetime.strptime(value, "%d.%m.%y").strftime("%Y-%m-%dT00:00:00Z")
    except ValueError:
        return ""


def _text(value: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>|\s+", " ", value)).strip()


def parse(raw: str, board: str, company: str | None = None) -> list[Job]:
    jobs: list[Job] = []
    seen: set[str] = set()
    for block in raw.split(_BLOCK)[1:]:
        job_id = block.split('"', 1)[0]
        link = _LINK.search(block)
        if job_id in seen or not link:
            continue
        seen.add(job_id)
        title = _text(link.group(2))
        audience = _AUDIENCE.search(block)
        if _TRAINING.search(title) or (audience and _TRAINING.search(audience.group(1))):
            continue
        date = _DATE.search(block)
        job = build_job(
            source="softgarden",
            board=board,
            job_id=job_id,
            title=title,
            company=company or board,
            locations=[html.unescape(c) for c in _CITY.findall(block)] or [""],
            url=f"https://{board}.softgarden.io/{html.unescape(link.group(1))}",
            posted_at=_date(date.group(1)) if date else "",
        )
        if job:
            jobs.append(job)
    return jobs
