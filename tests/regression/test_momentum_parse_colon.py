"""Regression (2026-07-16): Momentum-Parsing kippte still auf None, wenn die
Begruendung hinter dem Label einen Doppelpunkt enthielt (rsplit nahm den Text
nach dem LETZTEN Doppelpunkt). Aufgefallen beim Golden-Set-Ausbau P-GS6:
voltara_04/papyrus_03 wurden mit Momentum None geparst."""

from pathlib import Path

from src.agents.meddpicc.evaluation import parse_expected

_TEMPLATE = """# Soll-Bewertung — Test
## Metrics
- Confidence: UNBEKANNT
## Gesamt
- Overall score (0–100): 15
- Momentum (POSITIV / NEUTRAL / NEGATIV): {line}
"""


def _parse(tmp_path: Path, momentum_line: str):
    f = tmp_path / "testcase_01.expected.md"
    f.write_text(_TEMPLATE.format(line=momentum_line), encoding="utf-8")
    return parse_expected(f)


def test_momentum_with_colon_in_rationale(tmp_path):
    exp = _parse(tmp_path, "NEUTRAL — Lions Regel: beide Richtungen hart belegt -> NEUTRAL.")
    assert exp.momentum == "NEUTRAL"


def test_momentum_plain_label_still_parses(tmp_path):
    exp = _parse(tmp_path, "NEGATIV")
    assert exp.momentum == "NEGATIV"
