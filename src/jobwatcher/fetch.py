"""Calling every source and saving what it returns.

One source failing does not stop the run: the failure is recorded in the day's
run log and the remaining sources are still read. A source that fails writes no
raw file for that day, which is what keeps the build from marking its postings
removed.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
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

    # Count the postings the way the build will read them, not the board's own
    # reported total, which Workday caps.
    rows = adapter.normalize(source, envelope)

    # Every board on this watch list always has openings, so a clean response
    # carrying none means the read went wrong - a renamed site, a board moved
    # behind a login - rather than an employer with nothing open. Writing that
    # out would mark every one of this source's postings removed, so it counts
    # as a failed source instead and the day simply says nothing about it.
    if not rows:
        return {
            "name": source["name"],
            "employer": source["employer"],
            "ok": False,
            "count": 0,
            "error": "the board returned no postings; treated as a failed read",
        }

    store.write_raw(run_date, source["name"], envelope, raw_root)
    return {
        "name": source["name"],
        "employer": source["employer"],
        "ok": True,
        "count": len(rows),
        "error": "",
    }


#: Sources are read at the same time. Each one is a different host and the
#: throttle in jobwatcher.http is per host, so running them together does not
#: push any single board harder - it just stops a slow board from holding up
#: the rest of the run.
WORKERS = 8


def run(sources: list[dict], run_date: str | None = None,
        raw_root: Path | None = None, workers: int = WORKERS) -> dict:
    """Read every source, record each result, and return the day's run log."""
    run_date = run_date or utc_today()
    started = utc_now()

    results: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=min(workers, max(len(sources), 1))) as pool:
        futures = {
            pool.submit(fetch_source, source, run_date, raw_root): source
            for source in sources
        }
        for future in as_completed(futures):
            result = future.result()
            results[result["name"]] = result
            state = "ok" if result["ok"] else "FAILED"
            print(f"  {result['name']:<20} {state:<7} {result['count']:>5} postings"
                  f"{'  ' + result['error'] if result['error'] else ''}",
                  flush=True)

    # Report in watch-list order rather than whichever board answered first, so
    # the run log and the status file do not churn between runs.
    log = {
        "run_date": run_date,
        "run_time": started,
        "sources": [results[s["name"]] for s in sources if s["name"] in results],
    }
    store.write_run_log(run_date, log, raw_root)
    return log
