# ARCHITECTURE.md — Sales OS

Systemübersicht und Datenfluss. Wird bei jeder Schicht aktualisiert (DoD 5).
Stand: **P1 (Domain-Kern)** — Pydantic-Modelle in `src/domain/` stehen; noch
keine DB/Agenten/API. Der Datenfluss unten ist Ziel-Architektur.

## Prinzip
KEIN autonomes Multi-Agenten-System. Ein **Orchestrator** ruft spezialisierte
**Einzweck-Agenten**, die ausschließlich über das gemeinsame **Datenmodell
(Repository)** kooperieren. Deterministisch, testbar, günstig. Schichten von
innen nach außen; Cross-Layer-Verstöße sind Bugs.

## Datenfluss (Ziel-Architektur)

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
   Trigger  ──────────▶ │  1. Classifier  (Typ + Signale, Haiku)
 {NOTES|TIME|EVENT}     │  2. Resolver    (Deal/Kontakt-Zuordnung, Schwelle 0.8)
   V1: nur NOTES        │  3. Dedup       (SHA-256 über Roh-Text)
                        │  4. Router      (Signal -> Agent)
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
| Knowledge | `knowledge/` + `src/knowledge/` | P3 | leer (P0) |
| Agenten | `src/agents/` | P4, M1–M4 | leer (P0) |
| Repository | `src/repository/` | P5 | leer (P0) |
| Orchestrator | `src/orchestrator/` | P6 | leer (P0) |
| API | `src/api/` | P7 | leer (P0) |
| CLI | `src/cli.py` | P0 | Gerüst (Platzhalter) |

## Bewusste Abweichungen vom ursprünglichen Plan (P-1)
- **Konfiguration:** typisiertes `src/config/settings.py` statt `config.yaml`
  + pydantic-settings + Feature-Flags (Befund 1.4).
- **Fehler:** stdlib-Exceptions statt `src/exceptions.py` auf Vorrat (Befund 1.7).
- **Kosten:** Cost-/Call-Deckel in settings.py (Befund 2.8); Cost-Logging als
  Log-Zeile statt DB-Tabelle in V1 (Befund 1.1).
Details siehe `ARCHITECTURE_REVIEW.md` und CLAUDE.md → "Bewusste Entscheidungen".
