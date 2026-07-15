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
    ("ingest", "Text aufnehmen, klassifizieren, routen (Schicht 6)"),
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


def _resolve_field_path(data: dict, field_path: str):
    """Loest 'dimensions.champion.confidence' im Snapshot-Dict auf (None wenn unaufloesbar)."""
    node = data
    for part in field_path.split("."):
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return None
    return node


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
    from src.domain.correction import Correction
    from src.repository.corrections import save_correction
    from src.repository.deals import get_deal_by_name
    from src.repository.snapshots import get_latest_snapshot

    try:
        deal = get_deal_by_name(args.deal)
    except LookupError as e:
        log.error("%s", e)
        return 1
    snapshot = get_latest_snapshot(deal.id)
    original = None
    if snapshot is not None:
        original = _resolve_field_path(snapshot.model_dump(mode="json"), args.field)
        if original is None:
            log.warning("Feld-Pfad '%s' im letzten Snapshot nicht aufloesbar — original_value bleibt leer.", args.field)
    correction = save_correction(Correction(
        deal_id=deal.id, agent=AGENT_NAME, field_path=args.field,
        original_value="" if original is None else str(original),
        corrected_value=args.value, comment=args.comment or "",
    ))
    print(f"Korrektur gespeichert: {correction.field_path}: "
          f"'{correction.original_value}' -> '{correction.corrected_value}'")
    print("(Sammlung ab Tag 1; Injektion in Analysen bewusst erst nach M4 — CLAUDE.md)")
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
    p.set_defaults(func=cmd_correct)

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
