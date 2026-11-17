"""Calling every source and saving what it returns.

One source failing does not stop the run: the failure is recorded in the day's
run log and the remaining sources are still read. A source that fails writes no
raw file for that day, which is what keeps the build from marking its postings
removed.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from jobwatcher import store
from jobwatcher.adapters import for_source


def utc_today() -> str:
    """The UTC date of the moment the run starts."""
    return datetime.now(timezone.utc).date().isoformat()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def fetch_source(source: dict, run_date: str, raw_root: Path | None = None) -> dict:
    """Read one source and save its raw payload. Never raises."""
    adapter = for_source(source)
    try:
        payload = adapter.fetch(source)
    except Exception as exc:  # noqa: BLE001 - any failure is just a failed source
        return {
            "name": source["name"],
            "employer": source["employer"],
            "ok": False,
            "count": 0,
            "error": f"{type(exc).__name__}: {exc}"[:400],
        }

    envelope = {
        "source": source["name"],
        "employer": source["employer"],
        "ats": source["ats"],
        "kind": source["kind"],
        "run_date": run_date,
        "fetched_at": utc_now(),
        "payload": payload,
    }
    store.write_raw(run_date, source["name"], envelope, raw_root)

    # Count the postings the way the build will read them, not the board's own
    # reported total, which Workday caps.
    rows = adapter.normalize(source, envelope)
    return {
        "name": source["name"],
        "employer": source["employer"],
        "ok": True,
        "count": len(rows),
        "error": "",
    }


def run(sources: list[dict], run_date: str | None = None,
        raw_root: Path | None = None) -> dict:
    """Read every source, record each result, and return the day's run log."""
    run_date = run_date or utc_today()
    started = utc_now()

    results = []
    for source in sources:
        result = fetch_source(source, run_date, raw_root)
        state = "ok" if result["ok"] else "FAILED"
        print(f"  {source['name']:<20} {state:<7} {result['count']:>5} postings"
              f"{'  ' + result['error'] if result['error'] else ''}")
        results.append(result)

    log = {"run_date": run_date, "run_time": started, "sources": results}
    store.write_run_log(run_date, log, raw_root)
    return log
