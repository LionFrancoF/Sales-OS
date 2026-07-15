"""MEDDPICC-Analyzer: analyze(notes) -> MeddpiccSnapshot.

- Modell aus settings (MODEL_ANALYZE, nie hartcodiert), Structured Outputs +
  Circuit-Breaker + Kosten-Logzeile via src/agents/llm.py; 1 Retry mit
  Fehlermeldung als Sicherheitsnetz (CLAUDE.md Schicht-Regel).
- Prompt-Caching: [System][Knowledge] als stabiler Prefix mit cache_control,
  Variables in der User-Message (P-1 Befund 3.5).
- Kontextgrenze (Befund 2.2/4.1): der Analyzer bekommt NIE die Roh-Historie,
  sondern [letzter Snapshot] + [neue Note] — konstante Kosten je Ingest.
- Hinweis: Opus 4.8 akzeptiert KEIN temperature (API); adaptive thinking aktiv.
"""
from __future__ import annotations

import logging

from pydantic import ValidationError

from src.agents import llm
from src.agents.meddpicc.prompts import (
    KNOWLEDGE_HEADER,
    PROMPT_VERSION,
    RETRY_SUFFIX,
    SYSTEM_PROMPT,
    build_user_message,
)
from src.agents.meddpicc.schema import AnalysisResult
from src.config import settings
from src.domain.deal import Deal
from src.domain.meddpicc import DimensionAssessment, MeddpiccSnapshot
from src.knowledge.loader import load_for

log = logging.getLogger("sales_os.agents.meddpicc")

AGENT_NAME = "meddpicc_analyzer"
_MAX_TOKENS = 16_000  # non-streaming Empfehlung; JSON-Snapshot + adaptives Thinking passen locker


def _call_llm(system_blocks: list[dict], user_message: str) -> AnalysisResult:
    """Ein Analyzer-Call (separat, damit Tests genau hier mocken koennen)."""
    return llm.call_structured(
        model=settings.MODEL_ANALYZE,
        system=system_blocks,
        user=user_message,
        output_format=AnalysisResult,
        max_tokens=_MAX_TOKENS,
        thinking={"type": "adaptive"},
    )


def _build_system_blocks(knowledge_block: str) -> list[dict]:
    """Stabiler, cache-faehiger Prefix: [System][Knowledge]. Cache-Grenze nach Knowledge."""
    return [
        {"type": "text", "text": SYSTEM_PROMPT},
        {
            "type": "text",
            "text": f"{KNOWLEDGE_HEADER}\n{knowledge_block}",
            "cache_control": {"type": "ephemeral"},
        },
    ]


def _to_snapshot(
    result: AnalysisResult,
    deal: Deal | None,
    previous_snapshot: MeddpiccSnapshot | None,
    source_activity_ids: list[str],
) -> MeddpiccSnapshot:
    """Mappt den LLM-Vertrag in den Domain-Snapshot; Code setzt Verwaltungsfelder."""
    dims: dict[str, DimensionAssessment] = {}
    for key, llm_dim in result.dimensions.model_dump().items():
        if previous_snapshot is None:
            llm_dim["trend"] = "ERSTBEWERTUNG"  # Code erzwingt, nicht dem Modell vertrauen
        dims[key] = DimensionAssessment(**llm_dim)
    return MeddpiccSnapshot(
        deal_id=deal.id if deal else "unassigned",
        source_activity_ids=source_activity_ids,
        framework="MEDDPICC",
        framework_rationale="V1: MEDDPICC erzwungen, Auto-Wahl bewusst gestrichen (P-1 Befund 1.6).",
        dimensions=dims,
        overall_score=result.overall_score,
        score_rationale=result.score_rationale,
        momentum=result.momentum,
        deal_risks=result.deal_risks,
        next_best_questions=result.next_best_questions,
        summary_for_manager=result.summary_for_manager,
        prompt_version=PROMPT_VERSION,
    )


def analyze(
    notes: str,
    previous_snapshot: MeddpiccSnapshot | None = None,
    deal: Deal | None = None,
    corrections_block: str = "",
    source_activity_ids: list[str] | None = None,
) -> MeddpiccSnapshot:
    """Analysiert Call-Notes zu einem MeddpiccSnapshot (append-only, versioniert).

    Genau 1 Retry bei Validierungsfehler, mit der Fehlermeldung im Prompt
    (CLAUDE.md Schicht-Regel fuer Agenten).
    """
    if not notes.strip():
        raise ValueError("Leere Notes — nichts zu analysieren.")

    knowledge = load_for(AGENT_NAME)
    system_blocks = _build_system_blocks(knowledge)

    deal_context = None
    if deal is not None:
        deal_context = f"Deal: {deal.name} | Stage: {deal.stage}"
    previous_json = (
        previous_snapshot.model_dump_json(exclude={"id", "prompt_version"})
        if previous_snapshot
        else None
    )
    user_message = build_user_message(notes, previous_json, deal_context, corrections_block)

    try:
        result = _call_llm(system_blocks, user_message)
    except (ValidationError, ValueError) as first_error:
        log.warning("Analyzer-Output invalide, 1 Retry: %s", first_error)
        retry_message = user_message + RETRY_SUFFIX.format(error=first_error)
        result = _call_llm(system_blocks, retry_message)  # 2. Fehler propagiert

    return _to_snapshot(result, deal, previous_snapshot, source_activity_ids or [])
