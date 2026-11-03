from __future__ import annotations

from ..classify import detect_job_type, detect_language
from ..geo import city_of, in_germany, is_remote
from ..models import Job
from ..skills import extract_skills
from ..text import snippet


def build_job(
    *,
    source: str,
    job_id: str,
    board: str = "",
    title: str,
    company: str,
    locations: list[str],
    url: str,
    description: str = "",
    country_codes: list[str] | None = None,
    remote: bool | None = None,
    type_hints: list[str] | None = None,
    posted_at: str = "",
    tags: list[str] | None = None,
    language: str | None = None,
) -> Job | None:
    """Common job, or None when the role is not in Germany (or remote open to Germany).

    Company boards pass `board`; ids are `source:board-job_id`, aggregators `source:job_id`.
    """
    locations = [x.strip() for x in locations if x and x.strip()]
    if not in_germany(locations, country_codes):
        return None
    location_text = " · ".join(dict.fromkeys(locations))
    lang = language if language in ("en", "de") else detect_language(f"{title} {description}")
    return Job(
        id=f"{source}:{board}-{job_id}" if board else f"{source}:{job_id}",
        title=title.strip(),
        company=company.strip(),
        location=location_text,
        city=city_of(*locations),
        remote=bool(remote) if remote is not None else is_remote(location_text),
        job_type=detect_job_type(title, type_hints),
        language=lang,
        url=url,
        source=source,
        source_board=board,
        source_job_id=str(job_id),
        posted_at=posted_at,
        tags=[t.strip() for t in (tags or []) if t and t.strip()][:8],
        skills=extract_skills(f"{title}\n{description}"),
        snippet=snippet(description),
    )
