"""Resolver: ordnet Text einem Deal zu — NIE raten (bindende Ingestion-Entscheidung 1).

Regelbasiert (kein LLM): nutzt find_deal_candidates aus dem Repository.
- --deal-Flag uebersteuert alles.
- Bester Kandidat mit Confidence >= RESOLUTION_THRESHOLD (0.8): automatisch.
- Darunter: Kandidatenliste + Nachfrage ueber den ask-Callback (CLI: interaktiv;
  nicht-interaktiv liefert der Callback None -> sauberer Abbruch mit Hinweis).
"""
from __future__ import annotations

import logging
from typing import Callable

from src.config import settings
from src.domain.deal import Deal
from src.repository.deals import find_deal_candidates, get_deal_by_name

log = logging.getLogger("sales_os.orchestrator")

# ask(frage, optionen) -> Index der gewaehlten Option oder None (keine Antwort moeglich)
AskFn = Callable[[str, list[str]], int | None]


def resolve_deal(text: str, deal_name: str | None, ask: AskFn | None) -> tuple[Deal, float, str]:
    """Liefert (Deal, Confidence, Methode). Wirft ValueError, wenn keine sichere Zuordnung moeglich ist."""
    if deal_name:
        return get_deal_by_name(deal_name), 1.0, "--deal"

    candidates = find_deal_candidates(text)
    if not candidates:
        raise ValueError(
            "Kein passender Deal gefunden — mit --deal <name> angeben oder erst `add-deal`."
        )

    best_deal, best_score = candidates[0]
    if best_score >= settings.RESOLUTION_THRESHOLD:
        log.info("resolver: '%s' automatisch zugeordnet (%.2f)", best_deal.name, best_score)
        return best_deal, best_score, "auto"

    # Unter der Schwelle: nachfragen statt raten (falsch zugeordnete Notes = giftigstes Szenario)
    options = [f"{deal.name} (Confidence {score:.2f})" for deal, score in candidates[:5]]
    options.append("Keiner davon — abbrechen")
    choice = ask(
        f"Zuordnung unsicher (beste Confidence {best_score:.2f} < {settings.RESOLUTION_THRESHOLD}). Welcher Deal?",
        options,
    ) if ask else None
    if choice is None or choice >= len(candidates[:5]):
        raise ValueError(
            "Zuordnung unklar — Abbruch ohne Nebenwirkungen. Mit --deal <name> eindeutig machen. "
            f"Kandidaten: {', '.join(f'{d.name} ({s:.2f})' for d, s in candidates[:5])}"
        )
    deal, score = candidates[choice]
    return deal, score, "nachgefragt"
