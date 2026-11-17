"""Workday boards, read through the public ``wday/cxs`` JSON endpoint.

A board is addressed by tenant, host and site. The endpoint pages 20 postings
at a time and reports a ``total`` that Workday caps at 2,000.
"""

from __future__ import annotations

import re
from datetime import date, timedelta

from jobwatcher.http import post_json

PAGE = 20
MAX_PAGES = 150

#: "Posted 5 Days Ago" and friends. Workday gives no absolute posting date, so
#: the relative phrase is resolved against the run date stored in the raw file.
_DAYS_AGO = re.compile(r"posted\s+(\d+)\+?\s+day", re.I)


def endpoint(source: dict) -> str:
    return (
        f"https://{source['tenant']}.{source['host']}.myworkdayjobs.com"
        f"/wday/cxs/{source['tenant']}/{source['site']}/jobs"
    )


def fetch(source: dict) -> dict:
    """Page the board and return every posting it lists."""
    url = endpoint(source)
    postings: list[dict] = []
    total = None

    for page in range(MAX_PAGES):
        body = {
            "appliedFacets": {},
            "limit": PAGE,
            "offset": page * PAGE,
            "searchText": source.get("search_text", ""),
        }
        data = post_json(url, body)
        if total is None:
            total = data.get("total", 0)
        batch = data.get("jobPostings") or []
        postings.extend(batch)
        if len(batch) < PAGE or len(postings) >= (total or 0):
            break

    return {"endpoint": url, "total": total or 0, "jobPostings": postings}


def _posted_date(posted_on: str, run_date: str) -> str:
    """Resolve Workday's relative posting phrase into a UTC date.

    "Posted 30+ Days Ago" only sets a lower bound, so it is left empty rather
    than recorded as a date the board did not actually give.
    """
    if not posted_on:
        return ""
    text = posted_on.strip()
    low = text.lower()
    run = date.fromisoformat(run_date)

    if "today" in low:
        return run.isoformat()
    if "yesterday" in low:
        return (run - timedelta(days=1)).isoformat()
    if "+" in text:
        return ""
    match = _DAYS_AGO.search(low)
    if match:
        return (run - timedelta(days=int(match.group(1)))).isoformat()
    return ""


def _source_id(posting: dict, path: str) -> str:
    """The board's own ID for a posting.

    ``bulletFields`` carries the requisition number, which is what stays put
    when an employer edits a posting. The ``externalPath`` slug embeds the
    title, so keying on it would read an edited title as a removal plus a new
    posting; it is only a fallback for boards that leave bulletFields empty.
    """
    bullets = posting.get("bulletFields") or []
    for bullet in bullets:
        value = str(bullet or "").strip()
        if value:
            return value
    return path.rstrip("/").rsplit("/", 1)[-1]


def normalize(source: dict, raw: dict) -> list[dict]:
    run_date = raw["run_date"]
    payload = raw["payload"]
    site = source["site"]
    base = (
        f"https://{source['tenant']}.{source['host']}.myworkdayjobs.com"
        f"/en-US/{site}"
    )

    rows = []
    for posting in payload.get("jobPostings") or []:
        path = posting.get("externalPath") or ""
        source_id = _source_id(posting, path)
        if not source_id:
            continue
        rows.append(
            {
                "source_id": source_id,
                "title": (posting.get("title") or "").strip(),
                "location": (posting.get("locationsText") or "").strip(),
                "department": "",
                "posted_date": _posted_date(posting.get("postedOn") or "", run_date),
                "url": base + path,
            }
        )
    return rows
