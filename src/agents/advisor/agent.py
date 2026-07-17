"""Berater-Agent: advise(frage, ...) -> Prosa-Antwort. Read-only.

- Modell aus settings (MODEL_ADVISE, nie hartcodiert); freier Text via
  llm.call_text (gleicher Circuit-Breaker + Kosten-Logzeile wie alle Calls).
- Prompt-Caching: [System][Knowledge] als stabiler Prefix mit cache_control,
  Variables (Kontext + Frage/Verlauf) in den Messages (P-1 Befund 3.5).
- Bewusst KEIN Output-Schema (Beratung ist Prosa) und KEIN DB-Schreibzugriff:
  Festhalten von Ergebnissen laeuft ueber `ingest` (CLAUDE.md, Vision 17.07.).
- Mehrrunden-Gespraeche: der Aufrufer haelt die History (in-memory, CLI-Session);
  bewusst kein Konversations-Speicher in der DB (kein Vorbau).
"""
from __future__ import annotations

import logging

from src.agents import llm
from src.agents.advisor.context import build_deal_context, build_pipeline_context
from src.agents.advisor.prompts import KNOWLEDGE_HEADER, PROMPT_VERSION, SYSTEM_PROMPT
from src.config import settings
from src.knowledge.loader import load_for

log = logging.getLogger("sales_os.agents.advisor")

AGENT_NAME = "advisor"
_MAX_TOKENS = 8_000  # Prosa-Antwort + adaptives Thinking


def _build_system_blocks(knowledge_block: str) -> list[dict]:
    """Stabiler, cache-faehiger Prefix: [System][Knowledge]."""
    return [
        {"type": "text", "text": SYSTEM_PROMPT},
        {
            "type": "text",
            "text": f"{KNOWLEDGE_HEADER}\n{knowledge_block}",
            "cache_control": {"type": "ephemeral"},
        },
    ]


def _build_first_message(question: str, deal_name: str | None, pipeline: bool) -> str:
    """Erste User-Message: [Kontext][Frage]. Kontext kommt NUR aus dem Repository."""
    parts: list[str] = []
    if deal_name:
        parts.append(build_deal_context(deal_name))
    if pipeline:
        parts.append(build_pipeline_context())
    if not parts:
        parts.append("(Kein Deal-/Pipeline-Kontext mitgegeben — Methodik-Frage.)")
    parts.append(f"=== LIONS FRAGE ===\n{question}")
    return "\n\n".join(parts)


def advise(
    question: str,
    deal_name: str | None = None,
    pipeline: bool = False,
    topics: list[str] | None = None,
    history: list[dict] | None = None,
) -> tuple[str, list[dict]]:
    """Eine Berater-Antwort. Gibt (antwort, fortgeschriebene_history) zurueck.

    history: bisherige Messages der Session (in-memory). Beim ersten Aufruf None/
    leer — dann wird die erste Message inkl. Kontext gebaut; Folgefragen gehen
    als reine User-Messages in denselben Verlauf (Kontext bleibt Turn 1)."""
    knowledge = load_for(AGENT_NAME, topics=topics)
    system_blocks = _build_system_blocks(knowledge)

    messages = list(history) if history else []
    if messages:
        messages.append({"role": "user", "content": question})
    else:
        messages.append(
            {"role": "user", "content": _build_first_message(question, deal_name, pipeline)}
        )

    log.info(
        "advisor: frage (%d Zeichen), deal=%s, pipeline=%s, topics=%s, turn=%d, prompt_version=%s",
        len(question), deal_name or "-", pipeline, topics or "-",
        (len(messages) + 1) // 2, PROMPT_VERSION,
    )
    answer = llm.call_text(
        model=settings.MODEL_ADVISE,
        system=system_blocks,
        messages=messages,
        max_tokens=_MAX_TOKENS,
        thinking={"type": "adaptive"},
    )
    messages.append({"role": "assistant", "content": answer})
    return answer, messages
