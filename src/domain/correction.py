"""Correction-Aggregat: eine manuelle Korrektur als Grundlage des Feedback-Loops.

In P1 bewusst zurueckgestellt (Befund 1.10), jetzt in seiner Schicht (P5).
Wird ab jetzt GESAMMELT; die Injektion in Analysen bleibt bis nach M4
zurueckgestellt (CLAUDE.md: erst Fehlermuster kennen, dann Mechanik).
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class Correction(BaseModel):
    """Eine vom Nutzer korrigierte Feld-Bewertung (alt -> neu)."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: str(uuid4()), description="Eindeutige ID (uuid4).")
    deal_id: str = Field(description="Betroffener Deal (Pflichtfeld).")
    agent: str = Field(description="Agent, dessen Ausgabe korrigiert wurde (z.B. 'meddpicc_analyzer').")
    field_path: str = Field(description="Pfad zum korrigierten Feld, z.B. 'dimensions.champion.confidence'.")
    original_value: str = Field(description="Urspruenglicher Wert (serialisiert als String).")
    corrected_value: str = Field(description="Korrigierter Wert (serialisiert als String).")
    comment: str = Field(default="", description="Optionaler Kommentar zur Korrektur.")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Erstellzeitpunkt (UTC).")
