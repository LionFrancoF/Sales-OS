"""Activity-Aggregat: ein einzelnes Ereignis an einem Deal (append-only).

raw_text_hash wird bei fehlender Angabe aus raw_text abgeleitet (SHA-256).
Hinweis: die eigentliche Normalisierung vor dem Hash ist eine Ingestion-Aufgabe
(P6) — die Domain liefert nur einen simplen Content-Hash als Default und laesst
einen explizit gesetzten (normalisierten) Hash zu.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

ActivityType = Literal["CALL", "EMAIL", "MEETING", "NOTE", "DEMO", "OTHER"]


class Activity(BaseModel):
    """Ein Kontaktpunkt/Ereignis (Call, E-Mail, Meeting, Notiz, Demo, …)."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: str(uuid4()), description="Eindeutige ID (uuid4).")
    deal_id: str = Field(description="Zugehoeriger Deal (Pflichtfeld).")
    type: ActivityType = Field(description="Art der Aktivitaet (Pflichtfeld).")
    occurred_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Zeitpunkt des Ereignisses (UTC)."
    )
    raw_text: str = Field(description="Roh-Text der Notiz/Nachricht (Pflichtfeld).")
    raw_text_hash: str | None = Field(
        default=None, description="SHA-256 ueber raw_text. Wird abgeleitet, wenn nicht gesetzt (Idempotenz-Basis)."
    )
    summary: str = Field(default="", description="Kurzzusammenfassung, optional.")
    source: str = Field(default="", description="Herkunft, z.B. Dateiname oder 'manual'.")

    @model_validator(mode="after")
    def _derive_raw_text_hash(self) -> "Activity":
        """Setzt raw_text_hash = SHA-256(raw_text), wenn nicht explizit angegeben."""
        if self.raw_text_hash is None:
            self.raw_text_hash = hashlib.sha256(self.raw_text.encode("utf-8")).hexdigest()
        return self
