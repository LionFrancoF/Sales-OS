"""Tests fuer das Correction-Modell."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.domain.correction import Correction


def test_correction_valid():
    c = Correction(
        deal_id="deal-1",
        agent="meddpicc",
        field_path="dimensions.champion.confidence",
        original_value="WAHRSCHEINLICH",
        corrected_value="GESICHERT",
        comment="John hat schriftlich zugesagt.",
    )
    assert c.agent == "meddpicc"
    assert c.corrected_value == "GESICHERT"
    assert isinstance(c.id, str) and len(c.id) > 0


def test_correction_missing_required_invalid():
    with pytest.raises(ValidationError):
        Correction(deal_id="deal-1", agent="meddpicc")  # field_path/values fehlen


def test_correction_extra_field_forbidden():
    with pytest.raises(ValidationError):
        Correction(
            deal_id="deal-1",
            agent="meddpicc",
            field_path="x",
            original_value="a",
            corrected_value="b",
            tippfehler="nope",
        )
