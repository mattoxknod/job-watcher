"""The first-seen, last-seen and removed logic."""

from jobwatcher.history import COLUMNS, build_history, read_history, write_history


def posting(source_id, title="Financial Analyst", location="Dallas, TX"):
    return {
        "source_id": source_id,
        "employer": "Test Employer",
        "title": title,
        "location": location,
        "department": "",
        "posted_date": "",
        "url": f"https://example.test/{source_id}",
    }


def rows_by_id(rows):
    return {r["posting_id"]: r for r in rows}


def test_a_new_posting_gets_that_day_as_first_seen():
    rows = rows_by_id(build_history([
        ("2026-11-01", {"acme": [posting("1")]}),
        ("2026-11-02", {"acme": [posting("1"), posting("2")]}),
    ]))
    assert rows["acme:2"]["first_seen"] == "2026-11-02"
    assert rows["acme:2"]["last_seen"] == "2026-11-02"
    assert rows["acme:2"]["status"] == "open"


def test_last_seen_advances_while_the_source_keeps_listing_it():
    rows = rows_by_id(build_history([
        ("2026-11-01", {"acme": [posting("1")]}),
        ("2026-11-02", {"acme": [posting("1")]}),
        ("2026-11-03", {"acme": [posting("1")]}),
    ]))
    assert rows["acme:1"]["first_seen"] == "2026-11-01"
    assert rows["acme:1"]["last_seen"] == "2026-11-03"


def test_a_posting_its_source_stops_listing_is_removed_that_day():
    rows = rows_by_id(build_history([
        ("2026-11-01", {"acme": [posting("1"), posting("2")]}),
        ("2026-11-02", {"acme": [posting("1")]}),
    ]))
    assert rows["acme:2"]["status"] == "removed"
    assert rows["acme:2"]["removed_date"] == "2026-11-02"
    # Its last_seen stays on the last day the source actually listed it.
    assert rows["acme:2"]["last_seen"] == "2026-11-01"
    assert rows["acme:1"]["status"] == "open"


def test_a_relisted_posting_reopens_and_keeps_its_first_seen():
    rows = rows_by_id(build_history([
        ("2026-11-01", {"acme": [posting("1")]}),
        ("2026-11-02", {"acme": []}),
        ("2026-11-03", {"acme": [posting("1")]}),
    ]))
    row = rows["acme:1"]
    assert row["status"] == "open"
    assert row["removed_date"] == ""
    assert row["first_seen"] == "2026-11-01"
    assert row["last_seen"] == "2026-11-03"


def test_a_failed_source_removes_nothing():
    """No raw file that day means the day says nothing about that source."""
    rows = rows_by_id(build_history([
        ("2026-11-01", {"acme": [posting("1")], "other": [posting("9")]}),
        # acme failed, so it is absent; only "other" reported.
        ("2026-11-02", {"other": [posting("9")]}),
    ]))
    assert rows["acme:1"]["status"] == "open"
    assert rows["acme:1"]["removed_date"] == ""
    assert rows["acme:1"]["last_seen"] == "2026-11-01"


def test_one_source_does_not_remove_another_sources_postings():
    rows = rows_by_id(build_history([
        ("2026-11-01", {"acme": [posting("1")], "other": [posting("1")]}),
        ("2026-11-02", {"acme": [], "other": [posting("1")]}),
    ]))
    assert rows["acme:1"]["status"] == "removed"
    assert rows["other:1"]["status"] == "open"


def test_first_run_marks_the_first_raw_file_of_each_source():
    """first_run is per source, so a source added later gets its own baseline."""
    rows = rows_by_id(build_history([
        ("2026-11-01", {"acme": [posting("1")]}),
        ("2026-11-02", {"acme": [posting("1"), posting("2")],
                        "later": [posting("7")]}),
    ]))
    assert rows["acme:1"]["first_run"] is True
    assert rows["acme:2"]["first_run"] is False
    assert rows["later:7"]["first_run"] is True


def test_rows_are_sorted_by_posting_id():
    rows = build_history([
        ("2026-11-01", {"zeta": [posting("2"), posting("1")],
                        "alpha": [posting("3")]}),
    ])
    ids = [r["posting_id"] for r in rows]
    assert ids == sorted(ids)
    assert ids == ["alpha:3", "zeta:1", "zeta:2"]


def test_posting_id_is_the_source_and_the_sources_own_id():
    (row,) = build_history([("2026-11-01", {"acme": [posting("R-123")]})])
    assert row["posting_id"] == "acme:R-123"
    assert row["source"] == "acme"
    assert row["source_id"] == "R-123"


def test_the_build_is_reproducible():
    days = [
        ("2026-11-01", {"acme": [posting("1"), posting("2")]}),
        ("2026-11-02", {"acme": [posting("1")]}),
        ("2026-11-03", {"acme": [posting("1"), posting("2")]}),
    ]
    assert build_history(days) == build_history(days)


def test_an_edited_posting_keeps_its_row_and_shows_the_latest_fields():
    rows = rows_by_id(build_history([
        ("2026-11-01", {"acme": [posting("1", title="Credit Analyst")]}),
        ("2026-11-02", {"acme": [posting("1", title="Senior Credit Analyst",
                                        location="Little Rock, AR")]}),
    ]))
    assert len(rows) == 1
    assert rows["acme:1"]["title"] == "Senior Credit Analyst"
    assert rows["acme:1"]["location"] == "Little Rock, AR"
    assert rows["acme:1"]["first_seen"] == "2026-11-01"


def test_in_role_is_set_from_the_title_rule():
    rows = rows_by_id(build_history([
        ("2026-11-01", {"acme": [posting("1", title="Financial Analyst"),
                                 posting("2", title="Truck Driver")]}),
    ]))
    assert rows["acme:1"]["in_role"] is True
    assert rows["acme:2"]["in_role"] is False


def test_history_survives_a_write_and_read_round_trip(tmp_path):
    rows = build_history([
        ("2026-11-01", {"acme": [posting("1"), posting("2")]}),
        ("2026-11-02", {"acme": [posting("1")]}),
    ])
    path = tmp_path / "history.csv"
    write_history(rows, path)

    header = path.read_text(encoding="utf-8").splitlines()[0]
    assert header.split(",") == COLUMNS

    back = read_history(path)
    assert [r["posting_id"] for r in back] == [r["posting_id"] for r in rows]
    assert back[0]["in_role"] is True
    assert back[0]["first_run"] is True
    assert back[1]["status"] == "removed"
    assert back[1]["removed_date"] == "2026-11-02"
