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


_SENIORITY: tuple[tuple[str, str], ...] = (
    ("lead", r"\blead\b(?! generation| management)|\bhead of\b|\bprincipal\b|\bdirector\b|"
             r"\bstaff (?:engineer|scientist|software|data|machine)|"
             r"\b(?:team|gruppen|abteilungs|bereichs)?leit(?:er|erin|ung)\b"),
    ("senior", r"\bsenior\b|\bsr\.?\s"),
    ("junior", r"\bjunior\b|\bjr\.?\s"),
    ("graduate", r"graduate|trainee|entry[ -]level|berufseinsteiger|absolvent|young professional|"
                 r"new grad|direkteinstieg"),
)  # fmt: skip


def detect_seniority(title: str) -> str:
    """'lead', 'senior', 'junior', 'graduate' from the title; '' when it doesn't say."""
    low = (title or "").lower()
    return next((level for level, pattern in _SENIORITY if re.search(pattern, low)), "")


_NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
    "ein": 1, "eine": 1, "einem": 1, "zwei": 2, "drei": 3, "vier": 4, "fünf": 5, "sechs": 6,
}  # fmt: skip
_N = r"(\d{1,2}|" + "|".join(_NUMBER_WORDS) + r")"
_SPAN = r"\s*\+?\s*(?:(?:-|–|bis|to)\s*\d{1,2}\s*)?\+?\s*"
_YEARS = (
    re.compile(_N + _SPAN + r"(?:years?|yrs|jahre?n?)\b[^.;:\n]{0,50}?(?:experience|erfahrung)"),
    re.compile(
        r"(?:experience|erfahrung)[^.;:\n]{0,40}?\b" + _N + _SPAN + r"(?:years?|yrs|jahre?n?)\b"
    ),
)
MAX_YEARS = 15  # beyond this it's usually the company's age ("50 years of experience")


def detect_experience_years(text: str) -> int | None:
    """Smallest number of years of experience the ad asks for, or None when it doesn't say."""
    low = (text or "").lower()
    found = []
    for pattern in _YEARS:
        for m in pattern.finditer(low):
            g = m.group(1)
            n = int(g) if g.isdigit() else _NUMBER_WORDS[g]
            if 1 <= n <= MAX_YEARS:
                found.append(n)
    return min(found) if found else None
