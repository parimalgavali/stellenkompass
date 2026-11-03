import json

import pytest

from stellenkompass_scanner.models import Job
from stellenkompass_scanner.run import _collect, _entry, _finish, carry_over_failed, write_outputs
from stellenkompass_scanner.sources._common import Capped


def _job(n: int, board: str = "foo") -> Job:
    return Job(
        id=f"greenhouse:{board}-{n}", title=f"Role {n}", company="Foo", location="Berlin",
        url="u", source="greenhouse", source_board=board,
    )  # fmt: skip


def _capped():
    raise Capped([_job(1)])


def test_capped_board_keeps_missing_roles_and_reports_partial():
    entry, jobs = _entry(1), []
    _collect(entry, jobs, "greenhouse", "foo", _capped, lambda raw: raw)
    _finish(entry, 0.0)
    assert entry["status"] == "partial" and entry["jobs"] == 1
    previous = {"jobs": [_job(1).to_dict(), _job(2).to_dict()]}
    assert carry_over_failed(jobs, {"greenhouse": entry}, previous) == 1
    assert sorted(j.id for j in jobs) == ["greenhouse:foo-1", "greenhouse:foo-2"]


def test_wrong_shape_is_a_failed_board():
    def broken():
        raise ValueError("unexpected response shape: no jobs list")

    entry = _entry(1)
    _collect(entry, [], "greenhouse", "foo", broken, lambda raw: raw)
    _finish(entry, 0.0)
    assert entry["status"] == "failed" and entry["errors"][0]["board"] == "foo"


def test_invalid_snapshot_is_not_written(tmp_path):
    (tmp_path / "jobs.json").write_text('{"jobs": ["old"]}')
    with pytest.raises(ValueError):
        write_outputs(tmp_path, [], {}, "now")
    with pytest.raises(ValueError):
        write_outputs(tmp_path, [_job(1), _job(1)], {}, "now")
    assert json.loads((tmp_path / "jobs.json").read_text()) == {"jobs": ["old"]}


def test_report_has_counts(tmp_path):
    summary = write_outputs(tmp_path, [_job(1)], {}, "now", collected=3, duplicates_removed=2)
    saved = json.loads((tmp_path / "scan_report.json").read_text())
    assert saved == summary and saved["duplicates_removed"] == 2 and saved["collected"] == 3
    assert not list(tmp_path.glob("*.tmp"))


def test_record_without_title_is_skipped():
    from stellenkompass_scanner.sources._common import build_job

    job = build_job(
        source="arbeitnow", job_id="x", title=" ", company="Foo",
        locations=["Berlin"], url="u", description="",
    )  # fmt: skip
    assert job is None
