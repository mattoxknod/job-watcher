"""Turning a board's location text into one region.

The strings here are real ones taken from the boards on the watch list, which
is where the awkward cases come from.
"""

import pytest

from jobwatcher.region import (
    DALLAS_FORT_WORTH,
    INTERNATIONAL,
    LITTLE_ROCK,
    MULTIPLE,
    NORTHWEST_ARKANSAS,
    PRIMARY_REGIONS,
    REMOTE,
    UNKNOWN,
    is_primary,
    region_of,
    us_state,
)


@pytest.mark.parametrize(
    "location",
    [
        "Bentonville, AR",
        "Springdale, AR",
        "Rogers, AR",
        "Fayetteville, AR",
        "Lowell, AR - JB Hunt Corporate B  C",
        "Bella Vista, AR",
        "Siloam Springs, Arkansas",
        "Bentonville",
    ],
)
def test_northwest_arkansas(location):
    assert region_of(location) == NORTHWEST_ARKANSAS


@pytest.mark.parametrize(
    "location",
    [
        "Little Rock, AR",
        "North Little Rock, AR",
        "Maumelle, AR",
        "Conway, Arkansas",
        "Benton, AR",
        "Conway",
        "Maumelle",
    ],
)
def test_little_rock(location):
    assert region_of(location) == LITTLE_ROCK


@pytest.mark.parametrize(
    "location",
    [
        "Dallas, TX",
        "Fort Worth, TX",
        "Plano, Texas",
        "Irving, TX",
        "Frisco, TX",
        "Arlington, TX",
        "Dallas",
    ],
)
def test_dallas_fort_worth(location):
    assert region_of(location) == DALLAS_FORT_WORTH


@pytest.mark.parametrize(
    ("location", "expected"),
    [
        # A city name shared with another state must follow the state, not the
        # city. These are the cases the rule exists to get right.
        ("Fayetteville, NC", "North Carolina"),
        ("Arlington, VA", "Virginia"),
        ("Columbus, IN", "Indiana"),
        ("Conway, SC", "South Carolina"),
        ("Jacksonville, FL", "Florida"),
        # Arkansas and Texas outside the primary metros keep the state.
        ("USA-AR-FORT-SMITH-08134-SAMS-CLUB", "Arkansas"),
        ("Jonesboro, AR", "Arkansas"),
        ("Houston, TX", "Texas"),
        ("Austin, Texas", "Texas"),
    ],
)
def test_the_state_beats_a_shared_city_name(location, expected):
    assert region_of(location) == expected


@pytest.mark.parametrize(
    ("location", "expected"),
    [
        ("US - GA - Atlanta", "Georgia"),
        ("Bellevue, Washington, USA", "Washington"),
        ("Chicago, Illinois, United States", "Illinois"),
        ("Charlotte, NC", "North Carolina"),
        ("New York, NY", "New York"),
    ],
)
def test_other_formats_still_find_the_state(location, expected):
    assert region_of(location) == expected


@pytest.mark.parametrize(
    "location",
    [
        "Pune, Maharashtra, IND",
        "Pune Maharashtra India",
        "Mississauga Ontario Canada",
        "London  United Kingdom",
        "Limerick, Ireland",
        "Singapore  Singapore",
        "Ciudad De Mexico Distrito Federal Mexico",
        "Toronto, ON",
    ],
)
def test_international(location):
    assert region_of(location) == INTERNATIONAL


def test_new_mexico_is_a_state_not_a_country():
    assert region_of("Albuquerque, New Mexico") == "New Mexico"


@pytest.mark.parametrize(
    "location",
    ["Remote/Homebased", "RemoteHomebased", "Remote - US", "Virtual"],
)
def test_remote(location):
    assert region_of(location) == REMOTE


@pytest.mark.parametrize("location", ["2 Locations", "11 Locations"])
def test_multiple_locations(location):
    """Workday collapses a posting listed in several places into one line."""
    assert region_of(location) == MULTIPLE


@pytest.mark.parametrize("location", ["", "   "])
def test_a_missing_location_is_unknown(location):
    assert region_of(location) == UNKNOWN


def test_a_two_letter_word_is_not_a_state():
    """Only a capitalised code counts, so ordinary words do not become states."""
    assert us_state("somewhere in a town") is None


def test_the_primary_regions_are_the_three_this_watch_is_aimed_at():
    assert PRIMARY_REGIONS == [NORTHWEST_ARKANSAS, LITTLE_ROCK, DALLAS_FORT_WORTH]
    assert all(is_primary(r) for r in PRIMARY_REGIONS)
    assert not is_primary("New York")


def test_every_location_gets_exactly_one_region():
    samples = [
        "Bentonville, AR", "Dallas, TX", "Little Rock, AR", "2 Locations",
        "Remote/Homebased", "Pune, Maharashtra, IND", "", "US - GA - Atlanta",
    ]
    for location in samples:
        assert isinstance(region_of(location), str)
        assert region_of(location) == region_of(location)
