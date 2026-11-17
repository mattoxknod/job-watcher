"""Command line entry points.

    uv run python -m jobwatcher.cli fetch    # call every source, save raw files
    uv run python -m jobwatcher.cli build    # raw files -> history.csv, status.json
    uv run python -m jobwatcher.cli run      # fetch, then build
    uv run python -m jobwatcher.cli issue    # open or update today's issue
"""

from __future__ import annotations

import argparse
import sys

from jobwatcher import build as build_mod
from jobwatcher import fetch as fetch_mod
from jobwatcher.sources import all_sources


def _fetch(args) -> int:
    run_date = args.date or fetch_mod.utc_today()
    sources = all_sources()
    if args.only:
        wanted = set(args.only.split(","))
        sources = [s for s in sources if s["name"] in wanted]
    print(f"Fetching {len(sources)} sources for {run_date} (UTC)")
    log = fetch_mod.run(sources, run_date)
    ok = sum(1 for s in log["sources"] if s["ok"])
    print(f"{ok}/{len(log['sources'])} sources ok")
    return 0


def _build(args) -> int:
    rows, status = build_mod.build()
    print(f"history.csv: {len(rows)} rows")
    print(
        f"status.json: open={status['open']} new_today={status['new_today']} "
        f"removed_today={status['removed_today']} "
        f"days_with_success={status['days_with_success']}"
    )
    return 0


def _issue(args) -> int:
    from jobwatcher import issue as issue_mod

    run_date = args.date or fetch_mod.utc_today()
    issue_mod.load_and_publish(run_date)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="jobwatcher")
    sub = parser.add_subparsers(dest="command", required=True)

    fetch_cmd = sub.add_parser("fetch", help="call every source and save raw files")
    fetch_cmd.add_argument("--date", help="UTC date to write under (default: today)")
    fetch_cmd.add_argument("--only", help="comma-separated source names")
    fetch_cmd.set_defaults(func=_fetch)

    build_cmd = sub.add_parser("build", help="rebuild history.csv and status.json")
    build_cmd.set_defaults(func=_build)

    issue_cmd = sub.add_parser("issue", help="open or update today's issue")
    issue_cmd.add_argument("--date")
    issue_cmd.set_defaults(func=_issue)

    run_cmd = sub.add_parser("run", help="fetch then build")
    run_cmd.add_argument("--date")
    run_cmd.add_argument("--only")
    run_cmd.set_defaults(func=lambda a: _fetch(a) or _build(a))

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
