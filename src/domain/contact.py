"""Contact-Aggregat: eine Person bei einem Account, inkl. Stakeholder-Alignment.

Die Alignment-Felder tragen die politische Einordnung im Deal. Default ist
jeweils die "unbekannt"-Variante — nichts wird ohne Beleg behauptet
(Confidence-Philosophie: fehlt es in den Notes -> UNBEKANNT).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

RoleInDeal = Literal["ECONOMIC_BUYER", "CHAMPION", "COACH", "INFLUENCER", "BLOCKER", "USER", "UNKLAR"]
Influence = Literal["HOCH", "MITTEL", "NIEDRIG", "UNBEKANNT"]
Disposition = Literal["PROMOTER", "NEUTRAL", "SKEPTIKER", "GEGNER", "UNBEKANNT"]
RelationshipStrength = Literal["STARK", "AUFBAUEND", "SCHWACH", "KEIN_KONTAKT"]


class Contact(BaseModel):
    """Ein Ansprechpartner/Stakeholder bei einem Account."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: str(uuid4()), description="Eindeutige ID (uuid4).")
    account_id: str = Field(description="Zugehoeriger Account (Pflichtfeld).")
    name: str = Field(description="Vollstaendiger Name (Pflichtfeld).")
    title: str | None = Field(default=None, description="Jobtitel/Funktion, falls bekannt.")
    email: str | None = Field(default=None, description="E-Mail, optional.")
    phone: str | None = Field(default=None, description="Telefon, optional.")
    linkedin_url: str | None = Field(default=None, description="LinkedIn-Profil-URL, optional.")

    # --- Stakeholder-Alignment ---
    role_in_deal: RoleInDeal = Field(default="UNKLAR", description="Rolle im Buying-Circle.")
    influence: Influence = Field(default="UNBEKANNT", description="Einfluss auf die Kaufentscheidung.")
    disposition: Disposition = Field(default="UNBEKANNT", description="Haltung uns/dem Deal gegenueber.")
    relationship_strength: RelationshipStrength = Field(
        default="KEIN_KONTAKT", description="Staerke unserer Beziehung zur Person."
    )
    last_touchpoint: datetime | None = Field(default=None, description="Letzter Kontaktzeitpunkt, falls bekannt.")
    notes: str = Field(default="", description="Freitext-Notizen zur Person.")
