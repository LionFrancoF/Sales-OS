"""MEDDPICC-Aggregat: das Herzstueck. Bewertung eines Deals als append-only Snapshot.

Ein Snapshot buendelt pro Dimension ein DimensionAssessment plus Gesamt-Score,
Momentum, Risiken und die naechsten besten Fragen. Snapshots werden nie
ueberschrieben, sondern versioniert (append-only) — der Vergleich zweier
Snapshots ergibt den Trend.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

Confidence = Literal["GESICHERT", "WAHRSCHEINLICH", "ZU_PRUEFEN", "UNBEKANNT"]
Trend = Literal["VERBESSERT", "STABIL", "VERSCHLECHTERT", "ERSTBEWERTUNG"]
Framework = Literal["MEDDICC", "MEDDPICC"]
Momentum = Literal["POSITIV", "NEUTRAL", "NEGATIV"]

# Erlaubte Dimensions-Keys. paper_process ist nur bei MEDDPICC zulaessig.
_MEDDPICC_DIMENSIONS = frozenset(
    {
        "metrics",
        "economic_buyer",
        "decision_criteria",
        "decision_process",
        "paper_process",
        "identify_pain",
        "champion",
        "competition",
    }
)


class DimensionAssessment(BaseModel):
    """Bewertung einer einzelnen MEDDPICC-Dimension."""

    model_config = ConfigDict(extra="forbid")

    findings: str = Field(default="", description="Was aus den Notes zu dieser Dimension hervorgeht.")
    confidence: Confidence = Field(default="UNBEKANNT", description="Belegbarkeit der Findings.")
    evidence: list[str] = Field(default_factory=list, description="Woertliche Belege aus den Notes.")
    gaps: list[str] = Field(default_factory=list, description="Was zu dieser Dimension noch fehlt.")
    trend: Trend = Field(default="ERSTBEWERTUNG", description="Entwicklung ggue. dem vorigen Snapshot.")
    recommended_action: str = Field(default="", description="Konkrete, im naechsten Schritt umsetzbare Aktion.")
    next_question: str = Field(default="", description="Woertlich im naechsten Call stellbare Frage.")


class MeddpiccSnapshot(BaseModel):
    """Versionierte Gesamtbewertung eines Deals (append-only)."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: str(uuid4()), description="Eindeutige ID (uuid4).")
    deal_id: str = Field(description="Bewerteter Deal (Pflichtfeld).")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Erstellzeitpunkt (UTC).")
    source_activity_ids: list[str] = Field(
        default_factory=list, description="IDs der Activities, die in diese Bewertung eingeflossen sind."
    )
    framework: Framework = Field(default="MEDDPICC", description="Gewaehltes Framework.")
    framework_rationale: str = Field(default="", description="Begruendung der Framework-Wahl fuer diesen Deal.")
    dimensions: dict[str, DimensionAssessment] = Field(
        default_factory=dict,
        description="Bewertungen je Dimension (Keys: metrics, economic_buyer, decision_criteria, "
        "decision_process, paper_process[nur MEDDPICC], identify_pain, champion, competition).",
    )
    overall_score: int = Field(ge=0, le=100, description="Gesamt-Score 0-100 (Pflichtfeld).")
    score_rationale: str = Field(default="", description="Begruendung des Gesamt-Scores.")
    momentum: Momentum = Field(default="NEUTRAL", description="Gesamt-Momentum des Deals.")
    deal_risks: list[str] = Field(default_factory=list, description="Erkannte Deal-Risiken.")
    next_best_questions: list[str] = Field(
        default_factory=list, max_length=5, description="Priorisierte, woertlich stellbare Fragen (max 5)."
    )
    summary_for_manager: str = Field(default="", description="3 Saetze, forecast-tauglich.")
    prompt_version: str = Field(
        default="", description="Hash/Nummer des erzeugenden Prompts (Rueckverfolgung, CLAUDE.md-Datenmodell)."
    )

    @model_validator(mode="after")
    def _check_dimensions(self) -> "MeddpiccSnapshot":
        """Nur erlaubte Dimensions-Keys; paper_process ausschliesslich bei MEDDPICC."""
        unknown = set(self.dimensions) - _MEDDPICC_DIMENSIONS
        if unknown:
            raise ValueError(f"Unbekannte Dimensions-Keys: {sorted(unknown)}")
        if self.framework == "MEDDICC" and "paper_process" in self.dimensions:
            raise ValueError("paper_process ist nur bei framework=MEDDPICC zulaessig.")
        return self
