import json

from conftest import load

from stellenkompass_scanner.dedupe import dedupe
from stellenkompass_scanner.models import Job
from stellenkompass_scanner.run import carry_first_seen, scan, write_outputs


def _job(source, title="Data Engineer (m/w/d)", company="Acme GmbH", city="Berlin"):
    return Job(
        id=f"{source}:{title}", title=title, company=company, location=city, url="u",
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
    }

    def _find(self, url):
        for part, name in self.routes.items():
            if part in url:
                return load(name)
        raise RuntimeError(f"HTTP 404 for {url}")

    def get_json(self, url, params=None):
        return self._find(url)

    def get_text(self, url, params=None):
        return self._find(url)


CONFIG = {
    "aggregators": {"arbeitnow": True},
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
        "arbeitnow", "greenhouse", "ashby", "lever", "smartrecruiters", "personio",
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
