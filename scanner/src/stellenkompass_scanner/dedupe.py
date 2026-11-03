from __future__ import annotations

import re
from collections import defaultdict

from .models import Job

# Company boards are the original posting; aggregators repost them.
_SOURCE_RANK = {
    "greenhouse": 0,
    "ashby": 0,
    "lever": 0,
    "personio": 0,
    "smartrecruiters": 0,
    "recruitee": 0,
    "teamtailor": 0,
    "dvinci": 0,
    "workday": 0,
    "successfactors": 0,
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


def rank(source: str) -> int:
    if source not in _SOURCE_RANK:
        raise KeyError(f"add {source!r} to dedupe._SOURCE_RANK")
    return _SOURCE_RANK[source]


def dedupe(jobs: list[Job]) -> list[Job]:
    """Collapse copies of the same role across sources; keep distinct openings.

    Same id twice -> one job. Same (company, title, city) on several sources -> keep the
    best-ranked source's jobs (all of them: different ids there are different openings) and
    record the other sources' ids as aliases of the first kept job.
    """
    unique = list({job.id: job for job in jobs}.values())
    groups: dict[tuple[str, str, str], list[Job]] = defaultdict(list)
    for job in unique:
        groups[key(job)].append(job)
    kept: list[Job] = []
    for group in groups.values():
        winner = min(group, key=lambda j: rank(j.source)).source
        keep = [j for j in group if j.source == winner]
        copies = [j.id for j in group if j.source != winner]
        if copies:
            keep[0].aliases = list(dict.fromkeys([*keep[0].aliases, *copies]))
        kept.extend(keep)
    return kept
