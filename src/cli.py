"""Sales OS – CLI-Einstiegspunkt.

Implementiert: analyze, eval (P4); add-account, add-deal, add-contact,
list-deals, show-deal, correct (P5). Uebrige Befehle sind Platzhalter.
Bewusst KEIN compare-Befehl (Befund 1.8). DB = einzige Quelle der Wahrheit
fuer Snapshots bekannter Deals (Befund 4.4); outputs/-JSON nur noch fuer
Analysen ohne DB-Deal und fuer eval-Leseartefakte.

Aufruf: python -m src.cli --help
"""
from __future__ import annotations

import argparse
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

_PLACEHOLDER_COMMANDS: list[tuple[str, str]] = [
    ("research", "Deep-Research zu einem Account (Modul M1)"),
    ("account-map", "Stakeholder-Map (Modul M2)"),
    ("briefing", "Pipeline-Briefing (Modul M3)"),
    ("prep", "Meeting-Prep (Modul M4)"),
]


def _not_implemented(args: argparse.Namespace) -> int:
    log.warning("Befehl '%s' ist noch nicht implementiert.", args.command)
    return 1


# ---------------------------------------------------------------- Rendering

def _render_snapshot(snapshot, label: str) -> str:
    lines = [f"━━━ MEDDPICC-Analyse: {label} ━━━", ""]
    for key, heading in _DIMENSION_ORDER:
        dim = snapshot.dimensions.get(key)
        if dim is None:
            continue
        lines.append(f"{_AMPEL.get(dim.confidence, '?')} {heading} — {dim.confidence}")
        if dim.findings:
            lines.append(f"   {dim.findings}")
        if dim.gaps:
            lines.append(f"   Gaps: {'; '.join(dim.gaps)}")
        lines.append("")
    bonus = f" (davon Signal-Bonus: +{snapshot.signal_bonus})" if snapshot.signal_bonus else ""
    lines.append(f"Score: {snapshot.overall_score}/100{bonus} — {snapshot.score_rationale}")
    lines.append(f"Momentum: {snapshot.momentum} — {snapshot.momentum_rationale}")
    if snapshot.deal_risks:
        lines.append("Risiken:")
        lines.extend(f"  {i}. {r}" for i, r in enumerate(snapshot.deal_risks, 1))
    if snapshot.next_best_questions:
        lines.append("Next Best Questions:")
        lines.extend(f"  {i}. {q}" for i, q in enumerate(snapshot.next_best_questions, 1))
    lines.append(f"Manager-Summary: {snapshot.summary_for_manager}")
    lines.append(f"(prompt_version={snapshot.prompt_version})")
    return "\n".join(lines)


def _render_snapshot_short(snapshot) -> str:
    ampeln = " ".join(
        _AMPEL.get(snapshot.dimensions[k].confidence, "?")
        for k, _ in _DIMENSION_ORDER if k in snapshot.dimensions
    )
    return (
        f"  Snapshot {snapshot.created_at:%Y-%m-%d %H:%M} — Score {snapshot.overall_score}/100, "
        f"Momentum {snapshot.momentum}\n  {ampeln}\n  {snapshot.summary_for_manager}"
    )


def _save_snapshot_json(snapshot, stem: str, subdir: str = "") -> Path:
    target_dir = OUTPUTS_DIR / subdir if subdir else OUTPUTS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = target_dir / f"{stem}_{ts}.json"
    path.write_text(snapshot.model_dump_json(indent=2), encoding="utf-8")
    return path


# ---------------------------------------------------------------- P4-Befehle

def cmd_analyze(args: argparse.Namespace) -> int:
    """analyze <datei.txt> [--deal <name>] — Notes -> Snapshot (DB bei bekanntem Deal)."""
    from src.agents.meddpicc.agent import analyze
    from src.repository import deals as deals_repo
    from src.repository import snapshots as snapshots_repo

    notes_path = Path(args.file)
    if not notes_path.is_file():
        log.error("Datei nicht gefunden: %s", notes_path)
        return 1

    deal = None
    previous = None
    if args.deal:
        try:
            deal = deals_repo.get_deal_by_name(args.deal)
            previous = snapshots_repo.get_latest_snapshot(deal.id)
        except LookupError:
            log.error("Deal '%s' nicht in der DB — erst `add-deal`, oder ohne --deal analysieren.", args.deal)
            return 1

    snapshot = analyze(notes_path.read_text(encoding="utf-8"), previous_snapshot=previous, deal=deal)
    print(_render_snapshot(snapshot, args.deal or notes_path.stem))

    if deal is not None:
        snapshots_repo.save_snapshot(snapshot)
        print(f"\nSnapshot in DB gespeichert (Deal '{deal.name}', append-only"
              f"{', Vorgaenger beruecksichtigt' if previous else ', Erstbewertung'}).")
    else:
        saved = _save_snapshot_json(snapshot, notes_path.stem)
        print(f"\nKein DB-Deal — JSON gespeichert: {saved}")
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


# ---------------------------------------------------------------- P5-Befehle

def cmd_add_account(args: argparse.Namespace) -> int:
    from src.domain.account import Account
    from src.repository.accounts import save_account

    account = save_account(Account(
        name=args.name, domain=args.domain, industry=args.industry, size_estimate=args.size,
    ))
    print(f"Account angelegt: {account.name} ({account.id})")
    return 0


def cmd_add_deal(args: argparse.Namespace) -> int:
    from src.domain.deal import Deal
    from src.repository.accounts import get_account_by_name
    from src.repository.deals import save_deal

    try:
        account = get_account_by_name(args.account)
    except LookupError as e:
        log.error("%s — erst `add-account`.", e)
        return 1
    deal = save_deal(Deal(account_id=account.id, name=args.name, stage=args.stage))
    print(f"Deal angelegt: {deal.name} @ {account.name} — Stage {deal.stage}, Win {deal.win_probability}%")
    return 0


def cmd_add_contact(args: argparse.Namespace) -> int:
    from src.domain.contact import Contact
    from src.repository.accounts import get_account_by_name
    from src.repository.contacts import find_contact_candidates, save_contact

    try:
        account = get_account_by_name(args.account)
    except LookupError as e:
        log.error("%s — erst `add-account`.", e)
        return 1
    candidates = find_contact_candidates(account.id, args.name)
    if candidates and not args.force:
        print(f"Moegliche Dublette(n) fuer '{args.name}' bei {account.name}:")
        for contact, score in candidates:
            print(f"  {score:.2f}  {contact.name} ({contact.title or 'ohne Titel'})")
        print("Anlegen erzwingen mit --force.")
        return 1
    contact = save_contact(Contact(
        account_id=account.id, name=args.name, title=args.title, email=args.email,
        role_in_deal=args.role, influence=args.influence,
    ))
    print(f"Kontakt angelegt: {contact.name} @ {account.name} ({contact.role_in_deal})")
    return 0


def cmd_list_deals(args: argparse.Namespace) -> int:
    from src.repository.accounts import get_account
    from src.repository.deals import list_deals
    from src.repository.snapshots import get_latest_snapshot

    deals = list_deals()
    if not deals:
        print("Keine Deals in der DB.")
        return 0
    for deal in deals:
        account = get_account(deal.account_id)
        snap = get_latest_snapshot(deal.id)
        extra = f"Score {snap.overall_score}, {snap.momentum}" if snap else "kein Snapshot"
        print(f"  {deal.name:<28} {account.name:<22} {deal.stage:<12} Win {deal.win_probability}%  ({extra})")
    return 0


def cmd_show_deal(args: argparse.Namespace) -> int:
    from src.repository.accounts import get_account
    from src.repository.contacts import list_contacts
    from src.repository.corrections import get_corrections
    from src.repository.deals import get_deal_by_name
    from src.repository.snapshots import get_latest_snapshot

    try:
        deal = get_deal_by_name(args.name)
    except LookupError as e:
        log.error("%s", e)
        return 1
    account = get_account(deal.account_id)
    print(f"━━━ {deal.name} @ {account.name} ━━━")
    print(f"Stage: {deal.stage} | Win: {deal.win_probability}% | angelegt {deal.created_at:%Y-%m-%d}")

    contacts = list_contacts(account.id)
    if contacts:
        print("\nKontakte:")
        for c in contacts:
            print(f"  {c.name:<22} {c.title or '—':<24} {c.role_in_deal:<15} "
                  f"Einfluss {c.influence:<9} {c.disposition:<10} Beziehung {c.relationship_strength}")

    snap = get_latest_snapshot(deal.id)
    print("\nLetzter Snapshot:" if snap else "\nNoch kein Snapshot — `analyze <datei> --deal ...`.")
    if snap:
        print(_render_snapshot_short(snap))

    corrections = get_corrections(deal.id)
    if corrections:
        print(f"\nKorrekturen ({len(corrections)}, gesammelt — Injektion nach M4):")
        for corr in corrections:
            print(f"  {corr.created_at:%Y-%m-%d} {corr.field_path}: '{corr.original_value}' -> "
                  f"'{corr.corrected_value}'" + (f" ({corr.comment})" if corr.comment else ""))
    return 0


def cmd_correct(args: argparse.Namespace) -> int:
    """correct <deal> --field <pfad> --value <neu> [--comment] — Feedback sammeln."""
    from src.agents.meddpicc.agent import AGENT_NAME
    from src.repository.corrections import record_correction
    from src.repository.deals import get_deal_by_name

    try:
        deal = get_deal_by_name(args.deal)
    except LookupError as e:
        log.error("%s", e)
        return 1
    correction = record_correction(deal.id, AGENT_NAME, args.field, args.value, args.comment or "")
    print(f"Korrektur gespeichert: {correction.field_path}: "
          f"'{correction.original_value}' -> '{correction.corrected_value}'")
    print("(Sammlung ab Tag 1; Injektion in Analysen bewusst erst nach M4 — CLAUDE.md)")
    if args.golden:
        path = _export_golden_candidate(deal)
        if path:
            print(f"Golden-Set-Kandidat exportiert: {path}")
            print("(Ist-Werte als Vorlage — pruefen/korrigieren, dann als <slug>_NN.expected.md verschieben:")
            print(" echte Kundendaten -> tests/golden_set/private/ (gitignored, + export-notes),")
            print(" synthetische Faelle -> tests/golden_set/)")
    return 0


def cmd_export_notes(args: argparse.Namespace) -> int:
    """export-notes <deal> — Roh-Notes eines echten Deals fuer die Golden-Set-Privat-Ablage exportieren."""
    from src.repository.deals import get_deal_by_name

    try:
        deal = get_deal_by_name(args.deal)
    except LookupError as e:
        log.error("%s", e)
        return 1
    target_dir = Path(__file__).resolve().parent.parent / "tests" / "sample_notes" / "private"
    written = _export_notes(deal, target_dir)
    if not written:
        log.error("Keine Activities mit Roh-Text fuer '%s' — nichts zu exportieren.", deal.name)
        return 1
    for p in written:
        print(f"Note exportiert: {p}")
    slug = deal.name.lower().replace(" ", "_")
    print(f"(gitignored; passende Golden-Referenz als {slug}_{len(written):02d}.expected.md "
          f"nach tests/golden_set/private/ — der Eval findet beides automatisch)")
    return 0


def cmd_advise(args: argparse.Namespace) -> int:
    """advise — der Berater: freie Sales-Fragen durch Lions Brille (read-only)."""
    from src.agents.advisor.agent import advise

    topics = [t.strip() for t in args.topics.split(",")] if args.topics else None

    if args.interactive:
        print("Berater-Modus (interaktiv). Leere Eingabe oder 'exit' beendet.")
        history: list[dict] = []
        first = True
        while True:
            try:
                question = input("\nDu: ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not question or question.lower() in {"exit", "quit"}:
                break
            try:
                answer, history = advise(
                    question,
                    deal_name=args.deal if first else None,
                    pipeline=args.pipeline if first else False,
                    topics=topics,
                    history=history or None,
                )
            except LookupError as e:
                log.error("%s", e)
                return 1
            first = False
            print(f"\nBerater:\n{answer}")
        return 0

    if not args.question:
        log.error("Frage fehlt. Nutzung: advise \"<frage>\" [--deal X | --pipeline] oder advise -i")
        return 1
    try:
        answer, _ = advise(
            args.question, deal_name=args.deal, pipeline=args.pipeline, topics=topics
        )
    except LookupError as e:
        log.error("%s", e)
        return 1
    print(answer)
    return 0


def _export_notes(deal, target_dir: Path) -> list[Path]:
    """Schreibt die Roh-Texte aller Activities eines Deals chronologisch als
    <slug>_NN.txt in target_dir (Privat-Ablage: echte Kundendaten, gitignored).
    Gegenstueck zu _export_golden_candidate — zusammen ergeben sie einen
    eval-faehigen Fall aus einem echten Deal."""
    from src.repository.activities import list_activities

    activities = [a for a in list_activities(deal.id) if a.raw_text.strip()]
    if not activities:
        return []
    activities.sort(key=lambda a: a.occurred_at)
    target_dir.mkdir(parents=True, exist_ok=True)
    slug = deal.name.lower().replace(" ", "_")
    written: list[Path] = []
    for i, activity in enumerate(activities, 1):
        path = target_dir / f"{slug}_{i:02d}.txt"
        path.write_text(activity.raw_text, encoding="utf-8")
        written.append(path)
    return written


def _export_golden_candidate(deal) -> Path | None:
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
    for key, heading in _DIMENSION_ORDER:
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
    target_dir = Path(__file__).resolve().parent.parent / "tests" / "golden_set_candidates"
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f"{deal.name.lower().replace(' ', '_')}_{ts}.expected.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


# ---------------------------------------------------------------- P6-Befehle

def _interactive_ask(question: str, options: list[str]) -> int | None:
    """CLI-Nachfrage; None bei Nicht-Interaktivitaet (EOF) oder ungueltiger Eingabe."""
    print(f"\n{question}")
    for i, option in enumerate(options, 1):
        print(f"  [{i}] {option}")
    try:
        raw = input("Auswahl: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return None
    if raw.isdigit() and 1 <= int(raw) <= len(options):
        return int(raw) - 1
    return None


def cmd_ingest(args: argparse.Namespace) -> int:
    """ingest <datei.txt|-> [--deal <name>] — kompletter Ingestion-Durchlauf."""
    import sys

    from src.orchestrator.ingest import process_note

    if args.file == "-":
        text = sys.stdin.read()
        source = "stdin"
    else:
        notes_path = Path(args.file)
        if not notes_path.is_file():
            log.error("Datei nicht gefunden: %s", notes_path)
            return 1
        text = notes_path.read_text(encoding="utf-8")
        source = notes_path.name

    try:
        report = process_note(text, deal_name=args.deal, source=source, ask=_interactive_ask)
    except (ValueError, LookupError) as e:
        log.error("%s", e)
        return 1

    if report.aborted:
        print(f"⏭  {report.aborted}")
        return 0

    print(f"━━━ Ingest: {source} ━━━")
    print(f"Zuordnung: {report.deal_name} (Confidence {report.confidence:.2f}, {report.method or 'auto'})")
    print(f"Typ: {report.activity_type} | Signale: {', '.join(report.signals) or '—'}")
    print("Ausgefuehrt:")
    for action in report.actions:
        print(f"  • {action}")
    if report.changes:
        print("Veraendert (vs. Vorgaenger-Snapshot):")
        for change in report.changes:
            print(f"  Δ {change}")
    return 0


def cmd_set_stage(args: argparse.Namespace) -> int:
    """set-stage <deal> <stage> [--reason] — Stage-Wechsel; Won/Lost-Grund festhalten (2.7)."""
    from src.repository.deals import get_deal_by_name, update_deal_stage

    try:
        deal = get_deal_by_name(args.deal)
    except LookupError as e:
        log.error("%s", e)
        return 1
    if args.stage in ("CLOSED_WON", "CLOSED_LOST") and not args.reason:
        log.error("Bei %s ist --reason Pflicht — das Warum ist nicht nachholbar (Befund 2.7).", args.stage)
        return 1
    updated = update_deal_stage(deal.id, args.stage, close_reason=args.reason)
    print(f"{updated.name}: {deal.stage} → {updated.stage} (Win {updated.win_probability}%)")
    if updated.close_reason and updated.stage in ("CLOSED_WON", "CLOSED_LOST"):
        print(f"Grund festgehalten: {updated.close_reason}")
    return 0


# ---------------------------------------------------------------- Parser

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sales-os", description="Sales OS – AI-natives Sales-Betriebssystem.")
    sub = parser.add_subparsers(dest="command", metavar="<befehl>")

    p = sub.add_parser("analyze", help="Notes -> MEDDPICC-Analyse (DB bei bekanntem Deal)")
    p.add_argument("file", help="Pfad zur Notes-Datei (.txt)")
    p.add_argument("--deal", help="Deal-Name in der DB (laedt Vorgaenger-Snapshot, speichert append-only)")
    p.set_defaults(func=cmd_analyze)

    p = sub.add_parser("eval", help="Golden-Set: Ist vs. Soll qualitativ vergleichen")
    p.set_defaults(func=cmd_eval)

    p = sub.add_parser("ingest", help="Text aufnehmen: klassifizieren, zuordnen, routen (P6)")
    p.add_argument("file", help="Pfad zur Notes-Datei oder '-' fuer stdin")
    p.add_argument("--deal", help="Deal-Name — uebersteuert die automatische Zuordnung")
    p.set_defaults(func=cmd_ingest)

    p = sub.add_parser("set-stage", help="Deal-Stage wechseln; bei CLOSED_* mit --reason (Won/Lost)")
    p.add_argument("deal", help="Deal-Name")
    p.add_argument("stage", choices=["PROSPECT", "DISCOVERY", "EVALUATION", "PROPOSAL",
                                     "NEGOTIATION", "VERBAL", "CLOSED_WON", "CLOSED_LOST"])
    p.add_argument("--reason", help="Warum gewonnen/verloren (Pflicht bei CLOSED_*)")
    p.set_defaults(func=cmd_set_stage)

    p = sub.add_parser("add-account", help="Account anlegen")
    p.add_argument("--name", required=True)
    p.add_argument("--domain")
    p.add_argument("--industry")
    p.add_argument("--size", help="Groessenschaetzung, z.B. '500-1000 MA'")
    p.set_defaults(func=cmd_add_account)

    p = sub.add_parser("add-deal", help="Deal anlegen")
    p.add_argument("account", help="Account-Name")
    p.add_argument("--name", required=True)
    p.add_argument("--stage", default="PROSPECT",
                   choices=["PROSPECT", "DISCOVERY", "EVALUATION", "PROPOSAL", "NEGOTIATION", "VERBAL", "CLOSED_WON", "CLOSED_LOST"])
    p.set_defaults(func=cmd_add_deal)

    p = sub.add_parser("add-contact", help="Kontakt anlegen (mit Dubletten-Schutz)")
    p.add_argument("account", help="Account-Name")
    p.add_argument("--name", required=True)
    p.add_argument("--title")
    p.add_argument("--email")
    p.add_argument("--role", default="UNKLAR",
                   choices=["ECONOMIC_BUYER", "CHAMPION", "COACH", "INFLUENCER", "BLOCKER", "USER", "UNKLAR"])
    p.add_argument("--influence", default="UNBEKANNT", choices=["HOCH", "MITTEL", "NIEDRIG", "UNBEKANNT"])
    p.add_argument("--force", action="store_true", help="trotz moeglicher Dublette anlegen")
    p.set_defaults(func=cmd_add_contact)

    p = sub.add_parser("list-deals", help="Deals auflisten")
    p.set_defaults(func=cmd_list_deals)

    p = sub.add_parser("show-deal", help="Deal-Details: Snapshot-Kurzfassung + Kontakte + Korrekturen")
    p.add_argument("name", help="Deal-Name")
    p.set_defaults(func=cmd_show_deal)

    p = sub.add_parser("correct", help="Korrektur zum letzten Snapshot speichern (Feedback-Loop)")
    p.add_argument("deal", help="Deal-Name")
    p.add_argument("--field", required=True, help="z.B. dimensions.champion.confidence")
    p.add_argument("--value", required=True, help="korrigierter Wert")
    p.add_argument("--comment", help="optionaler Kommentar")
    p.add_argument("--golden", action="store_true",
                   help="letzten Snapshot als Golden-Set-Kandidat exportieren (organisches Wachstum Richtung n>=20)")
    p.set_defaults(func=cmd_correct)

    p = sub.add_parser("export-notes",
                       help="Roh-Notes eines Deals in die Golden-Set-Privat-Ablage exportieren "
                            "(tests/sample_notes/private/, gitignored — echte Kundendaten)")
    p.add_argument("deal", help="Deal-Name")
    p.set_defaults(func=cmd_export_notes)

    p = sub.add_parser("advise",
                       help="Der Berater: freie Sales-Frage durch Lions Brille beantworten "
                            "(read-only; Kontext optional per --deal oder --pipeline)")
    p.add_argument("question", nargs="?", help="Die Frage (bei -i optional)")
    p.add_argument("--deal", help="Deal-Name: kompletter Deal-Kontext aus der DB")
    p.add_argument("--pipeline", action="store_true", help="Kompakt-Digest aller Deals als Kontext")
    p.add_argument("--topics", help="Kommagetrennte Topics: nur passende Playbook-Abschnitte laden")
    p.add_argument("-i", "--interactive", action="store_true",
                   help="Mehrrunden-Gespraech (Verlauf nur im Arbeitsspeicher)")
    p.set_defaults(func=cmd_advise)

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
