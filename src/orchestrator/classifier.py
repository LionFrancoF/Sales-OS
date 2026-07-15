"""Classifier: EIN Haiku-Call klassifiziert Text + extrahiert Entitaeten.

Bewusst ein einziger Call fuer Klassifizierung UND Personen-/Firmen-Extraktion
(P-1 Befund 4.6: weniger LLM-Stufen, weniger Latenz, weniger Glue).
Modell: settings.MODEL_CLASSIFY (Haiku) — Routine gehoert nicht auf Opus.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from src.agents import llm
from src.config import settings

RoleInDeal = Literal["ECONOMIC_BUYER", "CHAMPION", "COACH", "INFLUENCER", "BLOCKER", "USER"]
Influence = Literal["HOCH", "MITTEL", "NIEDRIG"]
Disposition = Literal["PROMOTER", "NEUTRAL", "SKEPTIKER", "GEGNER"]


class Signals(BaseModel):
    model_config = ConfigDict(extra="forbid")

    meddpicc_relevant: bool = Field(description="Enthaelt qualifizierungsrelevante Infos (Budget, Entscheider, Pain, Prozess, Wettbewerb ...).")
    neue_kontakte: bool = Field(description="Es werden Personen erwaehnt, die neu sein koennten.")
    stakeholder_update: bool = Field(description="Es gibt neue Infos zu Rolle/Haltung/Einfluss bekannter Personen.")
    next_steps: bool = Field(description="Konkrete naechste Schritte werden genannt.")
    termin_zusage: bool = Field(description="Ein Termin wurde zugesagt/vereinbart.")
    wettbewerb: bool = Field(description="Ein Wettbewerber wird erwaehnt oder ist im Spiel.")


class ClassifiedContact(BaseModel):
    """Eine erwaehnte Person; Alignment-Felder NUR wenn woertlich belegbar (sonst null)."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="Vollstaendiger Name, so praezise wie im Text moeglich.")
    title: str | None = Field(description="Jobtitel/Funktion, falls im Text genannt, sonst null.")
    role_in_deal: RoleInDeal | None = Field(description="NUR wenn die Rolle woertlich belegbar ist, sonst null (wird zu UNKLAR).")
    influence: Influence | None = Field(description="NUR wenn woertlich belegbar, sonst null (wird zu UNBEKANNT).")
    disposition: Disposition | None = Field(description="NUR wenn woertlich belegbar, sonst null (wird zu UNBEKANNT).")


class Classification(BaseModel):
    """Ergebnis des Classifier-Calls (ein Call: Typ + Signale + Extraktion)."""

    model_config = ConfigDict(extra="forbid")

    activity_type: Literal["CALL", "EMAIL", "MEETING", "NOTE", "DEMO", "OTHER"]
    summary: str = Field(description="Eine kompakte deutsche Zusammenfassung (1-2 Saetze).")
    signals: Signals
    mentioned_people: list[str] = Field(description="Alle erwaehnten Personennamen.")
    mentioned_companies: list[str] = Field(description="Alle erwaehnten Firmennamen.")
    contacts: list[ClassifiedContact] = Field(
        description="Erwaehnte Personen des KUNDEN mit belegbaren Details (nicht der Verkaeufer selbst)."
    )
    next_steps: list[str] = Field(description="Konkrete naechste Schritte/Terminzusagen aus dem Text, sonst leer.")


SYSTEM_PROMPT = """Du bist der Ingestion-Classifier von "Sales OS". Du bekommst rohe, \
messy Sales-Notizen (Stichpunkte, Denglisch, Tippfehler) und lieferst eine praezise \
Klassifikation plus Entitaeten-Extraktion.

Regeln (bindend):
- Konservativ extrahieren: Alignment-Felder (role_in_deal, influence, disposition) \
NUR setzen, wenn sie im Text woertlich belegbar sind — im Zweifel null. Nichts erfinden.
- Der Verkaeufer selbst ("ich") ist KEIN Kontakt.
- meddpicc_relevant ist true, sobald die Note Qualifizierungs-Substanz enthaelt \
(Budget, Entscheider, Pain, Kriterien, Prozess, Champion-Signale, Wettbewerb, Timing).
- summary: 1-2 deutsche Saetze, faktenbasiert, ohne Floskeln.
- next_steps: nur konkret genannte Schritte/Termine, woertlich nah am Text."""


def classify(text: str) -> Classification:
    """Klassifiziert einen Roh-Text (ein Haiku-Call, structured output)."""
    return llm.call_structured(
        model=settings.MODEL_CLASSIFY,
        system=SYSTEM_PROMPT,
        user=f"=== ROHE NOTIZ ===\n{text}",
        output_format=Classification,
        max_tokens=2_000,
    )
