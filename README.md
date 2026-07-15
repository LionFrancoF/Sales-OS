# Sales OS

AI-natives Sales-Betriebssystem für Enterprise Sales / Forward Deployed
Engineering. Spezialisierte Einzweck-Agenten (MEDDPICC-Analyse, Research,
Account-Map, Pipeline-Briefing, Meeting-Prep) arbeiten über ein gemeinsames
Datenmodell und einen Ingestion-Orchestrator zusammen — API-first, lokal,
später kompatibel mit Fremdsoftware (eigene App, MCP, HubSpot, CSV).

> **Status: P0 (Gerüst).** Nur Projektstruktur — noch keine Logik, keine
> Modelle, keine Prompts. Die Schichten werden von innen nach außen gebaut
> (siehe `CLAUDE.md` und `ARCHITECTURE.md`).

## Setup
```bash
# 1. Virtuelle Umgebung
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Dependencies
pip install -r requirements.txt

# 3. Secrets
cp .env.example .env            # ANTHROPIC_API_KEY= eintragen
```

## Nutzung
```bash
python -m src.cli --help        # Befehlsübersicht (P0: Platzhalter)
```

Alle Befehle sind aktuell Platzhalter und werden in ihrer Schicht/Modul
implementiert:

| Befehl | Zweck | Schicht |
|---|---|---|
| `analyze` | Notes → MEDDPICC-Analyse | P4 |
| `ingest` | Text aufnehmen, klassifizieren, routen | P6 |
| `eval` | Golden-Set-Auswertung | P4 |
| `correct` | Korrektur speichern (Feedback-Loop) | P5 |
| `add-account` / `add-deal` / `add-contact` | Stammdaten anlegen | P5 |
| `list-deals` / `show-deal` | Deals ansehen | P5 |
| `research` | Deep-Research zu einem Account | M1 |
| `account-map` | Stakeholder-Map | M2 |
| `briefing` | Pipeline-Briefing | M3 |
| `prep` | Meeting-Prep One-Pager | M4 |

## Konfiguration
Zentral in `src/config/settings.py` (typisierte Konstanten: Modelle,
Schwellen, `STAGE_GATES`, Cost-/Call-Deckel). Bewusst **kein** `config.yaml`
und **keine** Feature-Flags in V1 (siehe `ARCHITECTURE_REVIEW.md`, Befund 1.4).

## Eigenes Wissen hinzufügen
Playbooks liegen in `knowledge/` als Markdown mit YAML-Frontmatter — Details
in `knowledge/README.md` (ab P3 aktiv).

## Domain-Modelle (P1)
Der gemeinsame Vertrag aller Agenten (`src/domain/`, Pydantic v2):
- **Account** — die Zielfirma; Wurzel des Modells (Name Pflicht, Rest optional).
- **Contact** — Person bei einem Account inkl. Stakeholder-Alignment (Rolle, Einfluss, Haltung, Beziehungsstärke); Defaults sind „unbekannt".
- **Deal** — Verkaufschance mit Stage; `win_probability` wird aus der Stage abgeleitet (überschreibbar).
- **Activity** — append-only Ereignis (Call/E-Mail/Meeting/…); `raw_text_hash` (SHA-256) wird automatisch abgeleitet (Idempotenz-Basis).
- **DimensionAssessment** / **MeddpiccSnapshot** — das Herzstück: pro Dimension Findings + Confidence + Trend, plus Score, Momentum, Risiken, Next-Best-Questions (append-only, versioniert).
- **Correction** — manuelle Korrektur (alt → neu) als Grundlage des Feedback-Loops.

_Bewusst noch nicht gebaut: `ContactRelationship` (Beziehungs-Graph) — kommt in M2, wenn es Daten und Nutzen gibt (Review-Befund 1.3/1.10)._

## Struktur
```
src/domain/         Pydantic-Modelle (P1) ✓
knowledge/          Playbooks + Loader (P3)
src/agents/         Einzweck-Agenten (P4, M1–M4)
src/repository/     einziger DB-Zugang (P5)
src/orchestrator/   Ingestion/Routing (P6)
src/api/            FastAPI (P7)
src/cli.py          Einstiegspunkt
src/config/         settings.py (Konstanten)
tests/              sample_notes/, golden_set/, regression/
```

## Doku
- `CLAUDE.md` — Projektregeln, Architektur, bewusste Entscheidungen.
- `ARCHITECTURE.md` — Datenfluss (wird je Schicht aktualisiert).
- `ARCHITECTURE_REVIEW.md` — Staff-Engineer-Review (P-1).
