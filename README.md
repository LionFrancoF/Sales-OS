# Sales OS

AI-natives Sales-Betriebssystem für Enterprise Sales / Forward Deployed
Engineering. Spezialisierte Einzweck-Agenten (MEDDPICC-Analyse, Research,
Account-Map, Pipeline-Briefing, Meeting-Prep) arbeiten über ein gemeinsames
Datenmodell und einen Ingestion-Orchestrator zusammen — API-first, lokal,
später kompatibel mit Fremdsoftware (eigene App, MCP, HubSpot, CSV).

> **Status: Schichten 0–7 komplett.** Kern-Datenfluss lebt (ingest →
> Klassifizierung → Resolution → append-only Persistenz → Analyse mit Trend)
> und ist per CLI UND FastAPI nutzbar. Als Nächstes: Module M1–M4.

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

# Golden-Set-Eval: Ist vs. Soll qualitativ je Deal (bewusst ohne Gesamtmetrik, n=6)
python -m src.cli eval

# Persistenz (P5): Stammdaten anlegen, analysieren, korrigieren
python -m src.cli add-account --name "Nordwind Logistics" --industry Logistik
python -m src.cli add-deal "Nordwind Logistics" --name "Ops-Analytics" --stage DISCOVERY
python -m src.cli analyze tests/sample_notes/nordwind_01.txt --deal "Ops-Analytics"  # -> DB, append-only
python -m src.cli show-deal "Ops-Analytics"     # Snapshot-Kurzfassung + Kontakte + Korrekturen
python -m src.cli correct "Ops-Analytics" --field dimensions.champion.confidence --value ZU_PRUEFEN
python -m src.cli correct "Ops-Analytics" --field overall_score --value 30 --golden  # + Golden-Set-Kandidat exportieren
python -m src.cli export-notes "Ops-Analytics"  # Roh-Notes -> tests/sample_notes/private/ (gitignored, echte Kundendaten)

# Ingestion (P6): klassifizieren, zuordnen (Schwelle 0.8, sonst Nachfrage), routen
python -m src.cli ingest tests/sample_notes/nordwind_02.txt        # auto-Resolution
python -m src.cli set-stage "Ops-Analytics" CLOSED_LOST --reason "Budget gestrichen"

# Der Berater (Haupteingang, Vision 17.07.): freie Fragen durch Lions Brille, read-only
python -m src.cli advise "Wie gehe ich den Account nach dem Champion-Wechsel an?" --deal "Ops-Analytics"
python -m src.cli advise "Was ist diese Woche in meiner Pipeline wichtig?" --pipeline
python -m src.cli advise -i --deal "Ops-Analytics"   # Mehrrunden-Gespraech (Verlauf nur in der Session)
```

Implementiert: P4 (`analyze`, `eval`), P5 (Persistenz-Befehle), P6 (`ingest`, `set-stage`):

| Befehl | Zweck | Schicht |
|---|---|---|
| `analyze` ✓ | Notes → MEDDPICC-Analyse; mit `--deal` inkl. Vorgänger-Snapshot/Trend + DB-Speicherung | P4/P5 |
| `eval` ✓ | Golden-Set: Ist vs. Soll qualitativ | P4 |
| `add-account` / `add-deal` / `add-contact` ✓ | Stammdaten anlegen (Kontakt mit Dubletten-Schutz) | P5 |
| `list-deals` / `show-deal` ✓ | Deals ansehen (Snapshot, Kontakte, Korrekturen) | P5 |
| `correct` ✓ | Korrektur zum letzten Snapshot speichern (Feedback wird gesammelt; Injektion nach M4) | P5 |
| `export-notes` ✓ | Roh-Notes eines echten Deals in die gitignorte Privat-Ablage (Golden-Set ohne Kundendaten-Leak) | P-GS6 |
| `advise` ✓ | Der Berater: freie Sales-Fragen durch Lions Brille (Kontext: `--deal` / `--pipeline` / `--topics`; `-i` interaktiv) | P-ADV |
| `ingest` ✓ | Text aufnehmen: klassifizieren, Deal auflösen (nachfragen statt raten), routen | P6 |
| `set-stage` ✓ | Stage wechseln; bei CLOSED_* mit `--reason` (Won/Lost, Befund 2.7) | P6 |
| `research` | Deep-Research zu einem Account | M1 |
| `account-map` | Stakeholder-Map | M2 |
| `briefing` | Pipeline-Briefing | M3 |
| `prep` | Meeting-Prep One-Pager | M4 |

_Bewusst kein `compare`-Befehl: der Analyzer berechnet `trend` bereits gegen den
vorigen Snapshot (Review-Befund 1.8)._

## API (P7)
Dünne FastAPI-Haut über exakt den CLI-Funktionen — lokal, ohne Auth (V1), Docs unter `/docs`:
```bash
uvicorn src.api.app:app --reload
```
```bash
# Ingest (409 bei Duplikat; 422 mit Kandidatenliste, wenn Zuordnung < 0.8 — dann deal_name setzen)
curl -X POST localhost:8000/ingest -H 'content-type: application/json' \
  -d '{"text": "Call mit Nordwind wegen Ops-Analytics Rollout ...", "source": "curl"}'

# Deals + Detail (inkl. letzter Snapshot, Kontakte, Korrekturen)
curl localhost:8000/deals
curl localhost:8000/deals/<deal_id>

# Korrektur speichern (original_value wird aus dem letzten Snapshot aufgelöst)
curl -X POST localhost:8000/corrections -H 'content-type: application/json' \
  -d '{"deal_id": "<deal_id>", "field_path": "dimensions.champion.confidence", "corrected_value": "ZU_PRUEFEN"}'

# CSV-Export (Kompatibilität mit Fremdsoftware)
curl -o deals.csv 'localhost:8000/export/csv?entity=deals'
```

## Persistenz (P5)
SQLite (`sales_os.db`, gitignored) hinter einer Repository-Schicht — dem einzigen
Datenbankzugang. Snapshots/Activities/ContactHistory sind **append-only**; die DB ist
die **einzige Quelle der Wahrheit** für Snapshots bekannter Deals (Befund 4.4).
**Schema-Wandel-Konvention V1:** Bei Modelländerungen wird die lokale `.db` gelöscht
und neu aufgebaut (Befund 2.5) — Testdaten sind reproduzierbar; eine
Migrations-Konvention kommt, sobald echte Daten schützenswert sind.

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
knowledge/          Playbooks + Loader (P3) ✓
src/agents/         Einzweck-Agenten (P4 ✓, M1–M4)
src/repository/     einziger DB-Zugang (P5) ✓
src/orchestrator/   Ingestion/Routing (P6) ✓
src/api/            FastAPI (P7) ✓
src/cli.py          Einstiegspunkt
src/config/         settings.py (Konstanten)
tests/              sample_notes/, golden_set/, regression/
```

## Doku
- `CLAUDE.md` — Projektregeln, Architektur, bewusste Entscheidungen.
- `ARCHITECTURE.md` — Datenfluss (wird je Schicht aktualisiert).
- `ARCHITECTURE_REVIEW.md` — Staff-Engineer-Review (P-1).
