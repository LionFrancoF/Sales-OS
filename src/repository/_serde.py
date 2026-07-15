"""Interne Serialisierungs-Helfer des Repositories (kein oeffentlicher Vertrag)."""
from __future__ import annotations

import json
from typing import Any


def dump_json(value: Any) -> str:
    """Deterministisches JSON fuer JSON-Spalten (sort_keys: stabile Bytes)."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def load_json(text: str | None, default: Any) -> Any:
    return json.loads(text) if text else default
