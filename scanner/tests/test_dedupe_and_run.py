import json

from conftest import load

from stellenkompass_scanner.dedupe import dedupe
from stellenkompass_scanner.models import Job
from stellenkompass_scanner.run import carry_first_seen, carry_over_failed, scan, write_outputs


def _job(source, title="Data Engineer (m/w/d)", company="Acme GmbH", city="Berlin", n=1):
    return Job(
        id=f"{source}:{title}-{city}-{n}", title=title, company=company, location=city, url="u",
        source=source, city=city,
    )  # fmt: skip


def test_dedupe_prefers_company_board():
    jobs = [_job("arbeitnow"), _job("greenhouse", "Data Engineer", "Acme")]
    kept = dedupe(jobs)
    assert [j.source for j in kept] == ["greenhouse"]


def test_dedupe_keeps_different_cities():
    assert len(dedupe([_job("ashby"), _job("ashby", city="Munich")])) == 2


class FakeFetcher:
    routes = {
        "boards-api.greenhouse.io/v1/boards/n26/": "greenhouse_n26.json",
        "api.ashbyhq.com/posting-api/job-board/parloa": "ashby_parloa.json",
        "api.lever.co/v0/postings/pigment": "lever_pigment.json",
        "api.smartrecruiters.com/v1/companies/BoschGroup/": "smartrecruiters_bosch.json",
        "ottonova.jobs.personio.de/xml": "personio_ottonova.xml",
        "www.arbeitnow.com/api/job-board-api": "arbeitnow.json",
        "rest.arbeitsagentur.de/": "bundesagentur.json",
    }

    def _find(self, url):
        for part, name in self.routes.items():
            if part in url:
                return load(name)
        raise RuntimeError(f"HTTP 404 for {url}")

    def get_json(self, url, params=None, headers=None):
        return self._find(url)

    def get_text(self, url, params=None):
        return self._find(url)


CONFIG = {
    "aggregators": {"arbeitnow": True, "bundesagentur": True},
    "bundesagentur": {"queries": ["Informatik"]},
    "greenhouse": [{"board": "n26", "name": "N26"}, "gone-company"],
    "ashby": [{"board": "parloa", "name": "Parloa"}],
    "lever": ["pigment"],
    "smartrecruiters": [{"board": "BoschGroup", "name": "Bosch"}],
    "personio": ["ottonova"],
}


def test_scan_survives_a_failing_board():
    jobs, report = scan(FakeFetcher(), CONFIG)
    assert report["greenhouse"]["boards"] == 2
    assert report["greenhouse"]["errors"][0]["board"] == "gone-company"
    assert report["greenhouse"]["jobs"] == 2
    assert {j.source for j in jobs} == {
        "arbeitnow", "bundesagentur", "greenhouse", "ashby", "lever", "smartrecruiters", "personio",
    }  # fmt: skip


def test_write_outputs_and_first_seen(tmp_path):
    jobs, report = scan(FakeFetcher(), CONFIG)
    previous = {"jobs": [{"id": jobs[0].id, "first_seen": "2026-01-01T00:00:00Z"}]}
    carry_first_seen(jobs, previous, "2026-11-03T05:00:00Z")
    assert jobs[0].first_seen == "2026-01-01T00:00:00Z"
    assert jobs[1].first_seen == "2026-11-03T05:00:00Z"

    write_outputs(tmp_path, jobs, report, "2026-11-03T05:00:00Z")
    data = json.loads((tmp_path / "jobs.json").read_text())
    assert data["count"] == len(jobs) == len(data["jobs"])
    assert set(data["jobs"][0]) >= {"id", "title", "company", "city", "job_type", "language"}
    summary = json.loads((tmp_path / "scan_report.json").read_text())
    assert summary["sources"]["greenhouse"]["errors"]


def test_failed_boards_keep_last_scan_jobs():
    jobs, report = scan(FakeFetcher(), CONFIG)
    report["arbeitnow"]["errors"] = [{"board": "arbeitnow", "error": "HTTP 429"}]
    previous = {
        "jobs": [
            {"id": "arbeitnow:old-role", "title": "Old", "company": "A", "location": "Berlin",
             "url": "u", "source": "arbeitnow", "skills_unknown_field": 1},
            {"id": "greenhouse:gone-company-7", "title": "Gone", "company": "G",
             "location": "Munich", "url": "u", "source": "greenhouse"},
            {"id": "greenhouse:n26-1", "title": "Live board", "company": "N26",
             "location": "Berlin", "url": "u", "source": "greenhouse"},
        ]
    }  # fmt: skip
    before = len(jobs)
    assert carry_over_failed(jobs, report, previous) == 2
    assert {j.id for j in jobs[before:]} == {"arbeitnow:old-role", "greenhouse:gone-company-7"}
    assert report["arbeitnow"]["carried"] == 1
    assert report["greenhouse"]["carried"] == 1
    assert report["ashby"]["carried"] == 0


def test_carry_over_without_previous_scan():
    jobs, report = scan(FakeFetcher(), CONFIG)
    assert carry_over_failed(jobs, report, None) == 0


def test_dedupe_keeps_distinct_openings_and_aliases_copies():
    a, b = _job("greenhouse", n=1), _job("greenhouse", n=2)
    copy = _job("arbeitnow", "Data Engineer", "Acme")
    kept = dedupe([copy, a, b, _job("greenhouse", n=1)])
    assert sorted(j.id for j in kept) == sorted([a.id, b.id])
    assert copy.id in kept[0].aliases


def test_carry_over_matches_exact_board():
    report = {"greenhouse": {"errors": [{"board": "foo", "error": "HTTP 500"}]}}
    previous = {
        "jobs": [
            {"id": "greenhouse:foo-1", "title": "A", "company": "Foo", "location": "Berlin",
             "url": "u", "source": "greenhouse", "source_board": "foo"},
            {"id": "greenhouse:foo-bar-2", "title": "B", "company": "Foo Bar", "location": "Berlin",
             "url": "u", "source": "greenhouse", "source_board": "foo-bar"},
        ]
    }  # fmt: skip
    jobs = []
    assert carry_over_failed(jobs, report, previous) == 1
    assert [j.id for j in jobs] == ["greenhouse:foo-1"]


def test_first_seen_and_history_follow_aliases():
    job = _job("greenhouse")
    job.aliases = ["arbeitnow:acme-data-engineer"]
    previous = {
        "jobs": [
            {"id": "arbeitnow:acme-data-engineer", "first_seen": "2026-10-01T00:00:00Z",
             "aliases": ["arbeitnow:older-slug"]},
        ]
    }  # fmt: skip
    carry_first_seen([job], previous, "2026-11-03T05:00:00Z")
    assert job.first_seen == "2026-10-01T00:00:00Z"
    assert job.aliases == ["arbeitnow:acme-data-engineer", "arbeitnow:older-slug"]
