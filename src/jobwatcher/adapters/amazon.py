"""Amazon's in-house board at amazon.jobs, read through ``search.json``.

The whole board runs well past the 5,000 postings the project allows, so it is
requested with a search term recorded in :mod:`jobwatcher.sources`.
"""

from __future__ import annotations

from datetime import datetime

from jobwatcher.http import get_json

SEARCH = "https://www.amazon.jobs/en/search.json"
PAGE = 100
MAX_PAGES = 50


def fetch(source: dict) -> dict:
    jobs: list[dict] = []
    hits = None

    for page in range(MAX_PAGES):
        data = get_json(
            SEARCH,
            params={
                "base_query": source.get("search_text", ""),
                "offset": page * PAGE,
                "result_limit": PAGE,
                "sort": "recent",
            },
        )
        if hits is None:
            hits = data.get("hits", 0)
        batch = data.get("jobs") or []
        jobs.extend(batch)
        if len(batch) < PAGE or len(jobs) >= (hits or 0):
            break

    return {"endpoint": SEARCH, "total": hits or 0, "jobs": jobs}


def _posted_date(value: str) -> str:
    """Amazon writes posting dates as "November 14, 2026"."""
    if not value:
        return ""
    try:
        return datetime.strptime(value.strip(), "%B %d, %Y").date().isoformat()
    except ValueError:
        return ""


def normalize(source: dict, raw: dict) -> list[dict]:
    rows = []
    for job in raw["payload"].get("jobs") or []:
        source_id = str(job.get("id_icims") or job.get("id") or "").strip()
        if not source_id:
            continue
        path = job.get("job_path") or ""
        rows.append(
            {
                "source_id": source_id,
                "title": (job.get("title") or "").strip(),
                "location": (
                    job.get("normalized_location") or job.get("location") or ""
                ).strip(),
                "department": (
                    job.get("job_category") or job.get("business_category") or ""
                ).strip(),
                "posted_date": _posted_date(job.get("posted_date") or ""),
                "url": f"https://www.amazon.jobs{path}" if path else "",
            }
        )
    return rows
