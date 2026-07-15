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
