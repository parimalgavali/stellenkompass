from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields

JOB_TYPES = ("full_time", "part_time", "working_student", "internship", "thesis", "other")


@dataclass
class Job:
    id: str
    title: str
    company: str
    location: str
    url: str
    source: str
    city: str = ""
    remote: bool = False  # fully remote only
    workplace_type: str = "unknown"  # onsite / hybrid / remote / unknown
    job_type: str = "full_time"
    experience_years: int | None = None  # smallest number of years the ad asks for
    seniority: str = ""  # lead / senior / junior / graduate / "" (title doesn't say)
    language: str = "en"
    posted_at: str = ""
    deadline: str = ""  # YYYY-MM-DD, last day to apply; "" when unknown
    first_seen: str = ""
    tags: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    snippet: str = ""
    source_board: str = ""  # empty for aggregators
    source_job_id: str = ""
    # Ids this role had before, or copies of it on other sources; keeps tracker links alive.
    aliases: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Job:
        names = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in names})
