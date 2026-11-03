"""Run all sources and write data/jobs.json and data/scan_report.json.

Usage: uv run stellenkompass-scan --out ../data
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from .dedupe import dedupe
from .http import Fetcher, HttpFetcher
from .models import Job
from .sources import AGGREGATORS, PER_COMPANY
from .sources._common import Capped

log = logging.getLogger("stellenkompass")
DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "companies.yaml"


def load_config(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _boards(config: dict[str, Any], source: str) -> list[dict[str, Any]]:
    boards = []
    for entry in config.get(source) or []:
        if isinstance(entry, str):
            entry = {"board": entry}
        options = {k: v for k, v in entry.items() if k not in ("board", "name")}
        boards.append(
            {
                "board": entry["board"],
                "name": entry.get("name") or entry["board"],
                "options": options,
            }
        )
    return boards


def scan(fetcher: Fetcher, config: dict[str, Any]) -> tuple[list[Job], dict[str, Any]]:
    jobs: list[Job] = []
    report: dict[str, Any] = {}

    for source, module in AGGREGATORS.items():
        if not (config.get("aggregators") or {}).get(source, True):
            continue
        started = time.monotonic()
        entry = _entry(1)
        _collect(
            entry,
            jobs,
            source,
            source,
            lambda m=module, s=source: m.fetch(fetcher, config.get(s) or {}),
            module.parse,
        )
        _finish(entry, started)
        report[source] = entry

    for source, module in PER_COMPANY.items():
        boards = _boards(config, source)
        if not boards:
            continue
        started = time.monotonic()
        entry = _entry(len(boards))
        for b in boards:
            _collect(
                entry, jobs, source, b["board"],
                lambda m=module, b=b: m.fetch(fetcher, b["board"], **b["options"]),
                lambda raw, m=module, b=b: m.parse(raw, b["board"], company=b["name"]),
            )  # fmt: skip
        _finish(entry, started)
        report[source] = entry

    return jobs, report


def _entry(boards: int) -> dict[str, Any]:
    return {"boards": boards, "jobs": 0, "errors": [], "capped": []}


def _collect(entry, jobs, source, board, fetch, parse) -> None:
    """Fetch and parse one board; record capped or failed boards instead of raising."""
    try:
        try:
            found = parse(fetch())
        except Capped as cap:
            found = parse(cap.raw)
            entry["capped"].append({"board": board, "carry": cap.carry})
            log.warning("%s/%s hit its page limit", source, board)
        jobs.extend(found)
        entry["jobs"] += len(found)
    except Exception as exc:  # noqa: BLE001 - one board must not stop the scan
        log.warning("%s/%s failed: %s", source, board, exc)
        entry["errors"].append({"board": board, "error": str(exc)[:200]})


def _finish(entry: dict[str, Any], started: float) -> None:
    failed = len(entry["errors"])
    if failed and failed == entry["boards"]:
        entry["status"] = "failed"
    elif failed or entry["capped"]:
        entry["status"] = "partial"
    else:
        entry["status"] = "complete"
    entry["seconds"] = round(time.monotonic() - started, 1)


def carry_over_failed(
    jobs: list[Job], report: dict[str, Any], previous: dict[str, Any] | None
) -> int:
    """Keep last scan's jobs from boards that failed or were cut off by a page limit now."""
    old = [j for j in (previous or {}).get("jobs", []) if isinstance(j, dict) and "id" in j]
    present = {j.id for j in jobs}
    carried = 0
    for source, entry in report.items():
        failed = {e["board"] for e in entry["errors"]}
        failed |= {c["board"] for c in entry.get("capped", []) if c["carry"]}
        kept = [
            Job.from_dict(j)
            for j in old
            if j["id"] not in present and _from_failed(j, source, failed)
        ]
        entry["carried"] = len(kept)
        jobs.extend(kept)
        carried += len(kept)
    return carried


def _from_failed(job: dict, source: str, failed: set[str]) -> bool:
    """Was this previous job scanned from one of the failed boards of `source`?"""
    if not failed or job.get("source", job["id"].split(":", 1)[0]) != source:
        return False
    if source in AGGREGATORS:
        return source in failed
    if "source_board" in job:
        return job["source_board"] in failed
    # jobs.json from before source_board existed (one transitional run): old prefix match.
    return job["id"].startswith(tuple(f"{source}:{b}-" for b in failed))


def carry_first_seen(jobs: list[Job], previous: dict[str, Any] | None, now: str) -> None:
    """Keep first_seen and old ids across runs, also when a role moves to another source."""
    old: dict[str, dict] = {}
    for prev in (previous or {}).get("jobs", []):
        for ident in [prev["id"], *(prev.get("aliases") or [])]:
            old.setdefault(ident, prev)
    for job in jobs:
        matches = [old[i] for i in dict.fromkeys([job.id, *job.aliases]) if i in old]
        dates = [m["first_seen"] for m in matches if m.get("first_seen")]
        job.first_seen = min(dates) if dates else now
        history = [i for m in matches for i in [m["id"], *(m.get("aliases") or [])]]
        job.aliases = [i for i in dict.fromkeys([*job.aliases, *history]) if i != job.id]


def validate(jobs: list[Job]) -> None:
    """Refuse to publish a broken snapshot."""
    if not jobs:
        raise ValueError("no jobs found from any source")
    ids = [j.id for j in jobs]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate job ids")
    bad = [j.id for j in jobs if not (j.title and j.url and j.source)]
    if bad:
        raise ValueError(f"{len(bad)} jobs without title, url or source, e.g. {bad[0]}")


def _replace(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def write_outputs(
    out_dir: Path, jobs: list[Job], report: dict[str, Any], now: str, **counts: int
) -> dict[str, Any]:
    validate(jobs)
    out_dir.mkdir(parents=True, exist_ok=True)
    jobs = sorted(jobs, key=lambda j: (j.posted_at or j.first_seen, j.id), reverse=True)
    payload = {"generated_at": now, "count": len(jobs), "jobs": [j.to_dict() for j in jobs]}
    summary = {"generated_at": now, "total_jobs": len(jobs), **counts, "sources": report}
    _replace(out_dir / "jobs.json", json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    _replace(out_dir / "scan_report.json", json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=Path("../data"))
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--pause", type=float, default=0.5, help="seconds between requests")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)

    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    fetcher = HttpFetcher(pause=args.pause)
    try:
        raw_jobs, report = scan(fetcher, load_config(args.config))
    finally:
        fetcher.close()

    previous_path = args.out / "jobs.json"
    previous = json.loads(previous_path.read_text("utf-8")) if previous_path.exists() else None
    carried = carry_over_failed(raw_jobs, report, previous)
    jobs = dedupe(raw_jobs)
    carry_first_seen(jobs, previous, now)
    try:
        write_outputs(
            args.out, jobs, report, now,
            collected=len(raw_jobs) - carried, carried=carried,
            duplicates_removed=len(raw_jobs) - len(jobs),
        )  # fmt: skip
    except ValueError as exc:
        log.error("not publishing: %s", exc)
        return 1
    log.info(
        "wrote %d jobs (%d duplicates removed, %d kept from last scan)",
        len(jobs), len(raw_jobs) - len(jobs), carried,
    )  # fmt: skip
    for source, entry in report.items():
        log.info(
            "  %-16s %5d jobs, %d errors, %s",
            source, entry["jobs"], len(entry["errors"]), entry["status"],
        )  # fmt: skip
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
