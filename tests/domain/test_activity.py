"""Tests fuer das Activity-Modell inkl. raw_text_hash-Ableitung."""
from __future__ import annotations

import hashlib

import pytest
from pydantic import ValidationError

from src.domain.activity import Activity


def test_activity_hash_derived_from_raw_text():
    text = "Kurzer Call mit Sarah, Budget bestaetigt."
    a = Activity(deal_id="deal-1", type="CALL", raw_text=text)
    assert a.raw_text_hash == hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_activity_explicit_hash_kept():
    a = Activity(deal_id="deal-1", type="NOTE", raw_text="x", raw_text_hash="vorgegeben")
    assert a.raw_text_hash == "vorgegeben"


def test_activity_missing_required_invalid():
    with pytest.raises(ValidationError):
        Activity(type="CALL", raw_text="ohne deal_id")  # deal_id fehlt


def test_activity_invalid_type():
    with pytest.raises(ValidationError):
        Activity(deal_id="deal-1", type="WHATSAPP", raw_text="x")


def test_activity_defaults():
    a = Activity(deal_id="deal-1", type="EMAIL", raw_text="hi")
    assert a.summary == "" and a.source == ""
    assert a.occurred_at is not None
