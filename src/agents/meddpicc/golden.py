"""Golden-Set-Export: Kandidaten aus echten Deals + Roh-Notes fuer die Privat-Ablage.

Aus cli.py hierher gezogen (Befund 17.07.: Rendering-/Exportlogik gehoert nicht
in die CLI-Schicht — CLI und API rufen dieselben Funktionen). Die Ziel-Ordner
sind Modul-Konstanten, damit Tests sie auf tmp-Verzeichnisse patchen koennen
(Lehre aus der Glob-Kollision des --golden-E2E-Tests am 16.07.).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger("sales_os.agents.meddpicc")

_REPO_ROOT = Path(__file__).resolve().parents[3]
CANDIDATES_DIR = _REPO_ROOT / "tests" / "golden_set_candidates"
PRIVATE_NOTES_DIR = _REPO_ROOT / "tests" / "sample_notes" / "private"

DIMENSION_ORDER = [
    ("metrics", "Metrics"),
    ("economic_buyer", "Economic Buyer"),
    ("decision_criteria", "Decision Criteria"),
    ("decision_process", "Decision Process"),
    ("paper_process", "Paper Process"),
    ("identify_pain", "Identify Pain"),
    ("champion", "Champion"),
    ("competition", "Competition"),
]


def _slug(name: str) -> str:
    return name.lower().replace(" ", "_")


def export_golden_candidate(deal) -> Path | None:
    """Exportiert den letzten Snapshot als vorausgefuellte Golden-Set-Vorlage.

    Organisches Wachstum des Golden Sets Richtung n>=20 durch taegliche Nutzung
    (Befund 2.3). Kandidaten koennen echte Kundendaten enthalten -> Ordner ist
    gitignored; Lion prueft, korrigiert und verschiebt von Hand.
    """
    from src.repository.activities import list_activities
    from src.repository.snapshots import get_latest_snapshot

    snapshot = get_latest_snapshot(deal.id)
    if snapshot is None:
        log.warning("--golden: kein Snapshot fuer '%s' — nichts zu exportieren.", deal.name)
        return None
    activities = list_activities(deal.id)
    sources = ", ".join(a.source or a.id[:8] for a in activities) or "(keine Activities erfasst)"

    lines = [
        f"# Golden-Set-KANDIDAT — {deal.name} (VON LION ZU PRUEFEN)",
        "",
        f"> Ist-Werte des Snapshots vom {snapshot.created_at:%Y-%m-%d %H:%M} als Vorlage —",
        "> jede Zeile pruefen/korrigieren, dann als <slug>_NN.expected.md verschieben:",
        "> echte Kundendaten -> tests/golden_set/private/ (gitignored, Notes via export-notes),",
        "> synthetische Faelle -> tests/golden_set/.",
        f"> Input-Notes: {sources}",
        f"> prompt_version des Ist-Laufs: {snapshot.prompt_version}",
        "",
    ]
    for key, heading in DIMENSION_ORDER:
        dim = snapshot.dimensions.get(key)
        if dim is None:
            continue
        lines += [
            f"## {heading}",
            f"- Findings: {dim.findings}",
            f"- Confidence: {dim.confidence}",
            f"- Evidence: {'; '.join(dim.evidence)}",
            f"- Gaps: {'; '.join(dim.gaps)}",
            f"- Trend: {dim.trend}",
            f"- Recommended action: {dim.recommended_action}",
            f"- Next question: {dim.next_question}",
            "",
        ]
    lines += [
        "## Gesamt",
        f"- Overall score (0–100): {snapshot.overall_score}",
        f"- Signal-Bonus (0–5): {snapshot.signal_bonus}",
        f"- Score rationale: {snapshot.score_rationale}",
        f"- Momentum (POSITIV / NEUTRAL / NEGATIV): {snapshot.momentum}",
        f"- Momentum rationale: {snapshot.momentum_rationale}",
        f"- Deal risks: {'; '.join(snapshot.deal_risks)}",
        f"- Next best questions (max 5, priorisiert): {'; '.join(snapshot.next_best_questions)}",
        f"- Summary for manager (3 Saetze, forecast-tauglich): {snapshot.summary_for_manager}",
    ]
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)
    path = CANDIDATES_DIR / f"{_slug(deal.name)}_{ts}.expected.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def export_notes(deal, target_dir: Path | None = None) -> list[Path]:
    """Schreibt die Roh-Texte aller Activities eines Deals chronologisch als
    <slug>_NN.txt in die Privat-Ablage (echte Kundendaten, gitignored).
    Gegenstueck zu export_golden_candidate — zusammen ergeben sie einen
    eval-faehigen Fall aus einem echten Deal."""
    from src.repository.activities import list_activities

    target_dir = target_dir or PRIVATE_NOTES_DIR
    activities = [a for a in list_activities(deal.id) if a.raw_text.strip()]
    if not activities:
        return []
    activities.sort(key=lambda a: a.occurred_at)
    target_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for i, activity in enumerate(activities, 1):
        path = target_dir / f"{_slug(deal.name)}_{i:02d}.txt"
        path.write_text(activity.raw_text, encoding="utf-8")
        written.append(path)
    return written
