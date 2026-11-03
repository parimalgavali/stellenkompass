"""SAP SuccessFactors Recruiting Marketing career sites (jobs.<company>.com), via the
HTML fragment their search page loads: GET https://{board}/tile-search-results/?startrow=N

robots.txt on these sites disallows /services/ (the newer JSON search), not this route.
Sites differ: with `country: DE` set for a board we ask for its Germany facet
(`optionsFacetsDD_country`) and treat every role as DE; set it only where the facet works,
since some sites ignore it. Otherwise the country comes from location fields like
"Ulm, DE, 89077". Tiles show the city only when the site configures it; otherwise it is
read from the job URL `/job/{City}-{Title}-{PLZ}/{id}/`. Paging stops when a page adds no
new roles (some sites ignore `startrow`).
Apprenticeships and dual-study places are left out, as in the BA source.
"""

from __future__ import annotations

import html
import re
from datetime import datetime
from urllib.parse import unquote

from ..http import Fetcher
from ..models import Job
from ._common import Capped, build_job

MAX_PAGES = 80
_TILE = re.compile(r'<li class="job-tile job-id-(\d+)\b([\s\S]*?)</li>')
_URL = re.compile(r'data-url="([^"]+)"')
_TITLE = re.compile(r'class="jobTitle-link[^"]*"[^>]*>([\s\S]*?)</a>')
_FIELD = re.compile(r'id="job-\d+-desktop-section-([a-z]+)-value"[^>]*>\s*([^<]*?)\s*<')
_TRAINING = re.compile(r"\b(Ausbildung|Duales Studium|Dualer Student|Azubi)", re.I)


def fetch(fetcher: Fetcher, board: str, country: str = "") -> dict:
    params = {"q": "", "optionsFacetsDD_country": country} if country else {"q": ""}
    raw: dict = {"country": country, "pages": []}
    seen: set[str] = set()
    start = 0
    for _ in range(MAX_PAGES):
        page = fetcher.get_text(
            f"https://{board}/tile-search-results/", params={**params, "startrow": start}
        )
        ids = [i for i, _ in _TILE.findall(page)]
        if not set(ids) - seen:
            return raw
        seen.update(ids)
        raw["pages"].append(page)
        start += len(ids)
    raise Capped(raw)


def _word(text: str) -> str:
    return re.sub(r"\W", "", text).lower()


def _city_from_url(path: str, title: str) -> str:
    m = re.search(r"/job/([^/]+)/", unquote(path))
    words = m.group(1).split("-") if m else []
    first = _word(title.split()[0]) if title.split() else ""
    for i, word in enumerate(words):
        if i and _word(word) == first:
            return " ".join(words[:i])
    return ""


def _date(value: str) -> str:
    for fmt in ("%b %d, %Y", "%d.%m.%Y", "%d %b %Y"):
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%dT00:00:00Z")
        except ValueError:
            continue
    return ""


def _place(text: str) -> tuple[str, str]:
    m = re.match(r"(.*?),\s*([A-Z]{2})(?:,\s*[\w-]+)?$", text)
    return (m.group(1), m.group(2)) if m else (text, "")


def parse(raw: dict, board: str, company: str | None = None) -> list[Job]:
    jobs: list[Job] = []
    seen: set[str] = set()
    for page in raw["pages"]:
        for job_id, block in _TILE.findall(page):
            url, title = _URL.search(block), _TITLE.search(block)
            if job_id in seen or not url or not title:
                continue
            seen.add(job_id)
            name = html.unescape(re.sub(r"\s+", " ", title.group(1))).strip()
            if _TRAINING.search(name):
                continue
            path = html.unescape(html.unescape(url.group(1)))
            fields = {k: html.unescape(v) for k, v in _FIELD.findall(block)}
            place = fields.get("city") or fields.get("location") or fields.get("multilocation")
            places = [_place(p.strip()) for p in (place or "").split(";") if p.strip()] or [
                (_city_from_url(path, name), "")
            ]
            codes = [raw["country"] or code for _, code in places]
            job = build_job(
                source="successfactors",
                board=board,
                job_id=job_id,
                title=name,
                company=company or board,
                locations=[loc for loc, _ in places],
                country_codes=codes if all(codes) else None,
                url=f"https://{board}{path}",
                posted_at=_date(fields.get("date", "")),
            )
            if job:
                jobs.append(job)
    return jobs
