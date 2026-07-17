"""Gemeinsamer LLM-Aufruf fuer alle Agenten/Orchestrator-Stufen.

Extrahiert aus meddpicc/agent.py, seit es einen zweiten Konsumenten gibt
(Classifier, P6). Buendelt:
- Structured Outputs via client.messages.parse() (schema-valides JSON)
- Cost-Circuit-Breaker (P-1 Befund 2.8): harter Call-/Token-Deckel pro
  CLI-Aufruf (Prozess), Werte aus settings.py
- genau EINE Kosten-Logzeile pro Call (Befund 1.1: keine Cost-Tabelle)

Modelle kommen IMMER vom Aufrufer aus settings (nie hartcodiert).
"""
from __future__ import annotations

import logging
import time

from dotenv import load_dotenv

from src.config import settings

log = logging.getLogger("sales_os.llm")

# Circuit-Breaker-Zaehler, gelten pro CLI-Aufruf (Prozess), ueber alle Modelle.
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


def call_text(
    *,
    model: str,
    system: list[dict] | str,
    messages: list[dict],
    max_tokens: int,
    thinking: dict | None = None,
) -> str:
    """Ein API-Call mit freier Text-Antwort (Berater/Prosa; mehrere Turns erlaubt).

    Zweiter Konsumententyp neben call_structured: gleicher Circuit-Breaker,
    gleiche eine Kosten-Logzeile — nur ohne Output-Schema."""
    _check_circuit_breaker()
    kwargs: dict = {}
    if thinking is not None:
        kwargs["thinking"] = thinking
    t0 = time.perf_counter()
    response = _client().messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=messages,
        **kwargs,
    )
    _log_call(model, response.usage, time.perf_counter() - t0)
    text = "".join(b.text for b in response.content if getattr(b, "type", "") == "text")
    if not text.strip():
        raise ValueError(f"Leere Text-Antwort (stop_reason={response.stop_reason}).")
    return text


def call_structured(
    *,
    model: str,
    system: list[dict] | str,
    user: str,
    output_format,
    max_tokens: int,
    thinking: dict | None = None,
):
    """Ein API-Call mit Structured Output; wirft ValueError bei unbrauchbarem Output."""
    _check_circuit_breaker()
    kwargs: dict = {}
    if thinking is not None:
        kwargs["thinking"] = thinking
    t0 = time.perf_counter()
    response = _client().messages.parse(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
        output_format=output_format,
        **kwargs,
    )
    _log_call(model, response.usage, time.perf_counter() - t0)
    if response.parsed_output is None:
        raise ValueError(f"Kein parsebarer Output (stop_reason={response.stop_reason}).")
    return response.parsed_output
