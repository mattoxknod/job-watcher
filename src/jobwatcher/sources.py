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
        "domain": "walmart.com",
        "employer": "Walmart",
        "ats": "Workday",
        "kind": "workday",
        "tenant": "walmart",
        "host": "wd504",
        "site": "WalmartExternal",
    },
    {
        "name": "bank_of_america",
        "domain": "bankofamerica.com",
        "employer": "Bank of America",
        "ats": "Workday",
        "kind": "workday",
        "tenant": "ghr",
        "host": "wd1",
        "site": "lateral-us",
    },
    {
        "name": "citi",
        "domain": "citi.com",
        "employer": "Citi",
        "ats": "Workday",
        "kind": "workday",
        "tenant": "citi",
        "host": "wd5",
        "site": "2",
    },
    {
        "name": "capital_one",
        "domain": "capitalone.com",
        "employer": "Capital One",
        "ats": "Workday",
        "kind": "workday",
        "tenant": "capitalone",
        "host": "wd12",
        "site": "Capital_One",
    },
    {
        "name": "truist",
        "domain": "truist.com",
        "employer": "Truist",
        "ats": "Workday",
        "kind": "workday",
        "tenant": "truist",
        "host": "wd1",
        "site": "Careers",
    },
    {
        "name": "pnc",
        "domain": "pnc.com",
        "employer": "PNC Financial Services",
        "ats": "Workday",
        "kind": "workday",
        "tenant": "pnc",
        "host": "wd5",
        "site": "External",
    },
    {
        "name": "northern_trust",
        "domain": "northerntrust.com",
        "employer": "Northern Trust",
        "ats": "Workday",
        "kind": "workday",
        "tenant": "ntrs",
        "host": "wd1",
        "site": "northerntrust",
    },
    {
        "name": "vanguard",
        "domain": "vanguard.com",
        "employer": "The Vanguard Group",
        "ats": "Workday",
        "kind": "workday",
        "tenant": "vanguard",
        "host": "wd5",
        "site": "vanguard_external",
    },
    {
        "name": "federal_reserve",
        "domain": "federalreserve.gov",
        "employer": "Federal Reserve System",
        "ats": "Workday",
        "kind": "workday",
        "tenant": "rb",
        "host": "wd5",
        "site": "FRS",
    },
    {
        "name": "tyson_foods",
        "domain": "tyson.com",
        "employer": "Tyson Foods",
        "ats": "Workday",
        "kind": "workday",
        "tenant": "tysonfoods",
        "host": "wd5",
        "site": "TSN",
    },
    {
        "name": "jb_hunt",
        "domain": "jbhunt.com",
        "employer": "J.B. Hunt Transport Services",
        "ats": "Workday",
        "kind": "workday",
        "tenant": "jbhunt",
        "host": "wd501",
        "site": "Careers",
    },
    {
        "name": "coca_cola",
        "domain": "coca-colacompany.com",
        "employer": "The Coca-Cola Company",
        "ats": "Workday",
        "kind": "workday",
        "tenant": "coke",
        "host": "wd1",
        "site": "coca-cola-careers",
    },
    {
        "name": "acxiom",
        "domain": "acxiom.com",
        "employer": "Acxiom",
        "ats": "Workday",
        "kind": "workday",
        "tenant": "acxiomllc",
        "host": "wd5",
        "site": "AcxiomUSA",
    },
    # Added for Little Rock and Northwest Arkansas, which the national
    # employers above barely cover.
    {
        "name": "arkansas_childrens",
        "domain": "archildrens.org",
        "employer": "Arkansas Children's",
        "ats": "Workday",
        "kind": "workday",
        "tenant": "archildrens",
        "host": "wd1",
        "site": "external_career_site",
    },
    {
        "name": "university_of_arkansas",
        "domain": "uark.edu",
        "employer": "University of Arkansas System",
        "ats": "Workday",
        "kind": "workday",
        "tenant": "uasys",
        "host": "wd5",
        "site": "UASYS",
    },
    {
        "name": "simmons_bank",
        "domain": "simmonsbank.com",
        "employer": "Simmons Bank",
        "ats": "Workday",
        "kind": "workday",
        "tenant": "simmonsbank",
        "host": "wd5",
        "site": "SimmonsCareers",
    },
    # Manufacturers with Arkansas plants. These carry the mechanical
    # engineering work the finance-led list above does not.
    {
        "name": "trane_technologies",
        "domain": "tranetechnologies.com",
        "employer": "Trane Technologies",
        "ats": "Workday",
        "kind": "workday",
        "tenant": "tranetechnologies",
        "host": "wd12",
        "site": "Trane_Technologies_Careers",
    },
    {
        "name": "kimberly_clark",
        "domain": "kimberly-clark.com",
        "employer": "Kimberly-Clark",
        "ats": "Workday",
        "kind": "workday",
        "tenant": "kimberlyclark",
        "host": "wd1",
        "site": "GLOBAL",
    },
    {
        "name": "zekelman",
        "domain": "zekelman.com",
        "employer": "Zekelman Industries",
        "ats": "Workday",
        "kind": "workday",
        "tenant": "zekelman",
        "host": "wd12",
        "site": "Careers",
    },
    {
        "name": "simmons_foods",
        "domain": "simmonsfoods.com",
        "employer": "Simmons Foods",
        "ats": "Workday",
        "kind": "workday",
        "tenant": "simmons",
        "host": "wd504",
        "site": "Simmons-Careers",
    },
    {
        "name": "fedex",
        "domain": "fedex.com",
        "employer": "FedEx",
        "ats": "Workday",
        "kind": "workday",
        "tenant": "fedex",
        "host": "wd1",
        "site": "FXE-MEISA-External",
    },
    # More of the same kinds of employer: asset managers and a digital bank
    # alongside the banks above, two food manufacturers alongside Tyson.
    {
        "name": "state_street",
        "domain": "statestreet.com",
        "employer": "State Street",
        "ats": "Workday",
        "kind": "workday",
        "tenant": "statestreet",
        "host": "wd1",
        "site": "Global",
    },
    {
        "name": "blackrock",
        "domain": "blackrock.com",
        "employer": "BlackRock",
        "ats": "Workday",
        "kind": "workday",
        "tenant": "blackrock",
        "host": "wd1",
        "site": "BlackRock_Professional",
    },
    {
        "name": "ally",
        "domain": "ally.com",
        "employer": "Ally Financial",
        "ats": "Workday",
        "kind": "workday",
        "tenant": "ally",
        "host": "wd1",
        "site": "Ally",
    },
    {
        "name": "general_mills",
        "domain": "generalmills.com",
        "employer": "General Mills",
        "ats": "Workday",
        "kind": "workday",
        "tenant": "genmills",
        "host": "wd1",
        "site": "GMI_External_Careers",
    },
    {
        "name": "smithfield",
        "domain": "smithfieldfoods.com",
        "employer": "Smithfield Foods",
        "ats": "Workday",
        "kind": "workday",
        "tenant": "smithfieldfoods",
        "host": "wd1",
        "site": "Careers",
    },
    # ---- Other applicant tracking systems ------------------------------
    {
        "name": "amazon",
        "domain": "amazon.com",
        "employer": "Amazon",
        "ats": "Amazon Jobs (in-house)",
        "kind": "amazon",
        # Amazon's board is far larger than 5,000 postings, so it is read with
        # a search term. See the README.
        "search_text": "analyst",
    },
    {
        "name": "jpmorgan_chase",
        "domain": "jpmorganchase.com",
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
