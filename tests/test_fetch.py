"""The fetch step: failures are recorded, and a run survives them."""

import json

from jobwatcher import fetch as fetch_mod
from jobwatcher import store
from jobwatcher.http import FetchError

SOURCE = {
    "name": "fake",
    "employer": "Fake Employer",
    "ats": "Workday",
    "kind": "workday",
    "tenant": "fake",
    "host": "wd1",
    "site": "External",
}

POSTING = {
    "title": "Financial Analyst",
    "externalPath": "/job/Dallas-TX/Financial-Analyst_R-1",
    "locationsText": "Dallas, TX",
    "postedOn": "Posted Today",
    "bulletFields": ["R-1"],
}


def fake_adapter(monkeypatch, payload=None, error=None):
    from jobwatcher.adapters import workday

    def fetch(source):
        if error:
            raise error
        return payload

    monkeypatch.setattr(workday, "fetch", fetch)


def test_a_successful_source_writes_a_raw_file(monkeypatch, tmp_path):
    fake_adapter(monkeypatch, payload={"total": 1, "jobPostings": [POSTING]})

    result = fetch_mod.fetch_source(SOURCE, "2026-11-17", tmp_path)

    assert result["ok"] is True
    assert result["count"] == 1
    path = store.raw_path("2026-11-17", "fake", tmp_path)
    assert path.exists()
    assert store.read_raw(path)["run_date"] == "2026-11-17"


def test_a_failing_source_is_recorded_and_writes_no_raw_file(monkeypatch, tmp_path):
    fake_adapter(monkeypatch, error=FetchError("429 Too Many Requests"))

    result = fetch_mod.fetch_source(SOURCE, "2026-11-17", tmp_path)

    assert result["ok"] is False
    assert result["count"] == 0
    assert "429" in result["error"]
    # No raw file is what stops the build from marking its postings removed.
    assert not store.raw_path("2026-11-17", "fake", tmp_path).exists()


def test_a_board_that_returns_nothing_counts_as_a_failed_read(monkeypatch, tmp_path):
    fake_adapter(monkeypatch, payload={"total": 0, "jobPostings": []})

    result = fetch_mod.fetch_source(SOURCE, "2026-11-17", tmp_path)

    assert result["ok"] is False
    assert not store.raw_path("2026-11-17", "fake", tmp_path).exists()


def test_one_failing_source_does_not_stop_the_run(monkeypatch, tmp_path):
    from jobwatcher.adapters import workday

    calls = []

    def fetch(source):
        calls.append(source["name"])
        if source["name"] == "bad":
            raise FetchError("boom")
        return {"total": 1, "jobPostings": [POSTING]}

    monkeypatch.setattr(workday, "fetch", fetch)

    sources = [
        {**SOURCE, "name": "bad"},
        {**SOURCE, "name": "good"},
    ]
    log = fetch_mod.run(sources, "2026-11-17", tmp_path)

    assert calls == ["bad", "good"]
    assert [s["ok"] for s in log["sources"]] == [False, True]

    # Every source's result, success or failure, is written down.
    written = json.loads(
        (store.day_dir("2026-11-17", tmp_path) / store.RUN_LOG).read_text()
    )
    assert {s["name"] for s in written["sources"]} == {"bad", "good"}
