"""The daily GitHub Issue.

Each run opens an issue titled with its UTC date, listing the new and the
removed postings with a link each, and closes the previous day's issue. The
issue is opened every day, including a day with no changes. A second run on the
same day edits that day's issue instead of opening another, so each day counts
once.
"""

from __future__ import annotations

import os

import requests

from jobwatcher.history import read_history
from jobwatcher.http import TIMEOUT, USER_AGENT
from jobwatcher.store import HISTORY_CSV

API = "https://api.github.com"

#: GitHub refuses an issue body over 65,536 characters with a 422. A busy day
#: across these boards moves well over a thousand postings, which at a link
#: each is several times that, so the lists are capped and the overflow is
#: counted instead. The site shows the full lists.
BODY_LIMIT = 60000

#: Most postings to list in one section before summarising the rest.
MAX_PER_SECTION = 150


def _link(row: dict) -> str:
    employer = row["employer"] or row["source"]
    title = row["title"] or "(untitled)"
    label = f"{employer} - {title}"
    location = row["location"]
    tail = f" - {location}" if location else ""
    role = " **[in role]**" if row["in_role"] else ""
    if row["url"]:
        return f"- [{label}]({row['url']}){tail}{role}"
    return f"- {label}{tail}{role}"


def _section(heading: str, rows: list[dict], empty: str,
             limit: int = MAX_PER_SECTION) -> list[str]:
    lines = [f"## {heading} ({len(rows)})", ""]
    if not rows:
        lines += [empty, ""]
        return lines

    # In-role postings are listed first, so whatever the cap cuts is always
    # the least relevant part of the list.
    in_role = sorted(
        (r for r in rows if r["in_role"]), key=lambda r: (r["employer"], r["title"])
    )
    other = sorted(
        (r for r in rows if not r["in_role"]), key=lambda r: (r["employer"], r["title"])
    )
    ordered = in_role + other

    for row in ordered[:limit]:
        lines.append(_link(row))

    hidden = len(ordered) - limit
    if hidden > 0:
        lines += [
            "",
            f"_…and {hidden} more. The full list is on the site._",
        ]
    lines.append("")
    return lines


def render_body(rows: list[dict], status: dict) -> str:
    """The issue body for the latest run."""
    latest = status.get("first_run_date", "")
    run_date = status.get("run_date") or _latest_date(rows) or latest

    new_rows = [
        r for r in rows if r["first_seen"] == run_date and not r["first_run"]
    ]
    removed_rows = [r for r in rows if r["removed_date"] == run_date]

    ok = [s for s in status.get("sources", []) if s["ok"]]
    failed = [s for s in status.get("sources", []) if not s["ok"]]

    lines = [
        f"Run at {status.get('run_time', '')} UTC.",
        "",
        f"- Open postings: **{status.get('open', 0)}**",
        f"- New today: **{status.get('new_today', 0)}**",
        f"- Removed today: **{status.get('removed_today', 0)}**",
        f"- Days with a successful run: **{status.get('days_with_success', 0)}**",
        f"- Sources read: **{len(ok)}/{len(status.get('sources', []))}**",
        "",
    ]
    if failed:
        lines += ["### Sources that failed", ""]
        lines += [f"- `{s['name']}`" for s in failed]
        lines.append("")

    # Fit inside GitHub's limit: shrink the per-section cap until the whole
    # body fits, rather than letting the API reject the issue outright.
    limit = MAX_PER_SECTION
    while True:
        body = "\n".join(
            lines
            + _section("New postings", new_rows, "No new postings today.", limit)
            + _section(
                "Removed postings", removed_rows, "No postings removed today.", limit
            )
        ).rstrip() + "\n"
        if len(body) <= BODY_LIMIT or limit == 0:
            return body
        limit = 0 if limit <= 10 else limit // 2


def _latest_date(rows: list[dict]) -> str:
    return max((r["last_seen"] for r in rows), default="")


class GitHub:
    """The few GitHub Issue calls this project needs."""

    def __init__(self, repo: str, token: str):
        self.repo = repo
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": USER_AGENT,
            }
        )

    def _call(self, method: str, path: str, **kwargs):
        response = self.session.request(
            method, f"{API}/repos/{self.repo}{path}", timeout=TIMEOUT, **kwargs
        )
        response.raise_for_status()
        return response.json()

    def find_issue(self, title: str) -> dict | None:
        """The most recent issue with this exact title, open or closed."""
        for state in ("open", "closed"):
            issues = self._call(
                "GET", "/issues", params={"state": state, "per_page": 100}
            )
            for issue in issues:
                if issue.get("title") == title and "pull_request" not in issue:
                    return issue
        return None

    def open_issues(self) -> list[dict]:
        issues = self._call("GET", "/issues", params={"state": "open",
                                                      "per_page": 100})
        return [i for i in issues if "pull_request" not in i]

    def create_issue(self, title: str, body: str) -> dict:
        return self._call("POST", "/issues", json={"title": title, "body": body})

    def update_issue(self, number: int, **fields) -> dict:
        return self._call("PATCH", f"/issues/{number}", json=fields)


def publish(run_date: str, rows: list[dict], status: dict,
            repo: str | None = None, token: str | None = None) -> dict:
    """Open or update today's issue and close every earlier daily issue."""
    repo = repo or os.environ.get("GITHUB_REPOSITORY", "")
    token = token or os.environ.get("GITHUB_TOKEN", "")
    if not repo or not token:
        raise RuntimeError("GITHUB_REPOSITORY and GITHUB_TOKEN are required")

    title = f"Job watch {run_date}"
    body = render_body(rows, {**status, "run_date": run_date})
    api = GitHub(repo, token)

    existing = api.find_issue(title)
    if existing:
        issue = api.update_issue(existing["number"], body=body, state="open")
        action = "updated"
    else:
        issue = api.create_issue(title, body)
        action = "created"

    # Close the previous day's issue, and any older one still open.
    closed = []
    for other in api.open_issues():
        other_title = other.get("title", "")
        if other_title.startswith("Job watch ") and other_title < title:
            api.update_issue(other["number"], state="closed")
            closed.append(other["number"])

    print(f"Issue #{issue['number']} {action}: {title}")
    if closed:
        print(f"Closed previous issues: {closed}")
    return {"number": issue["number"], "action": action, "closed": closed}


def load_and_publish(run_date: str) -> dict:
    import json

    from jobwatcher.store import STATUS_JSON

    rows = read_history(HISTORY_CSV)
    status = json.loads(STATUS_JSON.read_text(encoding="utf-8"))
    return publish(run_date, rows, status)
