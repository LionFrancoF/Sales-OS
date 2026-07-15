"""Repository: Activities (append-only, raw_text_hash UNIQUE = Idempotenz-Basis)."""
from __future__ import annotations

import sqlite3

from src.domain.activity import Activity
from src.repository import db


def save_activity(activity: Activity) -> Activity:
    """Speichert eine Activity. Wirft ValueError bei exaktem Duplikat (Hash)."""
    try:
        with db.connect() as conn:
            conn.execute(
                """INSERT INTO activities (id, deal_id, type, occurred_at, raw_text,
                   raw_text_hash, summary, source)
                   VALUES (:id, :deal_id, :type, :occurred_at, :raw_text,
                   :raw_text_hash, :summary, :source)""",
                activity.model_dump(mode="json"),
            )
    except sqlite3.IntegrityError as e:
        if "raw_text_hash" in str(e):
            existing = get_activity_by_hash(activity.raw_text_hash)
            raise ValueError(
                f"Bereits verarbeitet am {existing.occurred_at:%Y-%m-%d} (Activity {existing.id})."
            ) from e
        raise
    return activity


def get_activity_by_hash(raw_text_hash: str) -> Activity:
    with db.connect() as conn:
        row = conn.execute(
            "SELECT * FROM activities WHERE raw_text_hash = ?", (raw_text_hash,)
        ).fetchone()
    if row is None:
        raise LookupError(f"Keine Activity mit Hash {raw_text_hash[:12]}…")
    return Activity(**dict(row))


def list_all_activities() -> list[Activity]:
    """Alle Activities (CSV-Export, P7)."""
    with db.connect() as conn:
        rows = conn.execute("SELECT * FROM activities ORDER BY occurred_at").fetchall()
    return [Activity(**dict(r)) for r in rows]


def list_activities(deal_id: str) -> list[Activity]:
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT * FROM activities WHERE deal_id = ? ORDER BY occurred_at", (deal_id,)
        ).fetchall()
    return [Activity(**dict(r)) for r in rows]
