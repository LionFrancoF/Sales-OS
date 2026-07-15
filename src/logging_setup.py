"""Standardisiertes Logging (nie print).

Einmal am CLI-/API-Einstieg `setup_logging()` aufrufen. Bewusst minimal:
ein Format, ein Root-Handler. Kein Cost-/Metadaten-Overbau (P-1 Befund 1.1) —
LLM-Calls werden später als einzelne INFO-Zeile geloggt.
"""
from __future__ import annotations

import logging

_DEFAULT_FORMAT = "%(asctime)s %(levelname)-7s %(name)s | %(message)s"


def setup_logging(level: int = logging.INFO) -> None:
    """Konfiguriert den Root-Logger einmalig (idempotent via basicConfig)."""
    logging.basicConfig(level=level, format=_DEFAULT_FORMAT)
