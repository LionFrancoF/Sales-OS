"""Account-Aggregat: die Zielorganisation, gegen die verkauft wird.

Wurzel des Datenmodells (Account -> Contacts -> Deals -> Activities -> Snapshots).
Reines Pydantic-Modell, keine Logik ausser Feld-Defaults.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class Account(BaseModel):
    """Eine Firma/Organisation als Verkaufsziel."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: str(uuid4()), description="Eindeutige ID (uuid4).")
    name: str = Field(description="Firmenname (Pflichtfeld).")
    domain: str | None = Field(default=None, description="Primaere Web-Domain, z.B. 'acme.com'.")
    industry: str | None = Field(default=None, description="Branche/Industrie, falls bekannt.")
    size_estimate: str | None = Field(default=None, description="Grobe Groessenschaetzung, z.B. '500-1000 MA'.")
    research_profile: dict | None = Field(
        default=None,
        description="Recherche-Profil. Wird in M1 ein typisiertes ResearchProfile; vorerst optionales dict.",
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Erstellzeitpunkt (UTC).")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Letzte Aenderung (UTC).")
