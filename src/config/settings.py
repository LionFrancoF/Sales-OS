"""Zentrale, typisierte Konfiguration als Konstanten.

Ersetzt bewusst config.yaml + pydantic-settings-Loader + Feature-Flags
(P-1 Befund 1.4): Single-User, kein Deploy — Python-Konstanten sind bereits
typsicher und brauchen keinen YAML-Validierungslayer. YAML/Flags erst, wenn
ein Nicht-Engineer tunt oder Deploy von Release entkoppelt werden muss.

Hier stehen NUR Werte, keine Logik. Modelle NIE anderswo hartcodieren —
immer von hier importieren.
"""
from __future__ import annotations

from typing import Final

# --- Modell-Tiering (Stand Juli 2026) ---
MODEL_CLASSIFY: Final[str] = "claude-haiku-4-5-20251001"  # Klassifizierung, Entity-Resolution, Extraktion
MODEL_ANALYZE: Final[str] = "claude-opus-4-8"             # MEDDPICC-Analyse, Research-Synthese (Qualität kritisch)
MODEL_DEFAULT: Final[str] = "claude-sonnet-5"             # Meeting-Prep, Briefing, mittlere Aufgaben

# --- Schwellen ---
RESOLUTION_THRESHOLD: Final[float] = 0.8   # Entity-Resolution: darunter nachfragen statt raten
KNOWLEDGE_CHAR_LIMIT: Final[int] = 8000    # Max. Zeichen des injizierten Knowledge-Blocks

# --- Cost-/Call-Deckel (P-1 Befund 2.8: Circuit Breaker) ---
MAX_LLM_CALLS_PER_COMMAND: Final[int] = 25        # harter Anschlag gegen Runaway-Schleifen
MAX_LLM_TOKENS_PER_COMMAND: Final[int] = 500_000  # harte Token-Obergrenze pro CLI-Aufruf

# --- STAGE_GATES: Austrittskriterien + Default-Win-% pro Deal-Stage ---
# Referenz für Analyzer & Pipeline-Briefing. Als Python-dict statt config.yaml
# (P-1 Befund 4.3). Keys entsprechen Deal.stage (Domain kommt in P1).
STAGE_GATES: Final[dict[str, dict]] = {
    "PROSPECT": {"win": 10, "exit": ["Erstkontakt qualifiziert", "Bedarf grob erkennbar"]},
    "DISCOVERY": {"win": 20, "exit": ["Pain identifiziert", "Metrics benannt", "erster Stakeholder eingebunden"]},
    "EVALUATION": {"win": 40, "exit": ["qualifiziert", "weitere Stakeholder eingebunden", "Decision-Process/Budget identifiziert"]},
    "PROPOSAL": {"win": 60, "exit": ["Angebot gestellt", "Decision Criteria bestätigt", "Economic Buyer bekannt"]},
    "NEGOTIATION": {"win": 75, "exit": ["kommerzielle Punkte offen aber terminiert", "Paper Process bekannt"]},
    "VERBAL": {"win": 90, "exit": ["mündliche Zusage", "nur noch Paper Process offen"]},
    "CLOSED_WON": {"win": 100, "exit": []},
    "CLOSED_LOST": {"win": 0, "exit": []},
}
