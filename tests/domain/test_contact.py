"""Tests fuer das Contact-Modell inkl. Alignment-Felder."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.domain.contact import Contact


def test_contact_valid_defaults_are_unknown():
    c = Contact(account_id="acc-1", name="Sarah Lee")
    assert c.role_in_deal == "UNKLAR"
    assert c.influence == "UNBEKANNT"
    assert c.disposition == "UNBEKANNT"
    assert c.relationship_strength == "KEIN_KONTAKT"
    assert c.last_touchpoint is None
    assert c.notes == ""


def test_contact_valid_full_alignment():
    c = Contact(
        account_id="acc-1",
        name="John Doe",
        title="VP Engineering",
        email="john@acme.com",
        role_in_deal="CHAMPION",
        influence="HOCH",
        disposition="PROMOTER",
        relationship_strength="STARK",
    )
    assert c.role_in_deal == "CHAMPION"
    assert c.influence == "HOCH"


def test_contact_missing_required_invalid():
    with pytest.raises(ValidationError):
        Contact(name="No Account")  # account_id fehlt


@pytest.mark.parametrize(
    "field,value",
    [
        ("role_in_deal", "BOSS"),
        ("influence", "SEHR_HOCH"),
        ("disposition", "FAN"),
        ("relationship_strength", "MITTEL"),
    ],
)
def test_contact_invalid_literals(field, value):
    with pytest.raises(ValidationError):
        Contact(account_id="acc-1", name="X", **{field: value})
