from stellenkompass_scanner.geo import in_germany
from stellenkompass_scanner.sources._common import build_job


def test_explicit_foreign_country_beats_city_name():
    assert not in_germany(["Frankfurt, KY"], ["US"])
    assert not in_germany(["Berlin"], ["US"])


def test_unlisted_german_town_with_code_is_kept():
    assert in_germany(["Tettnang"], ["DE"])
    assert in_germany(["", "Remote"], ["de"])


def test_multi_country_posting_needs_one_german_location():
    assert in_germany(["London", "Munich"], ["GB", "DE"])
    assert in_germany(["London", "Munich"], ["GB"])  # second location uncoded: read as text
    assert not in_germany(["London", "Paris"], ["GB", "FR"])


def test_missing_country_falls_back_to_text():
    assert in_germany(["Berlin, Germany"])
    assert not in_germany(["Somewhere"])


def _job(location: str, **kw):
    return build_job(source="arbeitnow", job_id="x", title="Engineer", company="Foo",
                     locations=[location], url="u", **kw)  # fmt: skip


def test_workplace_type():
    assert _job("Berlin (Hybrid)").workplace_type == "hybrid"
    assert _job("Berlin").workplace_type == "unknown"
    remote = _job("Remote, Germany", workplace="remote")
    assert remote.workplace_type == "remote" and remote.remote is True
    assert _job("Berlin", workplace="hybrid").remote is False
