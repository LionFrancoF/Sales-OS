"""End-to-End-Durchlauf der DoD (LLM gemockt):
Account + Deal anlegen -> analyze -> show-deal zeigt Snapshot -> correct ->
erneutes analyze laedt den Vorgaenger; Korrektur liegt nachweislich in der DB
und ist abrufbar (Injektion bewusst erst nach M4 — CLAUDE.md).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from src import cli
from src.agents.meddpicc import agent as agent_mod
from src.agents.meddpicc.schema import AnalysisResult, LlmDimension, LlmDimensions
from src.repository.corrections import get_corrections
from src.repository.deals import get_deal_by_name
from src.repository.snapshots import list_snapshots

NOTES = Path(__file__).resolve().parents[2] / "tests" / "sample_notes" / "nordwind_01.txt"


def _dim(confidence="ZU_PRUEFEN", trend="ERSTBEWERTUNG"):
    return LlmDimension(findings="f", confidence=confidence, evidence=[], gaps=[],
                        trend=trend, recommended_action="a", next_question="q")


def _result():
    dims = {k: _dim() for k in ("metrics", "economic_buyer", "decision_criteria", "decision_process",
                                "paper_process", "identify_pain", "champion", "competition")}
    return AnalysisResult(dimensions=LlmDimensions(**dims), overall_score=25, signal_bonus=0,
                          score_rationale="r", momentum="NEGATIV",
                          momentum_rationale="Budget entfallen (Tier-Downgrade)",
                          deal_risks=["risk"], next_best_questions=["q?"], summary_for_manager="s")


@pytest.fixture()
def mock_llm(monkeypatch):
    captured: list[str] = []

    def fake(system_blocks, user_message):
        captured.append(user_message)
        return _result()

    monkeypatch.setattr(agent_mod, "_call_llm", fake)
    return captured


def test_full_p5_walkthrough(mock_llm, capsys):
    # 1) Account + Deal anlegen
    assert cli.main(["add-account", "--name", "Nordwind Logistics", "--industry", "Logistik"]) == 0
    assert cli.main(["add-deal", "Nordwind Logistics", "--name", "Ops-Analytics", "--stage", "DISCOVERY"]) == 0

    # 2) analyze mit --deal -> Snapshot landet in der DB (DB only, kein outputs-JSON)
    assert cli.main(["analyze", str(NOTES), "--deal", "Ops-Analytics"]) == 0
    deal = get_deal_by_name("Ops-Analytics")
    assert len(list_snapshots(deal.id)) == 1

    # 3) show-deal zeigt den Snapshot
    assert cli.main(["show-deal", "Ops-Analytics"]) == 0
    out = capsys.readouterr().out
    assert "Score 25/100" in out and "NEGATIV" in out

    # 4) correct -> Correction gespeichert, original_value aus dem Snapshot aufgeloest
    assert cli.main(["correct", "Ops-Analytics", "--field", "dimensions.champion.confidence",
                     "--value", "UNBEKANNT", "--comment", "zu grosszuegig"]) == 0
    corrections = get_corrections(deal.id, agent="meddpicc_analyzer")
    assert len(corrections) == 1
    assert corrections[0].original_value == "ZU_PRUEFEN"  # nachweislich aus letztem Snapshot
    assert corrections[0].corrected_value == "UNBEKANNT"

    # 5) erneutes analyze: Vorgaenger-Snapshot wird geladen und in den Prompt gegeben
    assert cli.main(["analyze", str(NOTES), "--deal", "Ops-Analytics"]) == 0
    assert len(list_snapshots(deal.id)) == 2  # append-only, nichts ueberschrieben
    assert "VORIGER SNAPSHOT (fuer trend-Bestimmung)" in mock_llm[-1]

    # show-deal weist die Korrektur aus (nachweislich gesammelt)
    assert cli.main(["show-deal", "Ops-Analytics"]) == 0
    out = capsys.readouterr().out
    assert "Korrekturen (1" in out and "UNBEKANNT" in out


def test_add_contact_duplicate_guard(capsys):
    assert cli.main(["add-account", "--name", "Aurelia Bank"]) == 0
    assert cli.main(["add-contact", "Aurelia Bank", "--name", "Katharina Bender", "--role", "CHAMPION"]) == 0
    # Dublette wird erkannt und abgelehnt
    assert cli.main(["add-contact", "Aurelia Bank", "--name", "Dr. Katharina Bender"]) == 1
    out = capsys.readouterr().out
    assert "Dublette" in out
    # --force erzwingt
    assert cli.main(["add-contact", "Aurelia Bank", "--name", "Dr. Katharina Bender", "--force"]) == 0


def test_analyze_unknown_deal_fails_cleanly(mock_llm):
    assert cli.main(["analyze", str(NOTES), "--deal", "Gibt Es Nicht"]) == 1
    assert mock_llm == []  # kein API-Call verschwendet


def test_correct_golden_exports_candidate(mock_llm, tmp_path, monkeypatch, capsys):
    """--golden exportiert eine vorausgefuellte Golden-Set-Vorlage (Wachstum Richtung n>=20)."""
    assert cli.main(["add-account", "--name", "Nordwind Logistics"]) == 0
    assert cli.main(["add-deal", "Nordwind Logistics", "--name", "Ops-Analytics"]) == 0
    assert cli.main(["analyze", str(NOTES), "--deal", "Ops-Analytics"]) == 0

    assert cli.main(["correct", "Ops-Analytics", "--field", "dimensions.champion.confidence",
                     "--value", "UNBEKANNT", "--golden"]) == 0
    out = capsys.readouterr().out
    assert "Golden-Set-Kandidat exportiert" in out

    candidates_dir = Path(cli.__file__).resolve().parent.parent / "tests" / "golden_set_candidates"
    files = sorted(candidates_dir.glob("ops-analytics_*.expected.md")) or sorted(
        candidates_dir.glob("ops_analytics_*.expected.md"))
    assert files, "Kandidaten-Datei fehlt"
    content = files[-1].read_text(encoding="utf-8")
    assert "VON LION ZU PRUEFEN" in content
    assert "- Confidence: ZU_PRUEFEN" in content       # Ist-Werte vorausgefuellt
    assert "- Momentum (POSITIV / NEUTRAL / NEGATIV): NEGATIV" in content
    assert "- Signal-Bonus (0–5): 0" in content
    files[-1].unlink()  # Testartefakt aufraeumen
