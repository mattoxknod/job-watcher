"""Where things live on disk."""

from __future__ import annotations

import gzip
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
RAW = DATA / "raw"
HISTORY_CSV = DATA / "history.csv"
STATUS_JSON = DATA / "status.json"

#: Per-day record of how every source fared, success or failure. It sits beside
#: the raw files so a rebuild can report source status without calling the web.
RUN_LOG = "_run.json"


def day_dir(run_date: str, raw_root: Path | None = None) -> Path:
    return (raw_root or RAW) / run_date


def raw_path(run_date: str, source_name: str, raw_root: Path | None = None) -> Path:
    return day_dir(run_date, raw_root) / f"{source_name}.json.gz"


def write_raw(run_date: str, source_name: str, envelope: dict,
              raw_root: Path | None = None) -> Path:
    path = raw_path(run_date, source_name, raw_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        json.dump(envelope, handle, separators=(",", ":"), sort_keys=True)
    return path


def read_raw(path: Path) -> dict:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def write_run_log(run_date: str, log: dict, raw_root: Path | None = None) -> Path:
    path = day_dir(run_date, raw_root) / RUN_LOG
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(log, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def read_run_log(run_date: str, raw_root: Path | None = None) -> dict:
    path = day_dir(run_date, raw_root) / RUN_LOG
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def raw_dates(raw_root: Path | None = None) -> list[str]:
    """Every date that has a raw directory, oldest first."""
    root = raw_root or RAW
    if not root.exists():
        return []
    return sorted(d.name for d in root.iterdir() if d.is_dir())


def raw_files(run_date: str, raw_root: Path | None = None) -> list[Path]:
    """The posting files for a day, skipping the run log."""
    directory = day_dir(run_date, raw_root)
    if not directory.exists():
        return []
    return sorted(directory.glob("*.json.gz"))
