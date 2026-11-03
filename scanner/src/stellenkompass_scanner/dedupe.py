from __future__ import annotations

import re

from .models import Job

# Company boards are the original posting; aggregators repost them.
_SOURCE_RANK = {
    "greenhouse": 0,
    "ashby": 0,
    "lever": 0,
    "personio": 0,
    "smartrecruiters": 0,
    "arbeitnow": 1,
    "bundesagentur": 1,
}
_LEGAL = re.compile(r"\b(gmbh|ag|se|kg|inc|ltd|llc|group|co|& co)\b\.?")
_GENDER = re.compile(r"\((?:[mwfdx]\s*/\s*){1,3}[mwfdx]\)|\b[mwfdx]/[mwfdx]/[mwfdx]\b")


def _norm(text: str) -> str:
    text = _GENDER.sub(" ", text.lower())
    text = _LEGAL.sub(" ", text)
    return re.sub(r"[^a-z0-9äöüß]+", " ", text).strip()


def key(job: Job) -> tuple[str, str, str]:
    return (_norm(job.company), _norm(job.title), job.city or _norm(job.location))


def dedupe(jobs: list[Job]) -> list[Job]:
    """Keep one job per (company, title, city), preferring the company's own board."""
    best: dict[tuple[str, str, str], Job] = {}
    for job in jobs:
        k = key(job)
        current = best.get(k)
        if current is None or _SOURCE_RANK.get(job.source, 9) < _SOURCE_RANK.get(current.source, 9):
            best[k] = job
    return list(best.values())
