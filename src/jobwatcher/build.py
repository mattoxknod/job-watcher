"""Rebuilding ``data/history.csv`` and ``data/status.json`` from the raw files.

Nothing here touches the network. Every number comes out of
``data/raw/<date>/<source>.json.gz`` plus the per-day run logs, so the build is
reproducible and a rule change applies to the whole history.
"""

from __future__ import annotations

import json
from pathlib import Path

from jobwatcher import store
from jobwatcher.adapters import for_source
from jobwatcher.history import build_history, write_history
from jobwatcher.sources import BY_NAME


def load_day(run_date: str, raw_root: Path | None = None) -> dict[str, list[dict]]:
    """Normalize every raw file of one day into the common columns."""
    by_source: dict[str, list[dict]] = {}

    for path in store.raw_files(run_date, raw_root):
        envelope = store.read_raw(path)
        source_name = envelope.get("source") or path.name.removesuffix(".json.gz")
        source = BY_NAME.get(source_name)
        if source is None:
            # A source retired from the watch list keeps its history: fall back
            # to what the raw file itself recorded about it.
            source = {
                "name": source_name,
                "employer": envelope.get("employer", source_name),
                "ats": envelope.get("ats", ""),
                "kind": envelope.get("kind", ""),
            }
            if not source["kind"]:
                continue
            source.update(envelope.get("source_config") or {})

        employer = envelope.get("employer") or source.get("employer") or source_name
        rows = for_source(source).normalize(source, envelope)
        for row in rows:
            row["employer"] = employer
        by_source[source_name] = rows

    return by_source


def load_days(raw_root: Path | None = None) -> list[tuple[str, dict]]:
    """Every day of raw files, oldest first."""
    return [(d, load_day(d, raw_root)) for d in store.raw_dates(raw_root)]


def build_status(rows: list[dict], dates: list[str],
                 raw_root: Path | None = None) -> dict:
    """Describe the latest run, as ``data/status.json``."""
    latest = dates[-1] if dates else ""
    log = store.read_run_log(latest, raw_root) if latest else {}

    new_today = [
        r for r in rows
        if r["first_seen"] == latest and not r["first_run"]
    ]
    removed_today = [r for r in rows if r["removed_date"] == latest]

    return {
        "run_time": log.get("run_time", ""),
        "first_run_date": dates[0] if dates else "",
        "days_with_success": len(dates),
        "open": sum(1 for r in rows if r["status"] == "open"),
        "new_today": len(new_today),
        "removed_today": len(removed_today),
        "sources": [
            {"name": s["name"], "ok": s["ok"], "count": s["count"]}
            for s in log.get("sources", [])
        ],
    }


def write_status(status: dict, path: Path | None = None) -> Path:
    path = path or store.STATUS_JSON
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    return path


def build(raw_root: Path | None = None, history_path: Path | None = None,
          status_path: Path | None = None) -> tuple[list[dict], dict]:
    """Rebuild the history and the status file from the raw files."""
    dates = store.raw_dates(raw_root)
    days = [(d, load_day(d, raw_root)) for d in dates]
    rows = build_history(days)

    write_history(rows, history_path or store.HISTORY_CSV)
    status = build_status(rows, dates, raw_root)
    write_status(status, status_path)
    return rows, status
