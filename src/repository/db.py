"""SQLite-Verbindung + Schema. EINZIGER Ort mit CREATE TABLE.

Regeln (CLAUDE.md):
- Das Repository ist der EINZIGE Datenbankzugang; Agenten importieren nie
  sqlite3 direkt.
- Snapshots, Activities und ContactHistory sind append-only — das Repository
  bietet dafuer schlicht keine update/delete-Funktionen an.
- raw_text_hash ist UNIQUE auf activities (Idempotenz-Basis fuer P6).
- Bewusst KEINE events- und KEINE llm_calls-Tabelle (Befunde 1.2/1.1,
  Entscheidungen Lion) und kein Migrations-Geruest (Befund 2.5: V1 =
  DB-neu-Konvention, siehe settings.py).

Komplexe Strukturen (dimensions, Listen) liegen als JSON-Text in einer
Spalte; abfragbare Kernfelder sind echte Spalten.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from src.config import settings

# Modul-Zustand: Tests setzen einen tmp-Pfad via set_db_path().
_db_path: Path = settings.DB_PATH

_SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    domain TEXT,
    industry TEXT,
    size_estimate TEXT,
    research_profile TEXT,          -- JSON
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS contacts (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES accounts(id),
    name TEXT NOT NULL,
    title TEXT,
    email TEXT,
    phone TEXT,
    linkedin_url TEXT,
    role_in_deal TEXT NOT NULL,
    influence TEXT NOT NULL,
    disposition TEXT NOT NULL,
    relationship_strength TEXT NOT NULL,
    last_touchpoint TEXT,
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS deals (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES accounts(id),
    name TEXT NOT NULL,
    stage TEXT NOT NULL,
    win_probability INTEGER,
    amount_estimate REAL,
    expected_close TEXT,
    framework_override TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- append-only
CREATE TABLE IF NOT EXISTS activities (
    id TEXT PRIMARY KEY,
    deal_id TEXT NOT NULL REFERENCES deals(id),
    type TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    raw_text_hash TEXT NOT NULL UNIQUE,
    summary TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL DEFAULT ''
);

-- append-only, versioniert ueber created_at
CREATE TABLE IF NOT EXISTS snapshots (
    id TEXT PRIMARY KEY,
    deal_id TEXT NOT NULL REFERENCES deals(id),
    created_at TEXT NOT NULL,
    source_activity_ids TEXT NOT NULL,   -- JSON-Liste
    framework TEXT NOT NULL,
    framework_rationale TEXT NOT NULL DEFAULT '',
    dimensions TEXT NOT NULL,            -- JSON: key -> DimensionAssessment
    overall_score INTEGER NOT NULL,
    score_rationale TEXT NOT NULL DEFAULT '',
    momentum TEXT NOT NULL,
    deal_risks TEXT NOT NULL,            -- JSON-Liste
    next_best_questions TEXT NOT NULL,   -- JSON-Liste
    summary_for_manager TEXT NOT NULL DEFAULT '',
    prompt_version TEXT NOT NULL DEFAULT ''
);

-- append-only (Feedback-Speicher; Injektion bis nach M4 zurueckgestellt)
CREATE TABLE IF NOT EXISTS corrections (
    id TEXT PRIMARY KEY,
    deal_id TEXT NOT NULL REFERENCES deals(id),
    agent TEXT NOT NULL,
    field_path TEXT NOT NULL,
    original_value TEXT NOT NULL,
    corrected_value TEXT NOT NULL,
    comment TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);

-- append-only (nie stilles Ueberschreiben von Alignment-Feldern)
CREATE TABLE IF NOT EXISTS contact_history (
    id TEXT PRIMARY KEY,
    contact_id TEXT NOT NULL REFERENCES contacts(id),
    field TEXT NOT NULL,
    old_value TEXT NOT NULL,
    new_value TEXT NOT NULL,
    source TEXT NOT NULL,
    ts TEXT NOT NULL
);
"""


def set_db_path(path: Path) -> None:
    """Setzt den DB-Pfad (Tests: tmp_path; Default: settings.DB_PATH)."""
    global _db_path
    _db_path = path


def get_db_path() -> Path:
    return _db_path


@contextmanager
def connect():
    """Verbindung mit Schema-Garantie, Row-Factory und Foreign Keys."""
    conn = sqlite3.connect(_db_path)
    try:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(_SCHEMA)
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
