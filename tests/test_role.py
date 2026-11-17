"""The title rule."""

import pytest

from jobwatcher.role import in_role


@pytest.mark.parametrize(
    "title",
    [
        "Financial Analyst",
        "Senior Financial Analyst",
        "Finance Analyst II",
        "Analyst, Financial Planning & Analysis",
        "FP&A Analyst",
        "Treasury Analyst",
        "Data Analyst II",
        "Business Intelligence Analyst",
        "Reporting Analyst",
        "Credit Analyst",
        "Credit Risk Analyst",
        "Risk Analyst - Wholesale",
        "Commercial Underwriter",
        "Investment Banking Analyst",
        "Capital Markets Analyst",
        "Equity Research Analyst",
        "Supply Chain Analyst",
        "Replenishment Analyst - Walmart/Sam's Club",
        "Pricing Analyst",
    ],
)
def test_analyst_titles_are_in_role(title):
    assert in_role(title)


@pytest.mark.parametrize(
    "title",
    [
        "2027 FT Senior Analyst, Finance - Accounting and Finance "
        "Development Program (AFDP)",
        "2027 Wholesale Credit Delivery - Analyst Program (INTERN CONVERSION)",
        "2027 Summer Internship Program - Business of IT Analyst Intern",
        "Finance Leadership Development Program",
        "Rotational Analyst, Corporate Finance",
        "Summer Analyst - Investment Banking",
    ],
)
def test_programs_and_internships_are_in_role(title):
    """The one-to-three year programs are part of the watch."""
    assert in_role(title)


@pytest.mark.parametrize(
    "title",
    [
        "Software Engineer",
        "Groundskeeper 1st Shift Corporate Springdale AR",
        "Warehouse Associate",
        "Registered Nurse",
        "Truck Driver - Dedicated",
        "Senior Marketing Manager",
    ],
)
def test_unrelated_titles_are_not_in_role(title):
    assert not in_role(title)


@pytest.mark.parametrize(
    "title",
    [
        "Manager, Financial Planning & Analysis",
        "Director of Risk Analytics",
        "Vice President, Credit Risk",
        "Head of Data Analytics",
        "Principal Financial Analyst",
        "Lead Financial Planning Analyst - FP&A",
    ],
)
def test_titles_above_analyst_level_are_not_in_role(title):
    """The watch list is aimed at analyst and associate level work."""
    assert not in_role(title)


def test_program_wording_survives_the_seniority_rule():
    """A program posting stays in role even when it carries a senior word."""
    assert in_role("Manager Trainee - Finance Rotational Program")


@pytest.mark.parametrize(
    "title",
    [
        "International Tax Specialist",
        "Internal Audit Associate",
    ],
)
def test_intern_does_not_match_inside_another_word(title):
    """"Intern" must not fire on "international" or "internal"."""
    assert not in_role(title)


def test_empty_title_is_not_in_role():
    assert not in_role("")
