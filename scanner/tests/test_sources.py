import pytest

from stellenkompass_scanner.sources import (
    arbeitnow,
    ashby,
    bundesagentur,
    greenhouse,
    lever,
    personio,
    smartrecruiters,
)
from stellenkompass_scanner.sources._common import Capped, records


def test_greenhouse_keeps_only_germany(fixture):
    jobs = greenhouse.parse(fixture("greenhouse_n26.json"), "n26", company="N26")
    assert [j.city for j in jobs] == ["Berlin", "Berlin"]
    job = jobs[0]
    assert job.id.startswith("greenhouse:n26-")
    assert job.company == "N26"
    assert job.url.startswith("https://")
    assert job.posted_at.endswith("Z")
    assert job.snippet and "<" not in job.snippet
    assert job.language == "en"


def test_ashby_uses_address_country(fixture):
    jobs = ashby.parse(fixture("ashby_parloa.json"), "parloa", company="Parloa")
    assert len(jobs) == 1
    assert jobs[0].city == "Berlin"
    assert jobs[0].remote is True
    assert jobs[0].url.startswith("https://jobs.ashbyhq.com/parloa/")


def test_smartrecruiters_drops_foreign_sites_tagged_de(fixture):
    jobs = smartrecruiters.parse(fixture("smartrecruiters_bosch.json"), "BoschGroup", "Bosch")
    cities = {j.city for j in jobs}
    assert "Shanghai" not in cities
    assert "Stuttgart" in cities
    assert all(j.job_type == "internship" for j in jobs)
    assert all(j.language == "de" for j in jobs)
    assert jobs[0].url.startswith("https://jobs.smartrecruiters.com/BoschGroup/")


def test_lever_country_code(fixture):
    jobs = lever.parse(fixture("lever_pigment.json"), "pigment", company="Pigment")
    assert [j.city for j in jobs] == ["Frankfurt"]
    assert jobs[0].posted_at.startswith("20")


def test_personio_xml(fixture):
    jobs = personio.parse(fixture("personio_ottonova.xml"), "ottonova", company="ottonova")
    assert len(jobs) == 2
    assert jobs[0].city == "Munich"
    assert "Köln" in jobs[0].location
    assert jobs[0].language == "de"
    assert jobs[0].url == f"https://ottonova.jobs.personio.de/job/{jobs[0].id.split('-')[-1]}"


def test_arbeitnow(fixture):
    jobs = arbeitnow.parse(fixture("arbeitnow.json")["data"])
    titles = [j.title for j in jobs]
    assert "Revenue Operations Manager" not in titles  # Paris
    assert any(j.job_type == "internship" for j in jobs)
    assert all(j.source == "arbeitnow" for j in jobs)


def test_arbeitnow_fetch_stops_at_last_page():
    class Pages:
        def __init__(self):
            self.calls = 0

        def get_json(self, url, params=None):
            self.calls += 1
            nxt = "x" if params["page"] < 2 else None
            return {"data": [{"slug": str(params["page"])}], "links": {"next": nxt}}

    pages = Pages()
    assert len(arbeitnow.fetch(pages, max_pages=10)) == 2
    assert pages.calls == 2


def test_bundesagentur_keeps_jobs_in_germany(fixture):
    jobs = bundesagentur.parse(fixture("bundesagentur.json")["ergebnisliste"])
    # Of 6 items: one apprenticeship and one role in Vienna are dropped.
    assert len(jobs) == 4
    assert all(j.source == "bundesagentur" and j.language == "de" for j in jobs)
    assert all(j.url.startswith("https://www.arbeitsagentur.de/jobsuche/jobdetail/") for j in jobs)
    assert not any("Wien" in j.location for j in jobs)
    first = jobs[0]
    assert first.id == "bundesagentur:14225-3170264583da19a7-S"
    assert first.job_type == "working_student"
    assert first.remote is True
    assert first.posted_at.endswith("T00:00:00Z")


class _BaPages:
    """Two full pages for every query, then an empty one."""

    def __init__(self):
        self.calls = []

    def get_json(self, url, params=None, headers=None):
        self.calls.append((params["was"], params["page"], headers))
        if params["page"] > 2:
            return {"ergebnisliste": [], "maxErgebnisse": 250}
        start = (params["page"] - 1) * 100
        rows = [{"referenznummer": f"ref-{i}"} for i in range(start, start + 100)]
        return {"ergebnisliste": rows, "maxErgebnisse": 250}


def test_bundesagentur_fetch_caps_pages_and_dedupes_queries():
    fetcher = _BaPages()
    with pytest.raises(Capped) as cap:
        bundesagentur.fetch(fetcher, {"queries": ["A", "B"], "max_per_query": 150})
    items = cap.value.raw
    assert cap.value.carry is False
    assert [(q, p) for q, p, _ in fetcher.calls] == [("A", 1), ("A", 2), ("B", 1), ("B", 2)]
    assert all(h == bundesagentur.HEADERS for _, _, h in fetcher.calls)
    assert len(items) == 200


def test_records_rejects_wrong_shape_and_skips_bad_records():
    with pytest.raises(ValueError):
        records({"error": "maintenance"}, "jobs", "id")
    assert records({"jobs": [{"id": 1}, "x", {"title": "no id"}]}, "jobs", "id") == [{"id": 1}]
