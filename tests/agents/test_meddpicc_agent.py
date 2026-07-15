"""Tests fuer den MEDDPICC-Analyzer (API gemockt; 1 echter Lauf hinter Flag)."""
from __future__ import annotations

import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.agents.meddpicc import agent as agent_mod
from src.agents.meddpicc.agent import analyze
from src.agents.meddpicc.prompts import PROMPT_VERSION, build_user_message
from src.agents.meddpicc.schema import AnalysisResult, LlmDimension, LlmDimensions
from src.domain.meddpicc import DimensionAssessment, MeddpiccSnapshot

NOTES_DIR = Path(__file__).resolve().parents[2] / "tests" / "sample_notes"


def _dim(confidence: str = "UNBEKANNT", trend: str = "ERSTBEWERTUNG") -> LlmDimension:
    return LlmDimension(
        findings="f", confidence=confidence, evidence=[], gaps=[], trend=trend,
        recommended_action="a", next_question="q",
    )


def _result(momentum: str = "NEUTRAL", score: int = 40) -> AnalysisResult:
    dims = {k: _dim() for k in (
        "metrics", "economic_buyer", "decision_criteria", "decision_process",
        "paper_process", "identify_pain", "champion", "competition",
    )}
    return AnalysisResult(
        dimensions=LlmDimensions(**dims),
        overall_score=score, signal_bonus=0, score_rationale="r",
        momentum=momentum, momentum_rationale="kein harter Beleg -> NEUTRAL",
        deal_risks=["risiko"], next_best_questions=["frage?"], summary_for_manager="s1. s2. s3.",
    )


@pytest.fixture(autouse=True)
def _reset_breaker():
    from src.agents import llm

    llm._calls_this_command = 0
    llm._tokens_this_command = 0


@pytest.fixture()
def mock_llm(monkeypatch):
    """Ersetzt den API-Call; zeichnet Aufrufe auf."""
    calls: list[str] = []

    def fake_call(system_blocks, user_message):
        calls.append(user_message)
        return _result()

    monkeypatch.setattr(agent_mod, "_call_llm", fake_call)
    return calls


def test_e2e_with_two_sample_notes(mock_llm):
    """End-to-End (gemockt) mit 2 echten sample_notes-Dateien."""
    notes = (NOTES_DIR / "nordwind_01.txt").read_text() + (NOTES_DIR / "nordwind_02.txt").read_text()
    snapshot = analyze(notes)
    assert isinstance(snapshot, MeddpiccSnapshot)
    assert snapshot.framework == "MEDDPICC"
    assert "1.6" in snapshot.framework_rationale  # erzwungen, begruendet
    assert snapshot.prompt_version == PROMPT_VERSION
    assert set(snapshot.dimensions) == {k for k, _ in [
        ("metrics", 0), ("economic_buyer", 0), ("decision_criteria", 0), ("decision_process", 0),
        ("paper_process", 0), ("identify_pain", 0), ("champion", 0), ("competition", 0),
    ]}
    assert "nordwind" in mock_llm[0].lower()  # Notes sind im User-Prompt gelandet


def test_trend_forced_to_erstbewertung_without_previous(monkeypatch):
    """Ohne previous_snapshot erzwingt der CODE ERSTBEWERTUNG, egal was das LLM sagt."""
    monkeypatch.setattr(agent_mod, "_call_llm", lambda s, u: _result())
    result = _result()
    for d in result.dimensions.model_dump().values():
        assert d["trend"] == "ERSTBEWERTUNG"
    lying = _result()
    lying.dimensions.champion.trend = "VERBESSERT"  # LLM "luegt"
    monkeypatch.setattr(agent_mod, "_call_llm", lambda s, u: lying)
    snapshot = analyze("notes")
    assert snapshot.dimensions["champion"].trend == "ERSTBEWERTUNG"


def test_previous_snapshot_flows_into_prompt(monkeypatch):
    captured = {}

    def fake_call(system_blocks, user_message):
        captured["user"] = user_message
        return _result()

    monkeypatch.setattr(agent_mod, "_call_llm", fake_call)
    previous = MeddpiccSnapshot(
        deal_id="d1", overall_score=55,
        dimensions={"champion": DimensionAssessment(findings="alt", confidence="ZU_PRUEFEN")},
    )
    analyze("neue note", previous_snapshot=previous)
    assert "VORIGER SNAPSHOT" in captured["user"]
    assert "ZU_PRUEFEN" in captured["user"]


def test_exactly_one_retry_on_validation_error(monkeypatch):
    attempts = []

    def flaky(system_blocks, user_message):
        attempts.append(user_message)
        if len(attempts) == 1:
            raise ValueError("Kein parsebarer Output (stop_reason=max_tokens).")
        return _result()

    monkeypatch.setattr(agent_mod, "_call_llm", flaky)
    snapshot = analyze("notes")
    assert len(attempts) == 2
    assert "KORREKTUR ERFORDERLICH" in attempts[1]  # Fehlermeldung im Retry-Prompt
    assert snapshot.overall_score == 40


def test_second_failure_propagates(monkeypatch):
    def always_fail(system_blocks, user_message):
        raise ValueError("kaputt")

    monkeypatch.setattr(agent_mod, "_call_llm", always_fail)
    with pytest.raises(ValueError, match="kaputt"):
        analyze("notes")


def test_circuit_breaker_stops_runaway(monkeypatch):
    from src.agents import llm

    monkeypatch.setattr(llm, "_calls_this_command", 999)
    with pytest.raises(RuntimeError, match="Circuit-Breaker"):
        llm._check_circuit_breaker()


def test_empty_notes_rejected():
    with pytest.raises(ValueError, match="Leere Notes"):
        analyze("   ")


def test_signal_bonus_hard_cap_in_code():
    """Lions Kalibrierung: +5-Deckel wird vom CODE erzwungen, nicht nur vom Prompt."""
    base = _result().model_dump()
    base["signal_bonus"] = 6
    with pytest.raises(ValidationError):
        AnalysisResult.model_validate(base)


def test_new_fields_flow_into_snapshot(mock_llm):
    snapshot = analyze("irgendwelche notes")
    assert snapshot.signal_bonus == 0
    assert "NEUTRAL" in snapshot.momentum_rationale


def test_llm_schema_rejects_sixth_question():
    with pytest.raises(ValidationError):
        _result_with_six = _result()
        type(_result_with_six).model_validate(
            {**_result_with_six.model_dump(), "next_best_questions": ["1", "2", "3", "4", "5", "6"]}
        )


def test_user_message_order_variable_parts():
    """Cache-Disziplin: Corrections vor Deal-Kontext vor Snapshot vor Notes."""
    msg = build_user_message("NOTES", previous_snapshot_json='{"x":1}', deal_context="Deal: A", corrections_block="KORR")
    assert msg.index("KORREKTUREN") < msg.index("DEAL-KONTEXT") < msg.index("VORIGER SNAPSHOT") < msg.index("CALL-NOTES")


@pytest.mark.skipif(not os.environ.get("RUN_REAL_API"), reason="echter API-Call nur mit RUN_REAL_API=1")
def test_real_api_smoke():
    """Optionaler echter Durchlauf (kostet Geld): 1 kleine Note gegen die echte API."""
    notes = (NOTES_DIR / "nordwind_01.txt").read_text()
    snapshot = analyze(notes)
    assert snapshot.overall_score >= 0
    assert snapshot.dimensions["champion"].confidence in {"GESICHERT", "WAHRSCHEINLICH", "ZU_PRUEFEN", "UNBEKANNT"}
