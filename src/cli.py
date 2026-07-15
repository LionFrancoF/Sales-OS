"""Sales OS – CLI-Einstiegspunkt.

Implementiert (P4): analyze, eval. Alle uebrigen Befehle sind Platzhalter und
werden in ihrer Schicht implementiert (siehe CLAUDE.md / ARCHITECTURE.md).
Bewusst KEIN compare-Befehl (P-1 Befund 1.8: redundant zu trend im Snapshot).

Aufruf: python -m src.cli --help
"""
from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from src.logging_setup import setup_logging

log = logging.getLogger("sales_os.cli")

OUTPUTS_DIR = Path(__file__).resolve().parent.parent / "outputs"
GOLDEN_DIR = Path(__file__).resolve().parent.parent / "tests" / "golden_set"
NOTES_DIR = Path(__file__).resolve().parent.parent / "tests" / "sample_notes"

_AMPEL = {"GESICHERT": "🟢", "WAHRSCHEINLICH": "🟡", "ZU_PRUEFEN": "🟠", "UNBEKANNT": "⚪"}
_DIMENSION_ORDER = [
    ("metrics", "Metrics"),
    ("economic_buyer", "Economic Buyer"),
    ("decision_criteria", "Decision Criteria"),
    ("decision_process", "Decision Process"),
    ("paper_process", "Paper Process"),
    ("identify_pain", "Identify Pain"),
    ("champion", "Champion"),
    ("competition", "Competition"),
]

# (Befehl, Hilfetext) – Platzhalter, in den jeweiligen Schichten implementiert.
_PLACEHOLDER_COMMANDS: list[tuple[str, str]] = [
    ("ingest", "Text aufnehmen, klassifizieren, routen (Schicht 6)"),
    ("correct", "Korrektur speichern (Schicht 5)"),
    ("add-account", "Account anlegen (Schicht 5)"),
    ("add-deal", "Deal anlegen (Schicht 5)"),
    ("add-contact", "Kontakt anlegen (Schicht 5)"),
    ("list-deals", "Deals auflisten (Schicht 5)"),
    ("show-deal", "Deal-Details anzeigen (Schicht 5)"),
    ("research", "Deep-Research zu einem Account (Modul M1)"),
    ("account-map", "Stakeholder-Map (Modul M2)"),
    ("briefing", "Pipeline-Briefing (Modul M3)"),
    ("prep", "Meeting-Prep (Modul M4)"),
]


def _not_implemented(args: argparse.Namespace) -> int:
    log.warning("Befehl '%s' ist noch nicht implementiert.", args.command)
    return 1


def _render_snapshot(snapshot, label: str) -> str:
    """Terminal-Darstellung eines Snapshots: Ampel je Dimension, dann Gesamtbild."""
    lines = [f"━━━ MEDDPICC-Analyse: {label} ━━━", ""]
    for key, heading in _DIMENSION_ORDER:
        dim = snapshot.dimensions.get(key)
        if dim is None:
            continue
        ampel = _AMPEL.get(dim.confidence, "?")
        lines.append(f"{ampel} {heading} — {dim.confidence}")
        if dim.findings:
            lines.append(f"   {dim.findings}")
        if dim.gaps:
            lines.append(f"   Gaps: {'; '.join(dim.gaps)}")
        lines.append("")
    lines.append(f"Score: {snapshot.overall_score}/100 — {snapshot.score_rationale}")
    lines.append(f"Momentum: {snapshot.momentum}")
    if snapshot.deal_risks:
        lines.append("Risiken:")
        lines.extend(f"  {i}. {r}" for i, r in enumerate(snapshot.deal_risks, 1))
    if snapshot.next_best_questions:
        lines.append("Next Best Questions:")
        lines.extend(f"  {i}. {q}" for i, q in enumerate(snapshot.next_best_questions, 1))
    lines.append(f"Manager-Summary: {snapshot.summary_for_manager}")
    lines.append(f"(prompt_version={snapshot.prompt_version})")
    return "\n".join(lines)


def _save_snapshot_json(snapshot, stem: str, subdir: str = "") -> Path:
    target_dir = OUTPUTS_DIR / subdir if subdir else OUTPUTS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = target_dir / f"{stem}_{ts}.json"
    path.write_text(snapshot.model_dump_json(indent=2), encoding="utf-8")
    return path


def cmd_analyze(args: argparse.Namespace) -> int:
    """analyze <datei.txt> [--deal <name>] — Notes -> MEDDPICC-Snapshot."""
    from src.agents.meddpicc.agent import analyze  # lazy: API-Deps nur bei Bedarf

    notes_path = Path(args.file)
    if not notes_path.is_file():
        log.error("Datei nicht gefunden: %s", notes_path)
        return 1
    label = args.deal or notes_path.stem
    snapshot = analyze(notes_path.read_text(encoding="utf-8"))
    print(_render_snapshot(snapshot, label))
    saved = _save_snapshot_json(snapshot, notes_path.stem)
    print(f"\nJSON gespeichert: {saved}")
    return 0


def cmd_eval(args: argparse.Namespace) -> int:
    """eval — Golden-Set qualitativ: Ist vs. Soll je Deal (keine Gesamtzahl, Befund 2.3)."""
    from src.agents.meddpicc.agent import analyze
    from src.agents.meddpicc.evaluation import concat_notes, find_golden_cases, render_comparison
    from src.agents.meddpicc.prompts import PROMPT_VERSION

    cases = find_golden_cases(GOLDEN_DIR, NOTES_DIR)
    if not cases:
        log.error("Keine *.expected.md in %s gefunden.", GOLDEN_DIR)
        return 1
    print(f"Golden-Set-Eval — {len(cases)} Deals, prompt_version={PROMPT_VERSION}")
    print("(qualitativer Vergleich; Einzelmetrik erst ab >=20 Beispielen — Befund 2.3)\n")
    for expected, note_files in cases:
        snapshot = analyze(concat_notes(note_files))
        print(render_comparison(expected, snapshot))
        saved = _save_snapshot_json(snapshot, expected.account, subdir="eval")
        print(f"  volle Analyse: {saved}\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sales-os",
        description="Sales OS – AI-natives Sales-Betriebssystem.",
    )
    sub = parser.add_subparsers(dest="command", metavar="<befehl>")

    p_analyze = sub.add_parser("analyze", help="Notes -> MEDDPICC-Analyse (Terminal + JSON nach outputs/)")
    p_analyze.add_argument("file", help="Pfad zur Notes-Datei (.txt)")
    p_analyze.add_argument("--deal", help="Deal-Name als Label (DB kommt in Schicht 5)")
    p_analyze.set_defaults(func=cmd_analyze)

    p_eval = sub.add_parser("eval", help="Golden-Set: Ist vs. Soll qualitativ vergleichen")
    p_eval.set_defaults(func=cmd_eval)

    for name, help_text in _PLACEHOLDER_COMMANDS:
        p = sub.add_parser(name, help=help_text)
        p.set_defaults(func=_not_implemented)
    return parser


def main(argv: list[str] | None = None) -> int:
    setup_logging()
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
