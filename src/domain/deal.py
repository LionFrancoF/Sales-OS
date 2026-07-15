"""Deal-Aggregat: eine Verkaufschance bei einem Account.

win_probability wird bei fehlender Angabe automatisch aus der Stage abgeleitet
(Default-Win-% aus settings.STAGE_GATES, der einzigen Quelle der Wahrheit) und
ist ueberschreibbar. settings.py ist Querschnitt (keine Schicht), daher als
Import in der Domain erlaubt.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.config.settings import STAGE_GATES

DealStage = Literal[
    "PROSPECT", "DISCOVERY", "EVALUATION", "PROPOSAL", "NEGOTIATION", "VERBAL", "CLOSED_WON", "CLOSED_LOST"
]
Framework = Literal["MEDDICC", "MEDDPICC"]


class Deal(BaseModel):
    """Eine Verkaufschance mit Stage, Win-Wahrscheinlichkeit und Rahmendaten."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: str(uuid4()), description="Eindeutige ID (uuid4).")
    account_id: str = Field(description="Zugehoeriger Account (Pflichtfeld).")
    name: str = Field(description="Deal-Name (Pflichtfeld).")
    stage: DealStage = Field(default="PROSPECT", description="Aktuelle Pipeline-Stage.")
    win_probability: int | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Win-Wahrscheinlichkeit in %. Wird aus der Stage abgeleitet, wenn nicht gesetzt; ueberschreibbar.",
    )
    amount_estimate: float | None = Field(default=None, ge=0, description="Geschaetztes Volumen, optional.")
    expected_close: datetime | None = Field(default=None, description="Erwartetes Abschlussdatum, optional.")
    framework_override: Framework | None = Field(
        default=None, description="Erzwingt ein Framework (MEDDICC/MEDDPICC); hat Vorrang vor der Analyzer-Wahl."
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Erstellzeitpunkt (UTC).")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Letzte Aenderung (UTC).")

    @model_validator(mode="after")
    def _derive_win_probability(self) -> "Deal":
        """Leitet win_probability aus der Stage ab, wenn nicht explizit gesetzt."""
        if self.win_probability is None:
            self.win_probability = STAGE_GATES[self.stage]["win"]
        return self
