import json

import pytest

from stellenkompass_scanner.sources import (
    arbeitnow,
    ashby,
    bundesagentur,
    dvinci,
    greenhouse,
    join,
    lever,
    personio,
    recruitee,
    smartrecruiters,
    softgarden,
    successfactors,
    teamtailor,
    workday,
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
    # isRemote is true, but workplaceType says Hybrid: not fully remote.
    assert jobs[0].workplace_type == "hybrid" and jobs[0].remote is False
    assert jobs[0].url.startswith("https://jobs.ashbyhq.com/parloa/")


def test_smartrecruiters_drops_foreign_sites_tagged_de(fixture):
    jobs = smartrecruiters.parse(fixture("smartrecruiters_bosch.json"), "BoschGroup", "Bosch")
    cities = {j.city for j in jobs}
    assert "Shanghai" not in cities
    assert {"Stuttgart", "Ansbach"} <= cities
    assert all(j.job_type == "internship" for j in jobs)
    assert all(j.language == "de" for j in jobs)
    assert jobs[0].url.startswith("https://jobs.smartrecruiters.com/BoschGroup/")


@pytest.mark.parametrize(
    ("location", "kept"),
    [
        ({"city": "Zeven", "region": "NDS", "latitude": "53.27", "longitude": "9.30"}, True),
        ({"city": "Ansbach", "region": "Mittelfranken", "postalCode": "91522"}, True),
        ({"city": "Stuttgart", "region": "BW"}, True),
        ({"city": "Shanghai", "region": "SHANGHAI", "address": "Shanghai"}, False),
        ({"city": "Shanghai", "region": "SH", "latitude": "31.2", "longitude": "121.5"}, False),
    ],
)
def test_smartrecruiters_region_check(location, kept):
    assert smartrecruiters._german_region(location) is kept


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
    assert first.workplace_type == "hybrid" and first.remote is False
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


def test_ashby_flat_secondary_address_in_small_german_town():
    raw = {"jobs": [{
        "id": "1", "title": "Engineer", "jobUrl": "https://jobs.ashbyhq.com/x/1",
        "location": "New York", "workplaceType": "OnSite",
        "address": {"postalAddress": {"addressCountry": "United States"}},
        "secondaryLocations": [{"location": "Tettnang", "address": {"addressCountry": "Germany"}}],
    }]}  # fmt: skip
    jobs = ashby.parse(raw, "x")
    assert len(jobs) == 1 and jobs[0].workplace_type == "onsite"


def test_recruitee_country_per_location(fixture):
    raw = fixture("recruitee_exeon.json")
    jobs = recruitee.parse(raw, "exeon", company="Exeon")
    # Every Exeon offer lists Zürich (CH) plus a remote location coded DE.
    assert len(jobs) == len(raw["offers"]) > 0
    assert jobs[0].id == f"recruitee:exeon-{raw['offers'][0]['id']}"
    assert jobs[0].url.startswith("https://exeon.recruitee.com/o/")
    assert jobs[0].posted_at.endswith("Z") and jobs[0].workplace_type == "hybrid"
    swiss = {**raw["offers"][0], "id": 1, "locations": [{"city": "Berlin", "country_code": "CH"}]}
    assert recruitee.parse({"offers": [swiss]}, "exeon") == []


def test_teamtailor_rss(fixture):
    jobs = teamtailor.parse([fixture("teamtailor_proxima.xml")], "proxima", company="Proxima")
    # 8 items: 6 in Düsseldorf, Germany; 2 in Chicago, United States.
    assert len(jobs) == 6
    assert all(j.city == "Düsseldorf" and j.workplace_type == "onsite" for j in jobs)
    assert jobs[0].id.startswith("teamtailor:proxima-") and len(jobs[0].source_job_id) == 36
    assert jobs[0].url.startswith("https://proxima.teamtailor.com/jobs/")
    assert jobs[0].posted_at.endswith("Z")


def test_teamtailor_paginates_past_first_page():
    item = "<item><guid>g{}</guid><title>T</title><link>u</link></item>"

    class Pages:
        def __init__(self):
            self.offsets = []

        def get_text(self, url, params=None):
            self.offsets.append(params["offset"])
            n = 100 if params["offset"] == 0 else 3
            return "<rss><channel>" + "".join(item.format(i) for i in range(n)) + "</channel></rss>"

    pages = Pages()
    raw = teamtailor.fetch(pages, "careers.example.de")
    assert pages.offsets == [0, 100] and len(raw) == 2


class _Recorder:
    def __init__(self, reply):
        self.reply, self.calls = reply, []

    def get_json(self, url, params=None, headers=None):
        self.calls.append((url, params))
        return self.reply(params)

    def get_text(self, url, params=None):
        self.calls.append((url, params))
        return self.reply(params)


def test_lever_eu_host_and_paging():
    rec = _Recorder(
        lambda p: [{"id": f"{p['skip']}-{i}"} for i in range(100 if p["skip"] == 0 else 7)]
    )
    postings = lever.fetch(rec, "acme", region="eu")
    assert len(postings) == 107
    assert [c[1]["skip"] for c in rec.calls] == [0, 100]
    assert rec.calls[0][0] == "https://api.eu.lever.co/v0/postings/acme"


def test_lever_capped_at_page_limit():
    rec = _Recorder(lambda p: [{"id": f"{p['skip']}-{i}"} for i in range(100)])
    with pytest.raises(Capped):
        lever.fetch(rec, "acme", max_pages=2)


def test_personio_languages_merge_by_id(fixture):
    xml = fixture("personio_ottonova.xml")
    rec = _Recorder(
        lambda p: xml.replace("<value>", "<value>Kubernetes ") if p["language"] == "en" else xml
    )
    raw = personio.fetch(rec, "ottonova", domain="jobs.personio.com", languages=["de", "en"])
    assert [c[0] for c in rec.calls] == ["https://ottonova.jobs.personio.com/xml"] * 2
    jobs = personio.parse(raw, "ottonova")
    one = personio.parse(xml, "ottonova")
    assert [j.id for j in jobs] == [j.id for j in one]
    assert jobs[0].url.startswith("https://ottonova.jobs.personio.com/job/")
    assert "Kubernetes" in jobs[0].skills and "Kubernetes" not in one[0].skills


def _sr_fetcher(fixture, detail):
    listing = fixture("smartrecruiters_bosch.json")

    class F:
        def __init__(self):
            self.details: list[str] = []

        def get_json(self, url, params=None, headers=None):
            if "/postings/" in url:
                self.details.append(url)
                return detail(url)
            return listing

    return F(), listing


def _sr_ad(url):
    return {"jobAd": {"sections": {"qualifications": {"text": "<p>Python und SQL</p>"}}}}


def test_smartrecruiters_fetches_details_for_german_postings(fixture):
    fetcher, listing = _sr_fetcher(fixture, _sr_ad)
    raw = smartrecruiters.fetch(fetcher, "BoschGroup")
    jobs = smartrecruiters.parse(raw, "BoschGroup", "Bosch")
    assert len(fetcher.details) == len(jobs) == 2  # only for postings that are kept
    assert all({"Python", "SQL"} <= set(j.skills) and j.snippet for j in jobs)


def test_smartrecruiters_reuses_unchanged_details(fixture):
    fetcher, listing = _sr_fetcher(fixture, _sr_ad)
    first = smartrecruiters.parse(smartrecruiters.fetch(fetcher, "BoschGroup"), "BoschGroup")
    known = {j.id: j.to_dict() for j in first}
    again, _ = _sr_fetcher(fixture, _sr_ad)
    jobs = smartrecruiters.parse(
        smartrecruiters.fetch(again, "BoschGroup", known=known), "BoschGroup"
    )
    assert again.details == []
    assert [(j.snippet, j.skills) for j in jobs] == [(j.snippet, j.skills) for j in first]


def test_smartrecruiters_detail_failure_keeps_role(fixture):
    def broken(url):
        raise RuntimeError("HTTP 500")

    fetcher, _ = _sr_fetcher(fixture, broken)
    jobs = smartrecruiters.parse(smartrecruiters.fetch(fetcher, "BoschGroup"), "BoschGroup")
    assert len(jobs) == 2 and all(j.snippet == "" for j in jobs)


def test_smartrecruiters_caps_new_details(fixture, monkeypatch):
    monkeypatch.setattr(smartrecruiters, "MAX_DETAILS", 0)
    fetcher, _ = _sr_fetcher(fixture, _sr_ad)
    jobs = smartrecruiters.parse(smartrecruiters.fetch(fetcher, "BoschGroup"), "BoschGroup")
    assert fetcher.details == [] and len(jobs) == 2


def test_dvinci_kit(fixture):
    jobs = dvinci.parse(fixture("dvinci_kit.json"), "jobs.pse.kit.edu", company="KIT")
    assert len(jobs) == 4  # the Ausbildung place is left out
    assert not any("Ausbildung" in j.title for j in jobs)
    job = jobs[0]
    assert job.id == "dvinci:jobs.pse.kit.edu-170977"
    assert (job.company, job.city, job.language) == ("KIT", "Eggenstein-Leopoldshafen", "de")
    assert "Scientific Computing Center (SCC)" in job.tags
    assert job.url.startswith("https://jobs.pse.kit.edu/de/jobs/170977/")
    assert {j.language for j in jobs} == {"de", "en"}
    assert any(j.job_type == "part_time" for j in jobs)


def test_dvinci_one_role_per_opening(fixture):
    jobs = dvinci.parse(fixture("dvinci_kit.json"), "jobs.pse.kit.edu", company="KIT")
    twin = next(j for j in jobs if j.source_job_id == "170942")
    assert twin.language == "en" and twin.aliases == ["dvinci:jobs.pse.kit.edu-170941"]
    assert not any(j.source_job_id == "170941" for j in jobs)


class _Workday:
    def __init__(self, facets, sizes):
        self.facets, self.sizes, self.bodies = facets, sizes, []

    def post_json(self, url, body):
        self.bodies.append(body)
        if body["limit"] == 1:
            return {"total": sum(self.sizes), "facets": self.facets, "jobPostings": []}
        n = body["offset"] // 20
        size = self.sizes[n] if n < len(self.sizes) else 0
        posts = [{"title": "T", "externalPath": f"/job/Berlin/T_{n}-{i}"} for i in range(size)]
        return {"total": sum(self.sizes) if n == 0 else 0, "jobPostings": posts}


def test_workday_uses_country_facet_and_first_page_total():
    facets = [
        {
            "facetParameter": "locationMainGroup",
            "values": [
                {
                    "facetParameter": "locationCountry",
                    "values": [{"descriptor": "Germany", "id": "de1"}, {"descriptor": "France"}],
                }
            ],
        }
    ]
    fake = _Workday(facets, [20, 20, 5])
    raw = workday.fetch(fake, "acme", "wd3", "Careers")
    assert raw["germany"] and len(raw["pages"]) == 3
    assert fake.bodies[1]["appliedFacets"] == {"locationCountry": ["de1"]}


def test_workday_falls_back_to_location_facets_naming_germany():
    facets = [
        {
            "facetParameter": "locations",
            "values": [
                {"descriptor": "Berlin, Germany", "id": "b"},
                {"descriptor": "Paris, France", "id": "p"},
            ],
        }
    ]
    fake = _Workday(facets, [3])
    raw = workday.fetch(fake, "acme", "wd3", "Careers")
    assert raw["germany"] and fake.bodies[1]["appliedFacets"] == {"locations": ["b"]}


def test_workday_caps_and_reads_text_without_facet(monkeypatch):
    monkeypatch.setattr(workday, "MAX_PAGES", 2)
    with pytest.raises(Capped) as cap:
        workday.fetch(_Workday([], [20, 20, 20]), "acme", "wd3", "Careers")
    assert not cap.value.raw["germany"]
    jobs = workday.parse(cap.value.raw, "acme")
    assert len(jobs) == 40 and jobs[0].city == "Berlin"


def test_workday_parses_philips(fixture):
    from datetime import date

    raw = fixture("workday_philips.json")
    jobs = workday.parse(raw, "philips", company="Philips", today=date(2026, 11, 3))
    assert len(jobs) == 4  # the repeated posting is kept once
    first = jobs[0]
    assert first.id == "workday:philips-589309-1"
    assert first.location == "Germany - Home Based"
    assert first.url == (
        "https://philips.wd3.myworkdayjobs.com/jobs-and-careers"
        "/job/Germany---Home-Based/Field-Specialist-IGT--all-genders--Region-Kln-Bonn_589309-1"
    )
    assert [j.posted_at[:10] for j in jobs] == [
        "2026-11-03",
        "2026-11-02",
        "2026-10-30",
        "2026-10-27",
    ]
    assert jobs[1].city == "Hamburg" and jobs[1].job_type == "working_student"


def _sf_pages(name):
    from pathlib import Path

    return (Path(__file__).parent / "fixtures" / name).read_text("utf-8")


def test_successfactors_fraunhofer_city_from_url():
    raw = {"country": "DE", "pages": [_sf_pages("successfactors_fraunhofer.html")]}
    jobs = successfactors.parse(raw, "jobs.fraunhofer.de", company="Fraunhofer")
    first, second = jobs[:2]
    assert first.id == "successfactors:jobs.fraunhofer.de-1403333433"
    assert (first.city, first.job_type) == ("Duisburg", "thesis")
    assert second.city == "Darmstadt" and "&apos;" not in second.url
    assert not any("Ausbildung" in j.title for j in jobs)


def test_successfactors_hensoldt_country_and_date_from_fields():
    raw = {"country": "", "pages": [_sf_pages("successfactors_hensoldt.html")]}
    jobs = successfactors.parse(raw, "jobs.hensoldt.net", company="HENSOLDT")
    assert jobs[0].location == "Ulm" and jobs[0].posted_at == "2026-11-03T00:00:00Z"
    assert jobs[0].url.startswith("https://jobs.hensoldt.net/job/Ulm-")


def _tile(i):
    return (
        f'<li class="job-tile job-id-{i} x" data-url="/job/Berlin-Dev-10115/{i}/">'
        f'<a class="jobTitle-link" href="#">Dev</a></li>'
    )


def test_successfactors_stops_when_page_repeats_and_caps(monkeypatch):
    class Pages:
        def __init__(self, repeat):
            self.repeat, self.params = repeat, []

        def get_text(self, url, params=None):
            self.params.append(params)
            n = params["startrow"]
            return "".join(_tile(0 if self.repeat else n + k) for k in range(2))

    fake = Pages(repeat=True)
    raw = successfactors.fetch(fake, "jobs.example.de", country="DE")
    assert len(raw["pages"]) == 1 and fake.params[0]["optionsFacetsDD_country"] == "DE"
    monkeypatch.setattr(successfactors, "MAX_PAGES", 3)
    with pytest.raises(Capped):
        successfactors.fetch(Pages(repeat=False), "jobs.example.de")


def test_softgarden_parses_widget_and_skips_training():
    from pathlib import Path

    raw = (Path(__file__).parent / "fixtures" / "softgarden_renk.html").read_text("utf-8")
    jobs = softgarden.parse(raw, "renk-group", company="RENK")
    first = jobs[0]
    assert first.id == "softgarden:renk-group-67620152"
    assert (first.city, first.posted_at) == ("Augsburg", "2026-11-02T00:00:00Z")
    assert first.url.startswith("https://renk-group.softgarden.io/job/67620152/")
    assert "&amp;" not in first.title and len({j.id for j in jobs}) == len(jobs)
    assert not any("Ausbildung" in j.title for j in jobs)
    assert any(j.job_type == "thesis" for j in jobs)


def test_join_keeps_german_roles_with_workplace(fixture):
    jobs = join.parse(fixture("join_accenture.json"), "accenture")
    assert len(jobs) == 8  # two Vienna roles left out
    first = jobs[0]
    assert first.id == "join:accenture-16471398"
    assert first.company == "Accenture"
    assert first.url == (
        "https://join.com/companies/accenture/"
        "16862569-consultant-infrastructure-und-capital-projects-all-genders"
    )
    assert first.workplace_type == "remote" and first.city == "Frankfurt"
    assert {j.workplace_type for j in jobs} == {"remote", "hybrid", "onsite"}


def test_join_skips_apprenticeships_and_repeats(fixture):
    pages = fixture("join_accenture.json")
    item = dict(pages[0]["jobs"]["items"][2], employmentType={"name": "Apprenticeship"})
    pages[0]["jobs"]["items"][2] = item
    pages.append(pages[1])
    assert len(join.parse(pages, "accenture")) == 7


def test_join_fetch_stops_at_page_count(fixture):
    pages = fixture("join_accenture.json")
    html = [
        '<script id="__NEXT_DATA__" type="application/json">'
        + json.dumps(
            {
                "props": {
                    "pageProps": {key: dict(p, jobs=dict(p["jobs"], pagination={"pageCount": 2}))}
                }
            }
        )
        + "</script>"
        for key, p in zip(("pageData", "initialState"), pages, strict=True)
    ]
    calls = []

    class Fake:
        def get_text(self, url, params=None):
            calls.append(params)
            return html[len(calls) - 1]

    assert len(join.parse(join.fetch(Fake(), "accenture"), "accenture")) == 8
    assert calls == [None, {"page": 2}]


def test_join_uses_page_name_and_marks_german_titles():
    page = {
        "company": {"name": "Hubside GmbH"},
        "jobs": {
            "items": [
                {"id": 1, "title": "Backend Entwickler (m/w/d)", "country": {"iso3166": "DE"},
                 "city": {"cityName": "Munich"}, "employmentType": {"name": "Employee"}},
                {"id": 2, "title": "Data Engineer", "country": {"iso3166": "DE"},
                 "city": {"cityName": "Berlin"}, "employmentType": {"name": "Employee"}},
            ]
        },
    }  # fmt: skip
    jobs = join.parse([page], "hubside", company="hubside")
    assert {j.company for j in jobs} == {"Hubside GmbH"}
    assert [j.language for j in jobs] == ["de", "en"]
    assert join.parse([page], "hubside", company="Hubside")[0].company == "Hubside"
