"""Converting each source's payload into the common columns.

The payloads below are trimmed copies of what each board actually returned, so
these tests pin the field mapping for every applicant tracking system on the
watch list.
"""

from jobwatcher.adapters import amazon, for_source, oracle, workday

WORKDAY_SOURCE = {
    "name": "federal_reserve",
    "employer": "Federal Reserve System",
    "ats": "Workday",
    "kind": "workday",
    "tenant": "rb",
    "host": "wd5",
    "site": "FRS",
}

WORKDAY_RAW = {
    "source": "federal_reserve",
    "employer": "Federal Reserve System",
    "kind": "workday",
    "run_date": "2026-11-17",
    "payload": {
        "total": 148,
        "jobPostings": [
            {
                "title": "Senior Credit Risk and Reserves Analyst",
                "externalPath": "/job/Dallas-TX/Senior-Credit-Risk-and-Reserves"
                                "-Analyst_R-0000034068",
                "locationsText": "Dallas, TX",
                "postedOn": "Posted 5 Days Ago",
                "bulletFields": ["R-0000034068"],
            },
            {
                "title": "Operations Associate",
                "externalPath": "/job/Houston-TX/Operations-Associate_R-0000034075",
                "locationsText": "Houston, TX",
                "postedOn": "Posted Today",
                "bulletFields": [],
            },
        ],
    },
}


def test_workday_maps_the_common_columns():
    rows = workday.normalize(WORKDAY_SOURCE, WORKDAY_RAW)
    assert len(rows) == 2

    first = rows[0]
    assert first["source_id"] == "R-0000034068"
    assert first["title"] == "Senior Credit Risk and Reserves Analyst"
    assert first["location"] == "Dallas, TX"
    assert first["posted_date"] == "2026-11-12"
    assert first["url"] == (
        "https://rb.wd5.myworkdayjobs.com/en-US/FRS"
        "/job/Dallas-TX/Senior-Credit-Risk-and-Reserves-Analyst_R-0000034068"
    )
    # Workday does not give a department on the search endpoint.
    assert first["department"] == ""


def test_workday_falls_back_to_the_path_when_bulletfields_is_empty():
    rows = workday.normalize(WORKDAY_SOURCE, WORKDAY_RAW)
    assert rows[1]["source_id"] == "Operations-Associate_R-0000034075"


def test_workday_resolves_relative_posting_dates():
    assert workday._posted_date("Posted Today", "2026-11-17") == "2026-11-17"
    assert workday._posted_date("Posted Yesterday", "2026-11-17") == "2026-11-16"
    assert workday._posted_date("Posted 5 Days Ago", "2026-11-17") == "2026-11-12"


def test_workday_leaves_an_open_ended_posting_date_empty():
    """"Posted 30+ Days Ago" is a lower bound, not a date."""
    assert workday._posted_date("Posted 30+ Days Ago", "2026-11-17") == ""
    assert workday._posted_date("", "2026-11-17") == ""


AMAZON_SOURCE = {
    "name": "amazon",
    "employer": "Amazon",
    "ats": "Amazon Jobs (in-house)",
    "kind": "amazon",
    "search_text": "analyst",
}

AMAZON_RAW = {
    "source": "amazon",
    "run_date": "2026-11-17",
    "payload": {
        "hits": 683,
        "jobs": [
            {
                "id_icims": "10606935",
                "title": "Sr. Compliance Associate-Quality Analyst",
                "normalized_location": "Pune, Maharashtra, IND",
                "job_category": "Fulfillment & Operations Management",
                "posted_date": "November 14, 2026",
                "job_path": "/en/jobs/10606935/sr-compliance-associate",
            }
        ],
    },
}


def test_amazon_maps_the_common_columns():
    (row,) = amazon.normalize(AMAZON_SOURCE, AMAZON_RAW)
    assert row["source_id"] == "10606935"
    assert row["title"] == "Sr. Compliance Associate-Quality Analyst"
    assert row["location"] == "Pune, Maharashtra, IND"
    assert row["department"] == "Fulfillment & Operations Management"
    assert row["posted_date"] == "2026-11-14"
    assert row["url"] == (
        "https://www.amazon.jobs/en/jobs/10606935/sr-compliance-associate"
    )


def test_amazon_leaves_an_unparseable_posting_date_empty():
    assert amazon._posted_date("not a date") == ""
    assert amazon._posted_date("") == ""


ORACLE_SOURCE = {
    "name": "jpmorgan_chase",
    "employer": "JPMorgan Chase",
    "ats": "Oracle Recruiting Cloud",
    "kind": "oracle",
    "host": "jpmc.fa.oraclecloud.com",
    "site_number": "CX_1001",
    "search_text": "analyst",
}

ORACLE_RAW = {
    "source": "jpmorgan_chase",
    "run_date": "2026-11-17",
    "payload": {
        "total": 997,
        "requisitionList": [
            {
                "Id": "210617464",
                "Title": "U.S. Private Bank - Client Service Associate",
                "PrimaryLocation": "Chicago, Illinois, United States",
                "JobFamily": "Client Service",
                "PostedDate": "2026-11-17",
            }
        ],
    },
}


def test_oracle_maps_the_common_columns():
    (row,) = oracle.normalize(ORACLE_SOURCE, ORACLE_RAW)
    assert row["source_id"] == "210617464"
    assert row["title"] == "U.S. Private Bank - Client Service Associate"
    assert row["location"] == "Chicago, Illinois, United States"
    assert row["department"] == "Client Service"
    assert row["posted_date"] == "2026-11-17"
    assert row["url"].endswith("/sites/CX_1001/job/210617464")


def test_every_adapter_returns_the_same_keys():
    """One common set of columns, whatever the board."""
    expected = {
        "source_id", "title", "location", "department", "posted_date", "url",
    }
    for source, raw in (
        (WORKDAY_SOURCE, WORKDAY_RAW),
        (AMAZON_SOURCE, AMAZON_RAW),
        (ORACLE_SOURCE, ORACLE_RAW),
    ):
        for row in for_source(source).normalize(source, raw):
            assert set(row) == expected


def test_postings_without_an_id_are_dropped():
    raw = {
        "source": "federal_reserve",
        "run_date": "2026-11-17",
        "payload": {"jobPostings": [{"title": "No id", "externalPath": ""}]},
    }
    assert workday.normalize(WORKDAY_SOURCE, raw) == []
