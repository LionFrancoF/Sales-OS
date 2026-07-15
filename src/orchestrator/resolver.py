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


class ResolutionUnclear(ValueError):
    """Zuordnung unter der Schwelle und keine Antwort moeglich — NIE raten.

    Erste eigene Exception des Projekts, konform zu Befund 1.7: sie existiert,
    weil sie unterschiedlich gefangen wird — die CLI fragt interaktiv nach,
    die API (P7) antwortet 422 mit strukturierter Kandidatenliste.
    """

    def __init__(self, message: str, candidates: list[tuple[Deal, float]]):
        super().__init__(message)
        self.candidates = candidates


def resolve_deal(text: str, deal_name: str | None, ask: AskFn | None) -> tuple[Deal, float, str]:
    """Liefert (Deal, Confidence, Methode). Wirft ResolutionUnclear, wenn keine sichere Zuordnung moeglich ist."""
    if deal_name:
        return get_deal_by_name(deal_name), 1.0, "--deal"

    candidates = find_deal_candidates(text)
    if not candidates:
        raise ResolutionUnclear(
            "Kein passender Deal gefunden — Deal explizit angeben oder erst anlegen.", []
        )

    best_deal, best_score = candidates[0]
    if best_score >= settings.RESOLUTION_THRESHOLD:
        log.info("resolver: '%s' automatisch zugeordnet (%.2f)", best_deal.name, best_score)
        return best_deal, best_score, "auto"

    # Unter der Schwelle: nachfragen statt raten (falsch zugeordnete Notes = giftigstes Szenario)
    top = candidates[:5]
    options = [f"{deal.name} (Confidence {score:.2f})" for deal, score in top]
    options.append("Keiner davon — abbrechen")
    choice = ask(
        f"Zuordnung unsicher (beste Confidence {best_score:.2f} < {settings.RESOLUTION_THRESHOLD}). Welcher Deal?",
        options,
    ) if ask else None
    if choice is None or choice >= len(top):
        raise ResolutionUnclear(
            "Zuordnung unklar — Abbruch ohne Nebenwirkungen. Deal explizit angeben. "
            f"Kandidaten: {', '.join(f'{d.name} ({s:.2f})' for d, s in top)}",
            top,
        )
    deal, score = top[choice]
    return deal, score, "nachgefragt"
