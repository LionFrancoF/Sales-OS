"""Golden-Set-Eval: Ist vs. Soll QUALITATIV nebeneinander.

Bewusste Entscheidung (P-1 Befund 2.3, CLAUDE.md): bei n=3 ist eine
Einzel-Metrik statistisch Rauschen — es gibt KEINE gewichtete Gesamtzahl.
Der Eval zeigt pro Deal die Confidence-Treffer je Dimension, Score- und
Momentum-Abgleich; das qualitative Urteil trifft der Mensch (volle Analysen
liegen in outputs/eval/). Eine Metrik kommt erst ab >=20 Beispielen.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

# Ueberschrift in *.expected.md -> Dimensions-Key im Snapshot
HEADING_TO_KEY = {
    "Metrics": "metrics",
    "Economic Buyer": "economic_buyer",
    "Decision Criteria": "decision_criteria",
    "Decision Process": "decision_process",
    "Paper Process": "paper_process",
    "Identify Pain": "identify_pain",
    "Champion": "champion",
    "Competition": "competition",
}

_CONFIDENCES = {"GESICHERT", "WAHRSCHEINLICH", "ZU_PRUEFEN", "UNBEKANNT"}
_MOMENTA = {"POSITIV", "NEUTRAL", "NEGATIV"}


@dataclass
class ExpectedAnalysis:
    """Soll-Werte aus einer handbewerteten *.expected.md."""

    account: str
    confidences: dict[str, str] = field(default_factory=dict)  # key -> Confidence
    overall_score: int | None = None
    momentum: str | None = None


def parse_expected(path: Path) -> ExpectedAnalysis:
    """Parst die Soll-Vorlage (## <Dimension> ... - Confidence: X, plus Gesamt-Sektion)."""
    text = path.read_text(encoding="utf-8")
    account = path.stem.split(".")[0].split("_")[0]
    expected = ExpectedAnalysis(account=account)

    current_key: str | None = None
    for line in text.splitlines():
        heading = re.match(r"^##\s+(.+?)\s*$", line)
        if heading:
            current_key = HEADING_TO_KEY.get(heading.group(1).strip())
            continue
        if current_key and line.strip().startswith("- Confidence:"):
            value = line.split(":", 1)[1].strip().upper()
            if value in _CONFIDENCES:
                expected.confidences[current_key] = value
            continue
        stripped = line.strip()
        if stripped.startswith("- Overall score"):
            digits = re.search(r":\s*(\d+)\s*$", stripped)
            if digits:
                expected.overall_score = int(digits.group(1))
        elif stripped.startswith("- Momentum"):
            value = stripped.rsplit(":", 1)[-1].strip().upper()
            # nur das reine Momentum-Wort werten (Zusatztext ignorieren)
            for m in _MOMENTA:
                if value.startswith(m):
                    expected.momentum = m
                    break
    return expected


def find_golden_cases(golden_dir: Path, notes_dir: Path) -> list[tuple[ExpectedAnalysis, list[Path]]]:
    """Findet alle Golden-Set-Vorlagen + die zugehoerigen, chronologischen Notes."""
    cases = []
    for expected_file in sorted(golden_dir.glob("*.expected.md")):
        expected = parse_expected(expected_file)
        note_files = sorted(notes_dir.glob(f"{expected.account}_*.txt"))
        if not note_files:
            raise FileNotFoundError(
                f"Keine Notes fuer Golden-Set-Account '{expected.account}' in {notes_dir}."
            )
        cases.append((expected, note_files))
    return cases


def concat_notes(note_files: list[Path]) -> str:
    """Konkateniert Notes chronologisch mit klaren Trennern (kumulierte Analyse)."""
    blocks = []
    for i, path in enumerate(note_files, 1):
        blocks.append(f"--- Note {i}/{len(note_files)}: {path.name} ---\n{path.read_text(encoding='utf-8')}")
    return "\n\n".join(blocks)


def render_comparison(expected: ExpectedAnalysis, snapshot) -> str:
    """Rendert den qualitativen Ist/Soll-Vergleich fuer einen Deal (Terminal)."""
    lines = [f"━━━ {expected.account.upper()} — Ist vs. Soll ━━━"]
    hits = 0
    for heading, key in HEADING_TO_KEY.items():
        soll = expected.confidences.get(key, "?")
        dim = snapshot.dimensions.get(key)
        ist = dim.confidence if dim else "?"
        match = "✓" if soll == ist else "✗"
        if soll == ist:
            hits += 1
        lines.append(f"  {match} {heading:<18} Soll: {soll:<15} Ist: {ist}")
    lines.append(f"  Confidence-Treffer: {hits}/8 (Anzeige, keine Qualitaetsmetrik — n=3, Befund 2.3)")
    if expected.overall_score is not None:
        delta = snapshot.overall_score - expected.overall_score
        lines.append(f"  Score   Soll: {expected.overall_score}  Ist: {snapshot.overall_score}  (Δ {delta:+d})")
    if expected.momentum:
        match = "✓" if expected.momentum == snapshot.momentum else "✗"
        lines.append(f"  {match} Momentum  Soll: {expected.momentum}  Ist: {snapshot.momentum}")
    return "\n".join(lines)
