import pytest

from stellenkompass_scanner.classify import detect_job_type, detect_language, detect_seniority


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
