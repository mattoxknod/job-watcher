"""The mechanical engineering rule and the entry-level rule.

The titles here are real ones from the boards on the watch list, which is where
the awkward cases come from: these boards carry far more software engineers
than mechanical ones, so the rule earns its keep by what it rejects.
"""

import pytest

from jobwatcher.mechanical import is_entry_level, is_mechanical


@pytest.mark.parametrize(
    "title",
    [
        "Mechanical Engineer",
        "Mechanical Design Engineer",
        "Manufacturing Engineer",
        "Industrial Engineer",
        "Process Engineer",
        "Project Engineer",
        "Product Design Engineer - Data Center",
        "Controls Engineer",
        "Automation Engineer",
        "Quality Engineer",
        "Packaging Engineer",
        "Metallurgical Engineer",
        "Mechatronics Engineer",
        "Engineer III - Project Engineer",
        "Engineer IV - Fresh Meats Project Engineer",
        "Manufacturing Engineer Intern",
        "Intern, Industrial Engineer",
        "2027 Engineering Intern",
        "Engineering Development Program",
        "Mechanical Design Co-op",
    ],
)
def test_mechanical_titles(title):
    assert is_mechanical(title)


@pytest.mark.parametrize(
    "title",
    [
        "Software Engineer",
        "Staff, Software Engineer",
        "Senior Data Engineer",
        "COSMOS - Data Engineer IV",
        "Site Reliability Engineer",
        "Lead Cyber Security Engineer (Onsite)",
        "Network Engineer",
        "Systems Engineer",
        "Sales Engineer",
        "Solutions Engineer",
        "Endpoint Engineer II",
        "Senior Microsoft SharePoint Engineer",
        "QA Engineer",
        "Lead IT Data Engineer (Onsite)",
    ],
)
def test_software_and_it_engineers_are_not_mechanical(title):
    """"Engineer" alone means little on these boards."""
    assert not is_mechanical(title)


@pytest.mark.parametrize(
    "title",
    [
        "Assistant Professor in Mechanical Engineering",
        "Assistant Teaching Professor - HVAC",
        "Adjunct Faculty - Engineering",
    ],
)
def test_teaching_posts_are_not_mechanical_jobs(title):
    """A professorship in mechanical engineering is not the job being watched."""
    assert not is_mechanical(title)


@pytest.mark.parametrize(
    "title",
    [
        "Skilled Tradesman-STW-HVAC",
        "HVAC Mechanic I",
        "HVAC Technician",
        "Maintenance Technician",
        "Millwright",
        "Machine Operator",
    ],
)
def test_skilled_trades_are_not_engineering(title):
    """Trades sit beside engineering in a plant and share its vocabulary."""
    assert not is_mechanical(title)


@pytest.mark.parametrize(
    "title",
    [
        "Mechanical Engineering Intern",
        "Manufacturing Engineer Intern",
        "Mechanical Design Co-op",
        "Industrial Engineer, Entry Level",
        "Junior Design Engineer",
        "Associate Mechanical Engineer",
        "Engineering Development Program",
        "Manufacturing Engineer I",
        "Engineer 1",
        "New Graduate Mechanical Engineer",
        "Engineering Apprentice",
        "Early Career Process Engineer",
    ],
)
def test_entry_level_titles(title):
    assert is_entry_level(title)


@pytest.mark.parametrize(
    "title",
    [
        "Mechanical Engineer",
        "Senior Mechanical Engineer",
        "Lead Engineer Controls",
        "Principal Design Engineer",
        "Manufacturing Engineer II",
        "Engineer III",
        "Engineer IV - Prepared Foods",
        "Manager, Maintenance Engineering",
        "(USA) Director, Automation Engineering",
        "Staff Process Engineer",
    ],
)
def test_titles_past_the_first_rung_are_not_entry_level(title):
    assert not is_entry_level(title)


def test_seniority_beats_entry_wording():
    """"Senior Associate" is not an entry-level job."""
    assert not is_entry_level("Senior Associate Engineer")
    assert not is_entry_level("Lead Engineering Intern Supervisor")


def test_the_two_rules_are_independent():
    """A posting can be entry level without being mechanical, and the reverse."""
    assert is_entry_level("Software Engineering Intern")
    assert not is_mechanical("Software Engineering Intern")
    assert is_mechanical("Senior Mechanical Engineer")
    assert not is_entry_level("Senior Mechanical Engineer")


@pytest.mark.parametrize("title", ["", "   "])
def test_an_empty_title_matches_neither(title):
    assert not is_mechanical(title)
    assert not is_entry_level(title)
