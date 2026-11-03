from datetime import date

import pytest

from stellenkompass_scanner.classify import (
    clean_deadline,
    detect_deadline,
    detect_experience_years,
    detect_job_type,
    detect_language,
    detect_seniority,
)


@pytest.mark.parametrize(
    "title, hints, expected",
    [
        ("Werkstudentin Data Science (m/w/d)", None, "working_student"),
        ("Working Student Marketing", None, "working_student"),
        ("Master Thesis: LLM evaluation", None, "thesis"),
        ("Praktikum im Bereich Produktion", None, "internship"),
        ("Software Engineering Intern", None, "internship"),
        ("International Sales Manager", None, "full_time"),
        ("Internal Audit Lead", None, "full_time"),
        ("Backend Engineer", ["Part-time"], "part_time"),
        ("Aktuar (20h)", ["permanent", "full-or-part-time"], "full_time"),
        ("Data Engineer", ["Full time"], "full_time"),
        ("Python Developer", ["Freelance"], "other"),
        ("Data Analyst", ["Praktikum", "hilfstätigkeit / student"], "internship"),
    ],
)
def test_job_type(title, hints, expected):
    assert detect_job_type(title, hints) == expected


def test_language():
    assert detect_language("We are looking for an engineer to join our team.") == "en"
    assert detect_language("Wir suchen dich für unser Team und deine Aufgaben sind") == "de"
    assert detect_language("") == "en"


@pytest.mark.parametrize(
    ("title", "level"),
    [
        ("Senior Data Scientist (m/w/d)", "senior"),
        ("Sr. Backend Engineer", "senior"),
        ("Junior Python Developer", "junior"),
        ("Graduate Programme Software 2027", "graduate"),
        ("Trainee Data Analytics", "graduate"),
        ("Berufseinsteiger Softwareentwicklung", "graduate"),
        ("Head of Machine Learning", "lead"),
        ("Senior Tech Lead Payments", "lead"),
        ("Teamleiter IT-Infrastruktur", "lead"),
        ("Staff Engineer, Platform", "lead"),
        ("Bauleiter Tiefbau", ""),
        ("Data Engineer", ""),
        ("Lead Generation Werkstudent", ""),
    ],
)
def test_detect_seniority(title, level):
    assert detect_seniority(title) == level


@pytest.mark.parametrize(
    ("text", "years"),
    [
        ("You have 3+ years of experience with Python.", 3),
        ("2-4 years of professional experience in data engineering", 2),
        ("At least two years of hands-on experience", 2),
        ("Mindestens 3 Jahre Berufserfahrung in der Softwareentwicklung", 3),
        ("Du bringst 5 Jahre relevante Erfahrung mit", 5),
        ("Erfahrung von mindestens drei Jahren im Vertrieb", 3),
        ("5+ years of experience in ML. 2 years of experience leading teams.", 2),
        ("With over 50 years of experience in the industry, we build pumps.", None),
        ("Erste Erfahrung mit SQL", None),
        ("We offer 30 days of holiday per year.", None),
        ("", None),
    ],
)
def test_detect_experience_years(text, years):
    assert detect_experience_years(text) == years


TODAY = date(2026, 11, 3)


@pytest.mark.parametrize(
    ("text", "deadline"),
    [
        ("Bewerbungsfrist: 30.11.2026. Wir freuen uns!", "2026-11-30"),
        ("Application Deadline: December 16, 2026", "2026-12-16"),
        ("Application Deadline: January, 17 2027", "2027-01-17"),
        ("Bitte bewerben Sie sich bis zum 15. Januar 2027 online.", "2027-01-15"),
        ("Closing date: 2026-11-20", "2026-11-20"),
        ("Bewerbungsschluss 1.12.26", "2026-12-01"),
        ("Bewerbungsfrist: 30.09.2026", ""),  # past
        ("Application deadline: none, we hire on a rolling basis.", ""),
        ("Start date: 01.01.2027", ""),  # no cue
        ("Apply by submitting your CV", ""),
    ],
)
def test_detect_deadline(text, deadline):
    assert detect_deadline(text, today=TODAY) == deadline


def test_clean_deadline():
    assert clean_deadline("2026-11-30T22:59:59.999Z", today=TODAY) == "2026-11-30"
    assert clean_deadline("2099-12-31T00:00:00Z", today=TODAY) == ""
    assert clean_deadline("", today=TODAY) == ""
