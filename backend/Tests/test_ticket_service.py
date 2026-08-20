import re

import pytest

from app.services import ticket_service


# ================================================================
# _category_code
# ================================================================

@pytest.mark.parametrize(
    "category, expected",
    [
        ("Network Access", "NA"),
        ("vpn", "V"),
        ("Software Installation Request", "SIR"),
        ("  extra   spaces  here ", "ESH"),
        ("", "TCK"),
        ("   ", "TCK"),
    ],
)
def test_category_code(category, expected):
    assert ticket_service._category_code(category) == expected


# ================================================================
# create_ticket
# ================================================================

def test_create_ticket_returns_all_expected_fields():
    ticket = ticket_service.create_ticket(
        category="Network",
        subcategory="VPN",
        priority="P1",
        impact="High",
        urgency="High",
        justification="Entire office cannot connect.",
        user_query="VPN is down for everyone",
    )

    assert ticket["category"] == "Network"
    assert ticket["subcategory"] == "VPN"
    assert ticket["priority"] == "P1"
    assert ticket["impact"] == "High"
    assert ticket["urgency"] == "High"
    assert ticket["justification"] == "Entire office cannot connect."
    assert ticket["summary"] == "VPN is down for everyone"
    assert "created_at" in ticket


def test_create_ticket_number_starts_with_category_code_and_is_well_formed():
    ticket = ticket_service.create_ticket(
        category="Network",
        subcategory="VPN",
        priority="P1",
        impact="High",
        urgency="High",
        justification="Entire office cannot connect.",
        user_query="VPN is down for everyone",
    )

    assert re.match(r"^N-\d{14}-[0-9A-F]{6}$", ticket["ticket_number"])


def test_create_ticket_numbers_are_unique():
    make = lambda: ticket_service.create_ticket(
        category="Software",
        subcategory="Installation",
        priority="P3",
        impact="Low",
        urgency="Low",
        justification="Needs an approved app installed.",
        user_query="Please install Acrobat Reader",
    )

    first = make()
    second = make()

    assert first["ticket_number"] != second["ticket_number"]


def test_create_ticket_falls_back_to_tck_for_empty_category():
    ticket = ticket_service.create_ticket(
        category="",
        subcategory="",
        priority="P5",
        impact="Low",
        urgency="Low",
        justification="",
        user_query="",
    )

    assert ticket["ticket_number"].startswith("TCK-")
