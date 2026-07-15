"""Repository: Corrections (Feedback-SPEICHER — Sammlung ab Tag 1).

Die Injektion in Analysen bleibt bis nach M4 zurueckgestellt (CLAUDE.md,
Bewusste Entscheidung — erst Fehlermuster kennen, dann Mechanik; KEIN
Feature-Flag, Befund 1.4: die Mechanik wird gebaut, wenn sie aktiviert wird).
"""
from __future__ import annotations

from src.domain.correction import Correction
from src.repository import db


def save_correction(correction: Correction) -> Correction:
    with db.connect() as conn:
        conn.execute(
            """INSERT INTO corrections (id, deal_id, agent, field_path,
               original_value, corrected_value, comment, created_at)
               VALUES (:id, :deal_id, :agent, :field_path,
               :original_value, :corrected_value, :comment, :created_at)""",
            correction.model_dump(mode="json"),
        )
    return correction


def resolve_field_path(data: dict, field_path: str):
    """Loest 'dimensions.champion.confidence' in einem Snapshot-Dict auf (None wenn unaufloesbar)."""
    node = data
    for part in field_path.split("."):
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return None
    return node


def record_correction(
    deal_id: str, agent: str, field_path: str, corrected_value: str, comment: str = ""
) -> Correction:
    """Speichert eine Korrektur; original_value wird aus dem letzten Snapshot aufgeloest.

    Gemeinsame Funktion fuer CLI (`correct`) und API (POST /corrections) —
    Endpoints sind duenne Haut ueber denselben Funktionen (CLAUDE.md).
    """
    from src.repository.snapshots import get_latest_snapshot  # lokal: Zyklusvermeidung

    snapshot = get_latest_snapshot(deal_id)
    original = None
    if snapshot is not None:
        original = resolve_field_path(snapshot.model_dump(mode="json"), field_path)
    return save_correction(Correction(
        deal_id=deal_id, agent=agent, field_path=field_path,
        original_value="" if original is None else str(original),
        corrected_value=corrected_value, comment=comment,
    ))


def get_corrections(deal_id: str, agent: str | None = None) -> list[Correction]:
    query = "SELECT * FROM corrections WHERE deal_id = ?"
    params: list = [deal_id]
    if agent is not None:
        query += " AND agent = ?"
        params.append(agent)
    query += " ORDER BY created_at"
    with db.connect() as conn:
        rows = conn.execute(query, params).fetchall()
    return [Correction(**dict(r)) for r in rows]
