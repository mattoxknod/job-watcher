"""Turning a board's location text into one region.

Every board writes locations differently - "Dallas, TX", "US - GA - Atlanta",
"USA-AR-FORT-SMITH-08134-SAMS-CLUB", "Bellevue, Washington, USA", "Conway",
"Remote/Homebased", "2 Locations" - so the region is worked out from the text
rather than taken from a field none of them share.

Three regions are primary, because they are the ones this watch is aimed at:

    Northwest Arkansas   Fayetteville, Bentonville, Rogers, Springdale
    Little Rock          Little Rock and central Arkansas
    Dallas-Fort Worth    the DFW metroplex

Everything else falls back to its US state, then to Remote, Multiple locations,
International or Other. The rule reads the location text only, so it gives the
same answer for every day of the history.
"""

from __future__ import annotations

import re

NORTHWEST_ARKANSAS = "Northwest Arkansas"
LITTLE_ROCK = "Little Rock"
DALLAS_FORT_WORTH = "Dallas-Fort Worth"

#: The three regions this watch is aimed at, in the order they are offered.
PRIMARY_REGIONS = [NORTHWEST_ARKANSAS, LITTLE_ROCK, DALLAS_FORT_WORTH]

REMOTE = "Remote"
MULTIPLE = "Multiple locations"
INTERNATIONAL = "International"
OTHER_US = "Other U.S."
OTHER = "Other"
UNKNOWN = "Unknown"

US_STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut",
    "DE": "Delaware", "DC": "District of Columbia", "FL": "Florida",
    "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois",
    "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky",
    "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana",
    "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire",
    "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania",
    "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota",
    "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont",
    "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming", "PR": "Puerto Rico",
}

_STATE_NAMES = {name.lower(): name for name in US_STATES.values()}

#: Cities in each primary region. These are consulted once the state is known
#: to be Arkansas or Texas, so a name shared with another state is safe here.
NWA_CITIES = (
    "bentonville", "springdale", "rogers", "fayetteville", "bella vista",
    "siloam springs", "centerton", "lowell", "farmington", "pea ridge",
    "gravette", "prairie grove", "tontitown", "elm springs", "johnson",
    "cave springs", "west fork", "greenland", "huntsville",
)

LITTLE_ROCK_CITIES = (
    "little rock", "maumelle", "sherwood", "jacksonville", "cabot",
    "benton", "bryant", "conway", "searcy", "white hall", "alexander",
    "mabelvale", "pulaski", "saline", "lonoke", "greenbrier", "vilonia",
)

DFW_CITIES = (
    "dallas", "fort worth", "ft worth", "ft. worth", "plano", "irving",
    "richardson", "frisco", "addison", "grapevine", "garland", "mckinney",
    "carrollton", "lewisville", "las colinas", "arlington", "denton",
    "allen", "coppell", "farmers branch", "dfw", "euless", "bedford",
    "flower mound", "mansfield", "rockwall", "southlake", "westlake",
    "the colony", "grand prairie", "duncanville", "desoto", "cedar hill",
)

#: Cities distinctive enough to place on their own when a board names no state
#: at all, as Acxiom's board does when it writes just "Conway".
BARE_CITIES = {
    NORTHWEST_ARKANSAS: (
        "bentonville", "springdale", "bella vista", "siloam springs",
        "centerton", "tontitown", "pea ridge", "cave springs",
    ),
    LITTLE_ROCK: (
        "little rock", "north little rock", "maumelle", "conway",
        "mabelvale",
    ),
    DALLAS_FORT_WORTH: (
        "dallas", "fort worth", "las colinas", "dfw",
    ),
}

_REMOTE = re.compile(
    r"\bremote\b|\bhome[\s-]?based\b|\bvirtual\b|\bwork from home\b|"
    r"\btelecommute\b|remotehomebased",
    re.I,
)

#: Workday collapses a posting listed in several places into "2 Locations".
_MULTIPLE = re.compile(r"^\s*\d+\s+locations?\s*$", re.I)

#: A trailing three-letter country code, as Amazon writes "Pune, …, IND".
_COUNTRY_CODE = re.compile(r"\b([A-Z]{3})\b")

_US_MARKER = re.compile(r"\b(usa|u\.s\.a?\.?|united states|us)\b", re.I)

#: Most boards name the country in words rather than as a code. Only countries
#: that actually turn up on these boards are listed. Names that are also US
#: states, Georgia above all, are safe here because the state check runs first.
COUNTRIES = (
    "india", "canada", "united kingdom", "great britain", "england",
    "scotland", "wales", "northern ireland", "ireland", "singapore",
    "mexico", "brazil", "argentina", "chile", "colombia", "peru",
    "costa rica", "panama", "china", "hong kong", "japan", "south korea",
    "korea", "taiwan", "philippines", "malaysia", "indonesia", "thailand",
    "vietnam", "australia", "new zealand", "germany", "france", "spain",
    "portugal", "italy", "netherlands", "belgium", "luxembourg",
    "switzerland", "austria", "poland", "czech", "hungary", "romania",
    "bulgaria", "sweden", "norway", "denmark", "finland", "israel",
    "turkey", "united arab emirates", "saudi arabia", "qatar", "egypt",
    "south africa", "nigeria", "kenya", "morocco", "jordan", "bahrain",
    "puerto rico", "dominican republic", "guatemala", "uruguay", "ecuador",
)

#: Canadian provinces, which otherwise look like US state codes.
_CA_PROVINCES = {"ON", "QC", "BC", "AB", "MB", "SK", "NS", "NB", "NL", "PE"}

#: Bare US cities worth placing when a board names no state. Kept short on
#: purpose: each one has to be distinctive enough to be unambiguous.
BARE_US_CITIES = (
    "charlotte", "atlanta", "chicago", "boston", "seattle", "denver",
    "phoenix", "philadelphia", "pittsburgh", "minneapolis", "milwaukee",
    "cleveland", "cincinnati", "columbus", "indianapolis", "nashville",
    "memphis", "louisville", "kansas city", "st. louis", "saint louis",
    "new orleans", "tampa", "orlando", "miami", "jacksonville",
    "san francisco", "los angeles", "san diego", "san jose", "portland",
    "salt lake city", "las vegas", "omaha", "des moines", "richmond",
    "baltimore", "pittsburgh", "buffalo", "hartford", "providence",
)


def _tokens(text: str) -> list[str]:
    return re.split(r"[^A-Za-z.]+", text)


def us_state(location: str) -> str | None:
    """The US state a location names, or None.

    A two-letter code only counts when the board wrote it in capitals, so
    "Columbus, IN" reads as Indiana while an ordinary word does not.
    """
    lowered = location.lower()
    for name, proper in _STATE_NAMES.items():
        if re.search(rf"\b{re.escape(name)}\b", lowered):
            return proper

    for token in _tokens(location):
        if len(token) == 2 and token.isupper() and token in US_STATES:
            return US_STATES[token]
    return None


def _matches(lowered: str, cities: tuple[str, ...]) -> bool:
    return any(re.search(rf"\b{re.escape(city)}\b", lowered) for city in cities)


def region_of(location: str) -> str:
    """Return the one region a location belongs to."""
    if not location or not location.strip():
        return UNKNOWN

    text = location.strip()
    lowered = text.lower()

    if _MULTIPLE.match(text):
        return MULTIPLE
    if _REMOTE.search(lowered):
        return REMOTE

    state = us_state(text)

    if state == "Arkansas":
        if _matches(lowered, NWA_CITIES):
            return NORTHWEST_ARKANSAS
        if _matches(lowered, LITTLE_ROCK_CITIES):
            return LITTLE_ROCK
        return "Arkansas"

    if state == "Texas":
        if _matches(lowered, DFW_CITIES):
            return DALLAS_FORT_WORTH
        return "Texas"

    if state:
        return state

    # No state named: fall back to the handful of cities distinctive enough to
    # place on their own.
    for region, cities in BARE_CITIES.items():
        if _matches(lowered, cities):
            return region

    if _matches(lowered, COUNTRIES):
        return INTERNATIONAL

    if any(token in _CA_PROVINCES for token in _tokens(text) if token.isupper()):
        return INTERNATIONAL

    codes = [c for c in _COUNTRY_CODE.findall(text) if c != "USA"]
    if codes:
        return INTERNATIONAL

    if _matches(lowered, BARE_US_CITIES):
        return OTHER_US

    if _US_MARKER.search(text):
        return OTHER_US

    return OTHER


def is_primary(region: str) -> bool:
    return region in PRIMARY_REGIONS
