"""Sales OS – CLI-Einstiegspunkt (P0: nur Gerüst).

Nur Struktur, keine Logik. Jeder Befehl ist ein Platzhalter und wird in seiner
Schicht/Modul implementiert (siehe CLAUDE.md / ARCHITECTURE.md).

Aufruf: python -m src.cli --help
"""
from __future__ import annotations

import argparse
import logging

from src.logging_setup import setup_logging

log = logging.getLogger("sales_os.cli")

# (Befehl, Hilfetext) – Platzhalter, in den jeweiligen Schichten implementiert.
_PLACEHOLDER_COMMANDS: list[tuple[str, str]] = [
    ("analyze", "Notes -> MEDDPICC-Analyse (Schicht 4)"),
    ("ingest", "Text aufnehmen, klassifizieren, routen (Schicht 6)"),
    ("eval", "Golden-Set-Auswertung (Schicht 4)"),
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
    log.warning("Befehl '%s' ist noch nicht implementiert (Gerüst P0).", args.command)
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sales-os",
        description="Sales OS – AI-natives Sales-Betriebssystem (Gerüst P0).",
    )
    sub = parser.add_subparsers(dest="command", metavar="<befehl>")
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
