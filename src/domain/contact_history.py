"""ContactHistoryEntry: protokollierte Alignment-Aenderung an einem Kontakt.

CLAUDE.md-Datenmodell: Kontakt-Aenderungen werden NIE still ueberschrieben —
jede Alignment-Aenderung wird als append-only Eintrag (alt -> neu, Quelle,
Zeitpunkt) festgehalten.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class ContactHistoryEntry(BaseModel):
    """Eine protokollierte Feld-Aenderung an einem Kontakt (append-only)."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: str(uuid4()), description="Eindeutige ID (uuid4).")
    contact_id: str = Field(description="Betroffener Kontakt (Pflichtfeld).")
    field: str = Field(description="Geaendertes Feld, z.B. 'role_in_deal'.")
    old_value: str = Field(description="Alter Wert (serialisiert als String).")
    new_value: str = Field(description="Neuer Wert (serialisiert als String).")
    source: str = Field(description="Quelle der Aenderung, z.B. 'manual' oder Notiz-Referenz.")
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Zeitpunkt (UTC).")
