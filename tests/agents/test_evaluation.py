"""Tests fuer das Golden-Set-Parsing und den Ist/Soll-Vergleich."""
from __future__ import annotations

from pathlib import Path

from src.agents.meddpicc.evaluation import (
    concat_notes,
    find_golden_cases,
    parse_expected,
    render_comparison,
)
from src.domain.meddpicc import DimensionAssessment, MeddpiccSnapshot

GOLDEN_DIR = Path(__file__).resolve().parents[2] / "tests" / "golden_set"
NOTES_DIR = Path(__file__).resolve().parents[2] / "tests" / "sample_notes"

SAMPLE_EXPECTED = """# Soll-Bewertung — Test / Deal "X"

## Metrics
- Findings: irgendwas
- Confidence: WAHRSCHEINLICH

## Champion
- Findings: uebergang
- Confidence: ZU_PRUEFEN

## Gesamt
- Overall score (0–100): 55
- Momentum (POSITIV / NEUTRAL / NEGATIV): NEUTRAL
"""


def test_parse_expected_fixture(tmp_path: Path):
    f = tmp_path / "testacct_05.expected.md"
    f.write_text(SAMPLE_EXPECTED, encoding="utf-8")
    exp = parse_expected(f)
    assert exp.account == "testacct"
    assert exp.confidences == {"metrics": "WAHRSCHEINLICH", "champion": "ZU_PRUEFEN"}
    assert exp.overall_score == 55
    assert exp.momentum == "NEUTRAL"


def test_parse_real_golden_files_complete():
    """Alle echten Golden-Set-Dateien muessen vollstaendig parsebar sein (8 Dimensionen, Score, Momentum)."""
    for path in sorted(GOLDEN_DIR.glob("*.expected.md")):
        exp = parse_expected(path)
        assert len(exp.confidences) == 8, f"{path.name}: nur {len(exp.confidences)} Confidences geparst"
        assert exp.overall_score is not None, f"{path.name}: Score fehlt"
        assert exp.momentum in {"POSITIV", "NEUTRAL", "NEGATIV"}, f"{path.name}: Momentum fehlt"


def test_find_golden_cases_maps_notes():
    cases = find_golden_cases(GOLDEN_DIR, NOTES_DIR)
    assert len(cases) == 6
    accounts = sorted(exp.account for exp, _ in cases)
    assert accounts == ["aurelia", "hanseatik", "meridian", "nordwind", "papyrus", "voltara"]
    for exp, notes in cases:
        assert all(exp.account in p.name for p in notes)
        assert len(notes) >= 3


def test_concat_notes_chronological(tmp_path: Path):
    a = tmp_path / "x_01.txt"
    b = tmp_path / "x_02.txt"
    a.write_text("erste", encoding="utf-8")
    b.write_text("zweite", encoding="utf-8")
    combined = concat_notes([a, b])
    assert combined.index("erste") < combined.index("zweite")
    assert "Note 1/2" in combined and "Note 2/2" in combined


def test_render_comparison_marks_hits_and_misses():
    exp = parse_expected_from_text()
    snapshot = MeddpiccSnapshot(
        deal_id="d", overall_score=50, momentum="NEGATIV",
        dimensions={
            "metrics": DimensionAssessment(confidence="WAHRSCHEINLICH"),   # Treffer
            "champion": DimensionAssessment(confidence="GESICHERT"),       # daneben
        },
    )
    out = render_comparison(exp, snapshot)
    assert "✓ Metrics" in out
    assert "✗ Champion" in out
    assert "keine Qualitaetsmetrik" in out  # Befund 2.3 sichtbar verankert
    assert "Δ -5" in out
    assert "✗ Momentum" in out


def parse_expected_from_text():
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "acct_01.expected.md"
        f.write_text(SAMPLE_EXPECTED, encoding="utf-8")
        return parse_expected(f)
