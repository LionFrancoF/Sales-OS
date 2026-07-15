"""MEDDPICC-Analyzer: analyze(notes) -> MeddpiccSnapshot.

- Modell aus settings (MODEL_ANALYZE, nie hartcodiert), Structured Outputs
  via client.messages.parse() -> schema-valides JSON garantiert; 1 Retry mit
  Fehlermeldung als Sicherheitsnetz (CLAUDE.md Schicht-Regel).
- Prompt-Caching: [System][Knowledge] als stabiler Prefix mit cache_control,
  Variables in der User-Message (P-1 Befund 3.5).
- Cost-Circuit-Breaker (P-1 Befund 2.8) + eine Kosten-Logzeile pro Call
  (keine Cost-Tabelle in V1, Befund 1.1).
- Hinweis: Opus 4.8 akzeptiert KEIN temperature (API-Vorgabe); adaptive
  thinking ist explizit aktiviert (qualitaetskritische Analyse).
"""
from __future__ import annotations

import json
import logging
import time

from dotenv import load_dotenv
from pydantic import ValidationError

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

# Circuit-Breaker-Zaehler, gelten pro CLI-Aufruf (Prozess).
_calls_this_command = 0
_tokens_this_command = 0


def _check_circuit_breaker() -> None:
    """Harter Anschlag gegen Kosten-Runaway (P-1 Befund 2.8)."""
    if _calls_this_command >= settings.MAX_LLM_CALLS_PER_COMMAND:
        raise RuntimeError(
            f"Cost-Circuit-Breaker: {_calls_this_command} LLM-Calls in diesem Aufruf "
            f"(Deckel {settings.MAX_LLM_CALLS_PER_COMMAND}, settings.py). Abbruch."
        )
    if _tokens_this_command >= settings.MAX_LLM_TOKENS_PER_COMMAND:
        raise RuntimeError(
            f"Cost-Circuit-Breaker: {_tokens_this_command:,} Tokens in diesem Aufruf "
            f"(Deckel {settings.MAX_LLM_TOKENS_PER_COMMAND:,}, settings.py). Abbruch."
        )


def _log_call(model: str, usage, latency_s: float) -> None:
    """Eine Log-Zeile pro Call: model, tokens, grober Cent-Betrag, Latenz."""
    global _calls_this_command, _tokens_this_command
    inp = getattr(usage, "input_tokens", 0) or 0
    out = getattr(usage, "output_tokens", 0) or 0
    cw = getattr(usage, "cache_creation_input_tokens", 0) or 0
    cr = getattr(usage, "cache_read_input_tokens", 0) or 0
    prices = settings.MODEL_PRICES_USD_PER_MTOK.get(model, {})
    cost_usd = (
        inp * prices.get("input", 0)
        + out * prices.get("output", 0)
        + cw * prices.get("cache_write", 0)
        + cr * prices.get("cache_read", 0)
    ) / 1_000_000
    _calls_this_command += 1
    _tokens_this_command += inp + out + cw + cr
    log.info(
        "llm-call model=%s in=%d out=%d cache_write=%d cache_read=%d ~%.1f ct latency=%.1fs",
        model, inp, out, cw, cr, cost_usd * 100, latency_s,
    )


def _client():
    """Anthropic-Client, lazy (Import-Zeit ohne Key soll nicht knallen)."""
    import anthropic

    load_dotenv()  # ANTHROPIC_API_KEY aus .env
    return anthropic.Anthropic()


def _call_llm(system_blocks: list[dict], user_message: str) -> AnalysisResult:
    """Ein API-Call mit Structured Output. Wirft ValidationError/ValueError bei invalidem Output."""
    _check_circuit_breaker()
    client = _client()
    t0 = time.perf_counter()
    response = client.messages.parse(
        model=settings.MODEL_ANALYZE,
        max_tokens=_MAX_TOKENS,
        thinking={"type": "adaptive"},
        system=system_blocks,
        messages=[{"role": "user", "content": user_message}],
        output_format=AnalysisResult,
    )
    _log_call(settings.MODEL_ANALYZE, response.usage, time.perf_counter() - t0)
    if response.parsed_output is None:
        raise ValueError(f"Kein parsebarer Output (stop_reason={response.stop_reason}).")
    return response.parsed_output


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
) -> MeddpiccSnapshot:
    """Mappt den LLM-Vertrag in den Domain-Snapshot; Code setzt Verwaltungsfelder."""
    dims: dict[str, DimensionAssessment] = {}
    for key, llm_dim in result.dimensions.model_dump().items():
        if previous_snapshot is None:
            llm_dim["trend"] = "ERSTBEWERTUNG"  # Code erzwingt, nicht dem Modell vertrauen
        dims[key] = DimensionAssessment(**llm_dim)
    return MeddpiccSnapshot(
        deal_id=deal.id if deal else "unassigned",
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

    return _to_snapshot(result, deal, previous_snapshot)
