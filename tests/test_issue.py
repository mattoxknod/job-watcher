"""The daily issue body.

GitHub rejects a body over 65,536 characters, and a busy day across these
boards moves well over a thousand postings, so the lists have to be capped.
"""

from jobwatcher.issue import BODY_LIMIT, MAX_PER_SECTION, render_body


def posting(i, in_role=True, removed=""):
    return {
        "posting_id": f"src:{i}",
        "source": "src",
        "employer": f"Employer {i % 7}",
        "title": f"Financial Analyst {i}",
        "location": "Dallas, TX",
        "url": f"https://example.test/{i}",
        "in_role": in_role,
        "first_run": False,
        "first_seen": "2026-11-18" if not removed else "2026-11-01",
        "last_seen": "2026-11-18",
        "removed_date": removed,
    }


STATUS = {
    "run_time": "2026-11-18T11:20:00+00:00",
    "first_run_date": "2026-11-17",
    "days_with_success": 2,
    "open": 20294,
    "new_today": 696,
    "removed_today": 607,
    "sources": [{"name": "src", "ok": True, "count": 10}],
    "run_date": "2026-11-18",
}


def test_a_quiet_day_still_gets_a_body():
    body = render_body([], STATUS)
    assert "No new postings today." in body
    assert "No postings removed today." in body


def test_a_normal_day_lists_every_posting():
    rows = [posting(i) for i in range(5)]
    body = render_body(rows, STATUS)
    for i in range(5):
        assert f"https://example.test/{i}" in body
    assert "and" not in body.split("## Removed")[0].split("\n")[-3]


def test_a_busy_day_stays_inside_the_github_limit():
    """1,300 postings at a link each is several times what GitHub accepts."""
    rows = [posting(i) for i in range(700)]
    rows += [posting(1000 + i, removed="2026-11-18") for i in range(600)]

    body = render_body(rows, STATUS)

    assert len(body) <= BODY_LIMIT
    assert "…and" in body


def test_the_counts_are_still_honest_when_the_lists_are_capped():
    rows = [posting(i) for i in range(700)]
    body = render_body(rows, STATUS)
    # The heading reports every new posting, even though not all are listed.
    assert "## New postings (700)" in body
    assert f"…and {700 - MAX_PER_SECTION} more" in body


def test_in_role_postings_survive_the_cap():
    """Whatever the cap cuts should be the least relevant part of the list."""
    rows = [posting(i, in_role=False) for i in range(400)]
    rows += [posting(9000 + i, in_role=True) for i in range(3)]

    body = render_body(rows, STATUS)

    for i in range(3):
        assert f"https://example.test/{9000 + i}" in body


def test_an_enormous_day_still_fits():
    rows = [posting(i) for i in range(20000)]
    body = render_body(rows, STATUS)
    assert len(body) <= BODY_LIMIT
