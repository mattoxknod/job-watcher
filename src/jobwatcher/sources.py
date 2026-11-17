"""The watch list.

Every source returns JSON to an unauthenticated request. ``kind`` picks the
adapter in :mod:`jobwatcher.adapters` that knows how to page the board and how
to turn its payload into the common columns.

Workday boards are addressed by ``tenant``, ``host`` and ``site``; the public
endpoint is::

    https://{tenant}.{host}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs

``search_text`` is sent to boards that would otherwise return more than the
5,000 postings the project allows; it is empty for every other board.
"""

SOURCES = [
    # ---- Workday -------------------------------------------------------
    {
        "name": "walmart",
        "employer": "Walmart",
        "ats": "Workday",
        "kind": "workday",
        "tenant": "walmart",
        "host": "wd504",
        "site": "WalmartExternal",
    },
    {
        "name": "bank_of_america",
        "employer": "Bank of America",
        "ats": "Workday",
        "kind": "workday",
        "tenant": "ghr",
        "host": "wd1",
        "site": "lateral-us",
    },
    {
        "name": "citi",
        "employer": "Citi",
        "ats": "Workday",
        "kind": "workday",
        "tenant": "citi",
        "host": "wd5",
        "site": "2",
    },
    {
        "name": "capital_one",
        "employer": "Capital One",
        "ats": "Workday",
        "kind": "workday",
        "tenant": "capitalone",
        "host": "wd12",
        "site": "Capital_One",
    },
    {
        "name": "truist",
        "employer": "Truist",
        "ats": "Workday",
        "kind": "workday",
        "tenant": "truist",
        "host": "wd1",
        "site": "Careers",
    },
    {
        "name": "pnc",
        "employer": "PNC Financial Services",
        "ats": "Workday",
        "kind": "workday",
        "tenant": "pnc",
        "host": "wd5",
        "site": "External",
    },
    {
        "name": "northern_trust",
        "employer": "Northern Trust",
        "ats": "Workday",
        "kind": "workday",
        "tenant": "ntrs",
        "host": "wd1",
        "site": "northerntrust",
    },
    {
        "name": "vanguard",
        "employer": "The Vanguard Group",
        "ats": "Workday",
        "kind": "workday",
        "tenant": "vanguard",
        "host": "wd5",
        "site": "vanguard_external",
    },
    {
        "name": "federal_reserve",
        "employer": "Federal Reserve System",
        "ats": "Workday",
        "kind": "workday",
        "tenant": "rb",
        "host": "wd5",
        "site": "FRS",
    },
    {
        "name": "tyson_foods",
        "employer": "Tyson Foods",
        "ats": "Workday",
        "kind": "workday",
        "tenant": "tysonfoods",
        "host": "wd5",
        "site": "TSN",
    },
    {
        "name": "jb_hunt",
        "employer": "J.B. Hunt Transport Services",
        "ats": "Workday",
        "kind": "workday",
        "tenant": "jbhunt",
        "host": "wd501",
        "site": "Careers",
    },
    {
        "name": "coca_cola",
        "employer": "The Coca-Cola Company",
        "ats": "Workday",
        "kind": "workday",
        "tenant": "coke",
        "host": "wd1",
        "site": "coca-cola-careers",
    },
    {
        "name": "acxiom",
        "employer": "Acxiom",
        "ats": "Workday",
        "kind": "workday",
        "tenant": "acxiomllc",
        "host": "wd5",
        "site": "AcxiomUSA",
    },
    {
        "name": "fedex",
        "employer": "FedEx",
        "ats": "Workday",
        "kind": "workday",
        "tenant": "fedex",
        "host": "wd1",
        "site": "FXE-MEISA-External",
    },
    # ---- Other applicant tracking systems ------------------------------
    {
        "name": "amazon",
        "employer": "Amazon",
        "ats": "Amazon Jobs (in-house)",
        "kind": "amazon",
        # Amazon's board is far larger than 5,000 postings, so it is read with
        # a search term. See the README.
        "search_text": "analyst",
    },
    {
        "name": "jpmorgan_chase",
        "employer": "JPMorgan Chase",
        "ats": "Oracle Recruiting Cloud",
        "kind": "oracle",
        "host": "jpmc.fa.oraclecloud.com",
        "site_number": "CX_1001",
        # The full board runs past 5,000 postings, so it is read with a search
        # term. See the README.
        "search_text": "analyst",
    },
]

BY_NAME = {s["name"]: s for s in SOURCES}


def all_sources():
    """Return the watch list in a stable order."""
    return list(SOURCES)
