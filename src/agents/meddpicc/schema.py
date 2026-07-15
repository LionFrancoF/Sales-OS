"""LLM-Output-Schema des MEDDPICC-Analyzers (Structured Outputs).

Bewusst ein EIGENES Schema statt des Domain-Snapshots: alle Felder sind
Pflicht (das Modell darf nichts weglassen — keine stillen Defaults), und
Verwaltungsfelder (id, deal_id, created_at, prompt_version) gehoeren nicht
in den LLM-Vertrag — die setzt der Code. Das Mapping in den Domain-Snapshot
passiert in agent.py.

framework/framework_rationale fehlen absichtlich: V1 erzwingt MEDDPICC
(Bewusste Entscheidung P-1/1.6), es gibt nichts zu waehlen.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Confidence = Literal["GESICHERT", "WAHRSCHEINLICH", "ZU_PRUEFEN", "UNBEKANNT"]
Trend = Literal["VERBESSERT", "STABIL", "VERSCHLECHTERT", "ERSTBEWERTUNG"]
Momentum = Literal["POSITIV", "NEUTRAL", "NEGATIV"]


class LlmDimension(BaseModel):
    """Bewertung einer Dimension — alle Felder Pflicht."""

    model_config = ConfigDict(extra="forbid")

    findings: str = Field(description="Was aus den Notes zu dieser Dimension hervorgeht (deutsch, kompakt).")
    confidence: Confidence = Field(description="Belegbarkeit gemaess der bindenden Confidence-Regeln.")
    evidence: list[str] = Field(description="Woertliche Zitate aus den Notes; leer bei UNBEKANNT.")
    gaps: list[str] = Field(description="Was zu dieser Dimension fehlt.")
    trend: Trend = Field(description="Vergleich zum vorigen Snapshot; ERSTBEWERTUNG wenn keiner existiert.")
    recommended_action: str = Field(description="Konkret und sofort umsetzbar — keine Floskeln.")
    next_question: str = Field(description="Woertlich im naechsten Call stellbar.")


class LlmDimensions(BaseModel):
    """Alle 8 MEDDPICC-Dimensionen (V1 erzwingt das volle Framework)."""

    model_config = ConfigDict(extra="forbid")

    metrics: LlmDimension
    economic_buyer: LlmDimension
    decision_criteria: LlmDimension
    decision_process: LlmDimension
    paper_process: LlmDimension
    identify_pain: LlmDimension
    champion: LlmDimension
    competition: LlmDimension


class AnalysisResult(BaseModel):
    """Gesamtergebnis einer Analyse — der komplette LLM-Vertrag."""

    model_config = ConfigDict(extra="forbid")

    dimensions: LlmDimensions
    overall_score: int = Field(ge=0, le=100, description="Qualifizierungs-Gesundheit 0-100 (nicht Win-%).")
    score_rationale: str = Field(description="Begruendung des Scores.")
    momentum: Momentum = Field(description="Tatsaechliche juengste Richtung des Deals (nicht Potenzial).")
    deal_risks: list[str] = Field(description="Erkannte Deal-Risiken, priorisiert.")
    next_best_questions: list[str] = Field(max_length=5, description="Max 5, priorisiert, woertlich stellbar.")
    summary_for_manager: str = Field(description="3 Saetze, forecast-tauglich.")
