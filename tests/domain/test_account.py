"""Tests fuer das Account-Modell: valide und invalide Daten."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.domain.account import Account


def test_account_valid_minimal():
    a = Account(name="Acme Corp")
    assert a.name == "Acme Corp"
    assert isinstance(a.id, str) and len(a.id) > 0
    assert a.domain is None and a.research_profile is None
    assert a.created_at is not None and a.updated_at is not None


def test_account_valid_full():
    a = Account(
        name="Globex",
        domain="globex.com",
        industry="Manufacturing",
        size_estimate="1000-5000 MA",
        research_profile={"signals": []},
    )
    assert a.domain == "globex.com"
    assert a.research_profile == {"signals": []}


def test_account_missing_name_invalid():
    with pytest.raises(ValidationError):
        Account()  # name ist Pflicht


def test_account_extra_field_forbidden():
    with pytest.raises(ValidationError):
        Account(name="Acme", unbekanntes_feld="x")
