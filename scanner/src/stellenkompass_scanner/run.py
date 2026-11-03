"""Run all sources and write data/jobs.json and data/scan_report.json.

Usage: uv run stellenkompass-scan --out ../data
"""

from __future__ import annotations

import argparse
import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from .dedupe import dedupe
from .http import Fetcher, HttpFetcher
from .models import Job
from .sources import AGGREGATORS, PER_COMPANY

log = logging.getLogger("stellenkompass")
DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "companies.yaml"


def load_config(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _boards(config: dict[str, Any], source: str) -> list[dict[str, str]]:
    boards = []
    for entry in config.get(source) or []:
        if isinstance(entry, str):
            entry = {"board": entry}
        boards.append({"board": entry["board"], "name": entry.get("name") or entry["board"]})
    return boards


def scan(fetcher: Fetcher, config: dict[str, Any]) -> tuple[list[Job], dict[str, Any]]:
    jobs: list[Job] = []
    report: dict[str, Any] = {}

    for source, module in AGGREGATORS.items():
        if not (config.get("aggregators") or {}).get(source, True):
            continue
        started = time.monotonic()
        entry = {"boards": 1, "jobs": 0, "errors": []}
        try:
            found = module.parse(module.fetch(fetcher, config.get(source) or {}))
            jobs.extend(found)
            entry["jobs"] = len(found)
        except Exception as exc:  # noqa: BLE001 - one source must not stop the scan
            log.warning("%s failed: %s", source, exc)
            entry["errors"].append({"board": source, "error": str(exc)[:200]})
        entry["seconds"] = round(time.monotonic() - started, 1)
        report[source] = entry

    for source, module in PER_COMPANY.items():
        boards = _boards(config, source)
        if not boards:
            continue
        started = time.monotonic()
        entry = {"boards": len(boards), "jobs": 0, "errors": []}
        for b in boards:
            try:
                raw = module.fetch(fetcher, b["board"])
                found = module.parse(raw, b["board"], company=b["name"])
                jobs.extend(found)
                entry["jobs"] += len(found)
            except Exception as exc:  # noqa: BLE001
                log.warning("%s/%s failed: %s", source, b["board"], exc)
                entry["errors"].append({"board": b["board"], "error": str(exc)[:200]})
        entry["seconds"] = round(time.monotonic() - started, 1)
        report[source] = entry

    return jobs, report


def _id_prefix(source: str, board: str) -> str:
    return f"{source}:" if source in AGGREGATORS else f"{source}:{board}-"


def carry_over_failed(
    jobs: list[Job], report: dict[str, Any], previous: dict[str, Any] | None
) -> int:
    """Keep last scan's jobs from boards that failed now, so a rate limit doesn't empty the list."""
    old = [j for j in (previous or {}).get("jobs", []) if isinstance(j, dict) and "id" in j]
    carried = 0
    for source, entry in report.items():
        prefixes = tuple(_id_prefix(source, e["board"]) for e in entry["errors"])
        kept = [Job.from_dict(j) for j in old if prefixes and j["id"].startswith(prefixes)]
        entry["carried"] = len(kept)
        jobs.extend(kept)
        carried += len(kept)
    return carried


def carry_first_seen(jobs: list[Job], previous: dict[str, Any] | None, now: str) -> None:
    """Keep the date we first saw each job across runs, so the app can show 'new'."""
    seen = {j["id"]: j.get("first_seen") for j in (previous or {}).get("jobs", [])}
    for job in jobs:
        job.first_seen = seen.get(job.id) or now


def write_outputs(
    out_dir: Path, jobs: list[Job], report: dict[str, Any], now: str
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    jobs = sorted(jobs, key=lambda j: (j.posted_at or j.first_seen, j.id), reverse=True)
    payload = {"generated_at": now, "count": len(jobs), "jobs": [j.to_dict() for j in jobs]}
    (out_dir / "jobs.json").write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    summary = {
        "generated_at": now,
        "total_jobs": len(jobs),
        "sources": report,
    }
    (out_dir / "scan_report.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
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
    summary = write_outputs(args.out, jobs, report, now)
    summary["duplicates_removed"] = len(raw_jobs) - len(jobs)
    log.info(
        "wrote %d jobs (%d duplicates removed, %d kept from last scan)",
        len(jobs), len(raw_jobs) - len(jobs), carried,
    )  # fmt: skip
    for source, entry in report.items():
        log.info("  %-16s %5d jobs, %d errors", source, entry["jobs"], len(entry["errors"]))
    if raw_jobs == []:
        log.error("no jobs found from any source")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
