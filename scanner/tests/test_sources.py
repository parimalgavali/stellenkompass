from stellenkompass_scanner.sources import (
    arbeitnow,
    ashby,
    greenhouse,
    lever,
    personio,
    smartrecruiters,
)


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
