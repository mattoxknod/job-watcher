"""Oracle Recruiting Cloud boards, read through the public ``hcmRestApi``.

The requisition search is paged with ``limit`` and ``offset`` inside the
``finder`` expression and reports ``TotalJobsCount``.
"""

from __future__ import annotations

from jobwatcher.http import get_json

PAGE = 200
MAX_PAGES = 40


def endpoint(source: dict) -> str:
    return (
        f"https://{source['host']}"
        "/hcmRestApi/resources/latest/recruitingCEJobRequisitions"
    )


def _finder(source: dict, offset: int) -> str:
    parts = [
        f"siteNumber={source['site_number']}",
        f"limit={PAGE}",
        f"offset={offset}",
        "sortBy=POSTING_DATES_DESC",
    ]
    if source.get("search_text"):
        parts.insert(1, f"keyword={source['search_text']}")
    return "findReqs;" + ",".join(parts)


def fetch(source: dict) -> dict:
    url = endpoint(source)
    requisitions: list[dict] = []
    total = None

    for page in range(MAX_PAGES):
        data = get_json(
            url,
            params={
                "onlyData": "true",
                "expand": "requisitionList",
                "finder": _finder(source, page * PAGE),
            },
        )
        items = data.get("items") or []
        if not items:
            break
        block = items[0]
        if total is None:
            total = block.get("TotalJobsCount", 0)
        batch = block.get("requisitionList") or []
        requisitions.extend(batch)
        if len(batch) < PAGE or len(requisitions) >= (total or 0):
            break

    return {"endpoint": url, "total": total or 0, "requisitionList": requisitions}


def normalize(source: dict, raw: dict) -> list[dict]:
    host = source["host"]
    rows = []
    for req in raw["payload"].get("requisitionList") or []:
        source_id = str(req.get("Id") or "").strip()
        if not source_id:
            continue
        rows.append(
            {
                "source_id": source_id,
                "title": (req.get("Title") or "").strip(),
                "location": (req.get("PrimaryLocation") or "").strip(),
                "department": (req.get("JobFamily") or "").strip(),
                "posted_date": (req.get("PostedDate") or "").strip(),
                "url": (
                    f"https://{host}/hcmUI/CandidateExperience/en/sites/"
                    f"{source['site_number']}/job/{source_id}"
                ),
            }
        )
    return rows
