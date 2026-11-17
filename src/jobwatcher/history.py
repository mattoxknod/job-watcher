"""Building the history from the raw files.

The history is a pure function of the raw files: feed the same days in and the
same ``history.csv`` comes out, so changing a rule here changes every day of
the history at once.

The rules the build follows, per day and per source:

* A posting seen for the first time gets that day as its ``first_seen``.
* Every posting its source lists that day gets that day as its ``last_seen``.
* An open posting is marked ``removed`` with that day's date when its source
  has a raw file for that day and no longer lists it. A source that failed, and
  so wrote no raw file, removes nothing.
* A removed posting its source lists again becomes ``open``, its
  ``removed_date`` cleared and its ``first_seen`` left alone.
* ``first_run`` is true for a posting listed in the first raw file of its
  source, whose real start date is therefore unknown.
"""

from __future__ import annotations

import csv
from pathlib import Path

from jobwatcher.region import region_of
from jobwatcher.role import in_role

COLUMNS = [
    "posting_id",
    "source",
    "source_id",
    "employer",
    "title",
    "location",
    "department",
    "posted_date",
    "url",
    "in_role",
    "first_run",
    "first_seen",
    "last_seen",
    "status",
    "removed_date",
    # Added on top of the required columns, so the ones the project specifies
    # keep the exact order it lists them in.
    "region",
]


def posting_id(source_name: str, source_id: str) -> str:
    """The source and the source's own ID for the posting."""
    return f"{source_name}:{source_id}"


def build_history(days: list[tuple[str, dict[str, list[dict]]]]) -> list[dict]:
    """Replay every day in order and return the history rows.

    ``days`` is ``[(date, {source_name: [normalized postings]}), ...]`` in
    ascending date order. A source missing from a day's mapping had no raw file
    that day.
    """
    history: dict[str, dict] = {}
    first_day_of_source: dict[str, str] = {}

    for day, by_source in days:
        for source_name, postings in sorted(by_source.items()):
            is_first_run_of_source = source_name not in first_day_of_source
            if is_first_run_of_source:
                first_day_of_source[source_name] = day

            listed: set[str] = set()
            for posting in postings:
                pid = posting_id(source_name, posting["source_id"])
                listed.add(pid)
                row = history.get(pid)
                if row is None:
                    history[pid] = {
                        "posting_id": pid,
                        "source": source_name,
                        "source_id": posting["source_id"],
                        "employer": posting["employer"],
                        "title": posting["title"],
                        "location": posting["location"],
                        "region": region_of(posting["location"]),
                        "department": posting["department"],
                        "posted_date": posting["posted_date"],
                        "url": posting["url"],
                        "in_role": in_role(posting["title"]),
                        "first_run": is_first_run_of_source,
                        "first_seen": day,
                        "last_seen": day,
                        "status": "open",
                        "removed_date": "",
                    }
                    continue

                # Seen before: refresh what the board may have edited, mark it
                # seen today, and reopen it if it had been removed.
                row["title"] = posting["title"]
                row["location"] = posting["location"]
                row["region"] = region_of(posting["location"])
                row["department"] = posting["department"]
                row["posted_date"] = posting["posted_date"]
                row["url"] = posting["url"]
                row["in_role"] = in_role(posting["title"])
                row["last_seen"] = day
                row["status"] = "open"
                row["removed_date"] = ""

            # This source has a raw file today, so anything of its own it no
            # longer lists is gone as of today.
            for pid, row in history.items():
                if (
                    row["source"] == source_name
                    and row["status"] == "open"
                    and pid not in listed
                ):
                    row["status"] = "removed"
                    row["removed_date"] = day

    return [history[pid] for pid in sorted(history)]


def write_history(rows: list[dict], path: Path) -> None:
    """Write the rows to ``path`` in the fixed column order."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            out = dict(row)
            out["in_role"] = "true" if row["in_role"] else "false"
            out["first_run"] = "true" if row["first_run"] else "false"
            writer.writerow(out)


def read_history(path: Path) -> list[dict]:
    """Read ``history.csv`` back, restoring the two boolean columns."""
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["in_role"] = row["in_role"] == "true"
        row["first_run"] = row["first_run"] == "true"
    return rows
