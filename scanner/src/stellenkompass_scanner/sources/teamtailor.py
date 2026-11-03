"""Teamtailor careers-site RSS feed:
https://support.teamtailor.com/en/articles/11171756-rss-feed-how-to-guide

`board` is the careers host: a bare name means `{name}.teamtailor.com`, anything with a dot
(e.g. `careers.example.de`) is used as is.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import UTC
from email.utils import parsedate_to_datetime

from ..http import Fetcher
from ..models import Job
from ..text import html_to_text
from ._common import Capped, build_job

PER_PAGE = 100
MAX_PAGES = 20
TT = "{https://teamtailor.com/locations}"
WORKPLACE = {"fully": "remote", "hybrid": "hybrid", "none": "onsite"}


def _host(board: str) -> str:
    return board if "." in board else f"{board}.teamtailor.com"


def _items(page: str) -> list[ET.Element]:
    return ET.fromstring(page.encode()).findall("channel/item")


def fetch(fetcher: Fetcher, board: str) -> list[str]:
    pages: list[str] = []
    for n in range(MAX_PAGES):
        page = fetcher.get_text(
            f"https://{_host(board)}/jobs.rss",
            params={"per_page": PER_PAGE, "offset": n * PER_PAGE},
        )
        pages.append(page)
        if len(_items(page)) < PER_PAGE:
            return pages
    raise Capped(pages)


def _date(value: str) -> str:
    try:
        return parsedate_to_datetime(value).astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    except (TypeError, ValueError):
        return ""


def parse(raw: list[str], board: str, company: str | None = None) -> list[Job]:
    jobs = []
    for page in raw:
        for item in _items(page):
            guid = (item.findtext("guid") or "").strip()
            if not guid:
                continue
            places = list(item.iter(f"{TT}location"))
            workplace = WORKPLACE.get((item.findtext("remoteStatus") or "").strip())
            locations = [p.findtext(f"{TT}city") or p.findtext(f"{TT}name") or "" for p in places]
            if workplace == "remote":
                locations.append("Remote")
            job = build_job(
                source="teamtailor",
                board=board,
                job_id=guid,
                title=(item.findtext("title") or "").strip(),
                company=company or board,
                locations=locations,
                country_codes=[(p.findtext(f"{TT}country") or "").strip() for p in places],
                workplace=workplace,
                url=(item.findtext("link") or "").strip(),
                description=html_to_text(item.findtext("description") or ""),
                posted_at=_date(item.findtext("pubDate") or ""),
                tags=[item.findtext(f"{TT}department") or ""],
            )
            if job:
                jobs.append(job)
    return jobs
