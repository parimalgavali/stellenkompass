"""Guess posting language and job type from text."""

from __future__ import annotations

import re

_EN = {
    "the", "and", "you", "your", "with", "for", "our", "we", "are", "will", "of", "to",
    "in", "is", "as", "team", "experience", "skills", "work", "this", "have", "who",
}  # fmt: skip
_DE = {
    "und", "der", "die", "das", "du", "dein", "deine", "wir", "mit", "für", "ist", "sind",
    "bei", "eine", "einen", "ein", "unser", "unsere", "sie", "ihre", "zu", "auf", "im", "von",
    "erfahrung", "kenntnisse", "aufgaben",
}  # fmt: skip
_WORD = re.compile(r"[a-zäöüß]+")


def detect_language(text: str) -> str:
    """'de' or 'en' by counting common words. Defaults to 'en' on a tie or empty text."""
    words = _WORD.findall((text or "").lower()[:4000])
    en = sum(w in _EN for w in words)
    de = sum(w in _DE for w in words)
    return "de" if de > en else "en"


_RULES: tuple[tuple[str, str], ...] = (
    ("working_student", r"werkstudent|working[ -]student|studentische|student assistant|"
                        r"student job|\bhiwi\b|student worker|student employee"),
    ("thesis", r"thesis|abschlussarbeit|masterarbeit|bachelorarbeit"),
    ("internship", r"\bintern\b|\binterns\b|internship|praktikum|praktikant|pflichtpraktik"),
    ("part_time", r"(?<!or-)part[ -]?time|teilzeit|minijob"),
    ("other", r"freelance|freiberuf|\bcontractor\b|selbstständig"),
)  # fmt: skip


def detect_job_type(title: str, hints: list[str] | None = None) -> str:
    """Job type from the title first, then from source hints (e.g. 'Full time', 'Intern')."""
    for text in [title, " ".join(hints or [])]:
        low = (text or "").lower()
        for job_type, pattern in _RULES:
            if re.search(pattern, low):
                return job_type
    return "full_time"
