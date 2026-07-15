"""Tests fuer DimensionAssessment und MeddpiccSnapshot."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.domain.meddpicc import DimensionAssessment, MeddpiccSnapshot


def test_dimension_assessment_defaults():
    d = DimensionAssessment()
    assert d.confidence == "UNBEKANNT"
    assert d.trend == "ERSTBEWERTUNG"
    assert d.evidence == [] and d.gaps == []


def test_snapshot_valid_full():
    snap = MeddpiccSnapshot(
        deal_id="deal-1",
        framework="MEDDPICC",
        dimensions={
            "champion": DimensionAssessment(findings="John treibt intern", confidence="WAHRSCHEINLICH"),
            "paper_process": DimensionAssessment(findings="Legal reviewt", confidence="ZU_PRUEFEN"),
        },
        overall_score=62,
        next_best_questions=["Wer unterschreibt?", "Bis wann Budget-Freigabe?"],
    )
    assert snap.overall_score == 62
    assert snap.dimensions["champion"].confidence == "WAHRSCHEINLICH"


def test_snapshot_requires_overall_score():
    with pytest.raises(ValidationError):
        MeddpiccSnapshot(deal_id="deal-1")  # overall_score fehlt


@pytest.mark.parametrize("bad_score", [-5, 101])
def test_snapshot_score_out_of_range(bad_score):
    with pytest.raises(ValidationError):
        MeddpiccSnapshot(deal_id="deal-1", overall_score=bad_score)


def test_snapshot_unknown_dimension_key_invalid():
    with pytest.raises(ValidationError):
        MeddpiccSnapshot(
            deal_id="deal-1",
            overall_score=50,
            dimensions={"budget": DimensionAssessment()},  # kein gueltiger Key
        )


def test_snapshot_paper_process_only_with_meddpicc():
    with pytest.raises(ValidationError):
        MeddpiccSnapshot(
            deal_id="deal-1",
            framework="MEDDICC",
            overall_score=50,
            dimensions={"paper_process": DimensionAssessment()},
        )


def test_snapshot_next_best_questions_max_five():
    with pytest.raises(ValidationError):
        MeddpiccSnapshot(
            deal_id="deal-1",
            overall_score=50,
            next_best_questions=["1", "2", "3", "4", "5", "6"],
        )
