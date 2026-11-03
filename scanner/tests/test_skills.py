import pytest

from stellenkompass_scanner.skills import _SKILLS, WEB_SKILLS, extract_skills, skills_json


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Senior Python Developer (FastAPI, PostgreSQL, Docker)", ["Python", "SQL", "FastAPI",
                                                                    "PostgreSQL", "Docker"]),
        ("Frontend Engineer – React, TypeScript", ["TypeScript", "React"]),
        ("React Native Developer", ["React Native"]),
        ("Java Backend Engineer, Spring Boot, Kafka", ["Java", "Spring", "Kafka"]),
        ("JavaScript Developer", ["JavaScript"]),
        ("Backend Engineer (Go, Kubernetes)", ["Go", "Kubernetes"]),
        ("Go-to-market Manager. Go beyond!", []),
        ("Data Scientist with Python and R", ["Python", "R", "Data Science"]),
        ("R&D Engineer", []),
        ("Werkstudent Maschinelles Lernen und Statistik", ["Machine Learning", "Statistics"]),
        ("Build LLM agents with RAG on AWS", ["LLM", "AWS"]),
        ("Restaurant manager, rest of the team", []),
        ("Design REST APIs", ["REST APIs"]),
        ("Build RESTful services", ["REST APIs"]),
    ],
)  # fmt: skip
def test_extract_skills(text, expected):
    assert extract_skills(text) == expected


def test_limit():
    assert len(extract_skills("python java sql docker aws azure gcp kafka spark git jira excel seo",
                              limit=5)) == 5  # fmt: skip


def test_web_skill_list_is_in_sync():
    assert WEB_SKILLS.read_text("utf-8") == skills_json(), (
        "run `uv run python -m stellenkompass_scanner.skills`"
    )


def test_patterns_have_no_inline_flags():
    """The web app compiles these with JavaScript's RegExp; keep to the shared syntax."""
    assert not [name for name, pattern in _SKILLS if "(?i" in pattern or "(?x" in pattern]
