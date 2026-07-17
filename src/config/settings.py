"""Zentrale, typisierte Konfiguration als Konstanten.

Ersetzt bewusst config.yaml + pydantic-settings-Loader + Feature-Flags
(P-1 Befund 1.4): Single-User, kein Deploy — Python-Konstanten sind bereits
typsicher und brauchen keinen YAML-Validierungslayer. YAML/Flags erst, wenn
ein Nicht-Engineer tunt oder Deploy von Release entkoppelt werden muss.

Hier stehen NUR Werte, keine Logik. Modelle NIE anderswo hartcodieren —
immer von hier importieren.
"""
from __future__ import annotations

from pathlib import Path
from typing import Final

# --- Persistenz (ab Schicht 5) ---
# SQLite, eine Datei, DB = einzige Quelle der Wahrheit (P-1 Befund 4.4).
# Schema-Wandel-Konvention V1 (Befund 2.5, Entscheidung Lion): bei
# Modellaenderung wird die lokale .db geloescht und neu aufgebaut —
# Testdaten sind synthetisch reproduzierbar. Migrations-Konvention kommt,
# sobald echte Daten schuetzenswert sind.
DB_PATH: Final[Path] = Path(__file__).resolve().parents[2] / "sales_os.db"

# --- Modell-Tiering (Stand Juli 2026) ---
MODEL_CLASSIFY: Final[str] = "claude-haiku-4-5-20251001"  # Klassifizierung, Entity-Resolution, Extraktion
MODEL_ANALYZE: Final[str] = "claude-opus-4-8"             # MEDDPICC-Analyse, Research-Synthese (Qualität kritisch)
MODEL_DEFAULT: Final[str] = "claude-sonnet-5"             # Meeting-Prep, Briefing, mittlere Aufgaben
MODEL_ADVISE: Final[str] = "claude-opus-4-8"              # Berater (advise): Beratungsqualität = Kern der Vision

# --- Schwellen ---
RESOLUTION_THRESHOLD: Final[float] = 0.8   # Entity-Resolution: darunter nachfragen statt raten

# Max. Zeichen des injizierten Knowledge-Blocks. Bewusst grosszuegig: der Block
# ist ein cache-faehiger Prompt-Prefix (Prompt-Caching -> grosse stabile Bloecke
# sind billig). Das Limit ist ein Runaway-Backstop, KEIN Sparinstrument — bei
# Ueberschreitung schlaegt der Loader LAUT fehl statt still zu trunkieren
# (P-1 Befund 3.2/4.5, Entscheidung Lion).
# 64k (Entscheidung Lion, P3): Agenten laden Volllast nach agents:-Frontmatter
# (Lions eigene Kuratierung); heutige Volllasten 41k/36k/43k passen mit Luft.
# Fokussierung per Topic-Profilen NUR, falls der Golden-Set-Eval in P4 zeigt,
# dass der Analyzer unfokussiert wird (erst messen, dann Mechanik).
KNOWLEDGE_CHAR_LIMIT: Final[int] = 64_000

# --- Cost-/Call-Deckel (P-1 Befund 2.8: Circuit Breaker) ---
MAX_LLM_CALLS_PER_COMMAND: Final[int] = 25        # harter Anschlag gegen Runaway-Schleifen
MAX_LLM_TOKENS_PER_COMMAND: Final[int] = 500_000  # harte Token-Obergrenze pro CLI-Aufruf

# --- Preise in USD je Million Tokens (Stand Juli 2026) ---
# Nur fuer die grobe Kosten-Logzeile pro Call (CLAUDE.md: eine Log-Zeile,
# keine Cost-Tabelle). cache_write = 1.25x Input, cache_read = 0.1x Input.
MODEL_PRICES_USD_PER_MTOK: Final[dict[str, dict[str, float]]] = {
    "claude-opus-4-8": {"input": 5.0, "output": 25.0, "cache_read": 0.5, "cache_write": 6.25},
    "claude-sonnet-5": {"input": 3.0, "output": 15.0, "cache_read": 0.3, "cache_write": 3.75},
    "claude-haiku-4-5-20251001": {"input": 1.0, "output": 5.0, "cache_read": 0.1, "cache_write": 1.25},
}

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
