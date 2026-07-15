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
python -m src.cli --help        # Befehlsübersicht

# Notes analysieren (erster Agent, P4): Ampel je Dimension + JSON nach outputs/
python -m src.cli analyze tests/sample_notes/nordwind_01.txt --deal "Nordwind"

# Golden-Set-Eval: Ist vs. Soll qualitativ je Deal (bewusst ohne Gesamtmetrik, n=3)
python -m src.cli eval
```

Implementiert: `analyze`, `eval`. Übrige Befehle sind Platzhalter für ihre Schicht:

| Befehl | Zweck | Schicht |
|---|---|---|
| `analyze` ✓ | Notes → MEDDPICC-Analyse (Opus 4.8, Structured Outputs, Prompt-Caching) | P4 |
| `eval` ✓ | Golden-Set: Ist vs. Soll qualitativ | P4 |
| `ingest` | Text aufnehmen, klassifizieren, routen | P6 |
| `correct` | Korrektur speichern (Feedback-Loop) | P5 |
| `add-account` / `add-deal` / `add-contact` | Stammdaten anlegen | P5 |
| `list-deals` / `show-deal` | Deals ansehen | P5 |
| `research` | Deep-Research zu einem Account | M1 |
| `account-map` | Stakeholder-Map | M2 |
| `briefing` | Pipeline-Briefing | M3 |
| `prep` | Meeting-Prep One-Pager | M4 |

_Bewusst kein `compare`-Befehl: der Analyzer berechnet `trend` bereits gegen den
vorigen Snapshot (Review-Befund 1.8)._

## Konfiguration
Zentral in `src/config/settings.py` (typisierte Konstanten: Modelle,
Schwellen, `STAGE_GATES`, Cost-/Call-Deckel). Bewusst **kein** `config.yaml`
und **keine** Feature-Flags in V1 (siehe `ARCHITECTURE_REVIEW.md`, Befund 1.4).

## Eigenes Wissen hinzufügen
Eine `.md` in `knowledge/` ablegen, Frontmatter (`topics`, `agents`, `status: FREIGEGEBEN`)
setzen, Abschnitte mit `<!-- topic: x -->` markieren — der Loader findet sie automatisch.
Details: `knowledge/README.md`. **Hinweis:** Playbook-Inhalte sind gitignored
(persönliches Wissen, Repo ist public) — Ordner separat sichern.

## Domain-Modelle (P1)
Der gemeinsame Vertrag aller Agenten (`src/domain/`, Pydantic v2):
- **Account** — die Zielfirma; Wurzel des Modells (Name Pflicht, Rest optional).
- **Contact** — Person bei einem Account inkl. Stakeholder-Alignment (Rolle, Einfluss, Haltung, Beziehungsstärke); Defaults sind „unbekannt".
- **Deal** — Verkaufschance mit Stage; `win_probability` wird aus der Stage abgeleitet (überschreibbar).
- **Activity** — append-only Ereignis (Call/E-Mail/Meeting/…); `raw_text_hash` (SHA-256) wird automatisch abgeleitet (Idempotenz-Basis).
- **DimensionAssessment** / **MeddpiccSnapshot** — das Herzstück: pro Dimension Findings + Confidence + Trend, plus Score, Momentum, Risiken, Next-Best-Questions (append-only, versioniert).

_Bewusst noch nicht gebaut (P1 schlank, Review-Befund 1.10): `Correction` kommt in P5 (Feedback-Speicher), `ContactRelationship` in M2 — jeweils erst, wenn es Daten und Nutzen gibt._

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
