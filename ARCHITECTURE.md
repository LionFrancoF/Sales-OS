# ARCHITECTURE.md — Sales OS

Systemübersicht und Datenfluss. Wird bei jeder Schicht aktualisiert (DoD 5).
Stand: **Schichten 0–7 komplett.** Der Kern-Datenfluss (ingest → Klassifizierung
→ Resolution → Activity zuerst → Analyzer/Kontakte) ist per CLI und FastAPI
(P7, dünne Haut, /docs) nutzbar. Als Nächstes: Module M1–M4.

## Prinzip
KEIN autonomes Multi-Agenten-System. Ein **Orchestrator** ruft spezialisierte
**Einzweck-Agenten**, die ausschließlich über das gemeinsame **Datenmodell
(Repository)** kooperieren. Deterministisch, testbar, günstig. Schichten von
innen nach außen; Cross-Layer-Verstöße sind Bugs.

## Datenfluss (real ab Schicht 7)

```
                 ┌──────────────┐        ┌──────────────┐
   Zugänge  ─────▶   CLI         │        │   API        │
 (Notes rein)     │  src/cli.py  │        │  src/api/    │  (dünne Haut, P7)
                 └──────┬───────┘        └──────┬───────┘
                        │  gleiche Funktionen   │
                        └───────────┬───────────┘
                                    ▼
                        ┌───────────────────────┐
                        │   Orchestrator (P6)    │
                        │   src/orchestrator/    │
                        │                        │
   process_note() ────▶ │  1. Dedup       (SHA-256; Activity = Wiederaufsetzpunkt)
 (bewusst kein Trigger- │  2. Classifier  (Typ + Signale + Extraktion, Haiku)
  Envelope, Befund 1.5) │  3. Resolver    (Deal-Zuordnung 0.8, nachfragen statt raten)
                        │  4. Router      (Signal -> Agent, regelbasiert)
                        └───────┬───────────────┘
                                │  ruft je nach Signal
              ┌─────────────────┼──────────────────┐
              ▼                 ▼                  ▼
      ┌──────────────┐  ┌──────────────┐   ┌──────────────┐
      │ MEDDPICC (P4)│  │ Research (M1) │   │ Account-Map …│   src/agents/<name>/
      └──────┬───────┘  └──────┬───────┘   └──────┬───────┘   (Prompt + API + Val.)
             │                 │                  │
             │   Knowledge-Injection (P3): src/knowledge/loader.py
             │   zieht Abschnitte aus knowledge/*.md in den System-Prompt
             │                 │                  │
             └─────────────────┼──────────────────┘
                               ▼
                     ┌──────────────────────┐
                     │  Repository (P5)      │  EINZIGER DB-Zugang
                     │  src/repository/      │  (Domain-Modelle rein/raus)
                     └──────────┬────────────┘
                                ▼
                       ┌────────────────┐
                       │  SQLite (*.db) │  append-only Snapshots/Activities
                       └────────────────┘

  Querschnitt (keine Schicht, von überall nutzbar):
    src/config/settings.py   typisierte Konstanten (Modelle, Schwellen,
                             STAGE_GATES, Cost-/Call-Deckel) — kein config.yaml
    src/logging_setup.py     standardisiertes Logging (nie print)
    src/domain/              Pydantic-Modelle (der gemeinsame Vertrag)
```

## Schichten (Reihenfolge = Bauabfolge)
| Schicht | Pfad | Prompt | Status |
|---|---|---|---|
| Domain | `src/domain/` | P1 | ✓ Modelle stehen |
| Knowledge | `knowledge/` + `src/knowledge/` | P3 | ✓ Loader + Playbooks (Inhalte gitignored) |
| Agenten | `src/agents/` | P4, M1–M4 | ✓ MEDDPICC-Analyzer (Opus 4.8, Structured Outputs, Caching, Circuit-Breaker) |
| Repository | `src/repository/` | P5 | ✓ SQLite, append-only Snapshots/Activities/History, Entity-Resolution |
| Orchestrator | `src/orchestrator/` | P6 | ✓ classifier/resolver/ingest (process_note, Wiederaufsetzpunkt) |
| API | `src/api/` | P7 | ✓ FastAPI: ingest/deals/analyze/corrections/export-csv (409/422-Fehlerbild) |
| CLI | `src/cli.py` | P0–P6 | ✓ analyze/eval/ingest/set-stage + Stammdaten (Platzhalter nur M1–M4) |

## Bewusste Abweichungen vom ursprünglichen Plan (P-1)
- **Konfiguration:** typisiertes `src/config/settings.py` statt `config.yaml`
  + pydantic-settings + Feature-Flags (Befund 1.4).
- **Fehler:** stdlib-Exceptions statt `src/exceptions.py` auf Vorrat (Befund 1.7).
- **Kosten:** Cost-/Call-Deckel in settings.py (Befund 2.8); Cost-Logging als
  Log-Zeile statt DB-Tabelle in V1 (Befund 1.1).
Details siehe `ARCHITECTURE_REVIEW.md` und CLAUDE.md → "Bewusste Entscheidungen".
