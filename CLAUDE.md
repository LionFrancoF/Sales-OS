# CLAUDE.md — Sales OS

## Projektziel
AI-natives Sales-Betriebssystem für Enterprise Sales / Forward Deployed
Engineering. Mehrere spezialisierte Agenten (MEDDPICC-Analyse, Research,
Account-Mapping, Meeting-Prep, Pipeline-Briefing u.a.) arbeiten über ein
gemeinsames Datenmodell und einen Ingestion-Orchestrator zusammen und
unterstützen den kompletten Sales-Alltag. Zugleich Portfolio-Projekt:
Jede Architektur-Entscheidung muss in 2 Sätzen erklärbar sein.

## Rolle von Claude Code (WICHTIG — zuerst lesen)
Du bist kein Ausführer, du bist mein Senior Engineer. Wenn eine Idee
schlecht ist, widersprich. Wenn eine einfachere Architektur existiert,
nenne sie. Wenn etwas unnötig komplex ist, sag es deutlich — BEVOR du
baust. Baue niemals einfach nur das, was geschrieben steht.
- Bei jeder Schicht gilt: "Ist das heute wirklich notwendig?"
- Bei größeren Architekturentscheidungen: erst Decision-Matrix
  (Problem / Optionen A-B-C / Vor- & Nachteile / Komplexität / Kosten /
  Empfehlung), dann — nach meinem Go — Code.
- Refactoring ist kein Fehler, es ist Teil des Prozesses. Die Architektur
  darf sich verändern. Einfachheit schlägt Perfektion.
- Getroffene UND bewusst abgelehnte Entscheidungen werden unten unter
  "Bewusste Entscheidungen" festgehalten.

## Tech-Stack
- Python 3.11+, Pydantic v2 für ALLE Datenstrukturen
- Claude API. Modelle NIE hartcodieren — immer aus src/config/settings.py.
  Modell-Tiering pro Aufgabe (Stand Juli 2026, in settings.py pflegen):
    * MODEL_CLASSIFY = "claude-haiku-4-5-20251001"  # Klassifizierung, Entity-Resolution, Extraktion
    * MODEL_ANALYZE  = "claude-opus-4-8"            # MEDDPICC-Analyse, Research-Synthese (Qualität kritisch)
    * MODEL_DEFAULT  = "claude-sonnet-5"            # Meeting-Prep, Briefing, mittlere Aufgaben
  Prinzip: teure Reasoning-Qualität nur wo sie zählt; Routine an Haiku.
- Prompt-Caching aktivieren: System-Prompts + Knowledge-Blöcke als
  cache-fähige Prefixe senden (bei jedem Call gleich → bis zu 90% günstiger).
  Reihenfolge diszipliniert halten: [System][Knowledge] cachefähig zuerst,
  [Corrections][Deal-Kontext][Note] variabel dahinter (P-1 Befund 3.5).
- SQLite (ab Schicht 5), FastAPI (ab Schicht 7)
- pytest für Tests, python-dotenv für Secrets
- Code auf Englisch, Feldbeschreibungen/Docstrings auf Deutsch ok
- Konfiguration: typisiertes src/config/settings.py mit Konstanten
  (Modelle, Schwellen wie RESOLUTION_THRESHOLD, STAGE_GATES, Cost-/Call-Deckel).
  KEIN config.yaml, KEINE Feature-Flags (P-1 Befund 1.4) — Single-User, kein
  Deploy: Python-Konstanten sind bereits typsicher. YAML/Flags erst, wenn ein
  Nicht-Engineer tunt bzw. Deploy von Release entkoppelt werden muss.
- Logging: standardisiertes logging-Modul (DEBUG/INFO/WARNING/ERROR), nie print
- Fehler: stdlib-Exceptions (ValueError/LookupError) mit klarer Message.
  KEINE Custom-Exception-Hierarchie auf Vorrat (P-1 Befund 1.7) — eigene
  Exception erst, wenn sie irgendwo unterschiedlich gefangen wird.
- Kosten: harter Cost-/Call-Deckel pro CLI-Aufruf als Konstante in settings.py
  (P-1 Befund 2.8, Circuit Breaker). LLM-Calls werden geloggt (model, tokens,
  grober Cent-Betrag, latency) — eine Log-Zeile, keine DB-Cost-Tabelle in V1.
- Jeder Analyse-Lauf trägt prompt_version für Rückverfolgung.
- Jeder echte Bug und jede Korrektur wird ein Regression-Test (tests/regression/)

## Warum diese Entscheidungen (nicht löschen — sonst vergessen wir es)
- Repository-Pattern: DB austauschbar (SQLite→HubSpot/Postgres), testbar,
  keine Agenten mit SQL.
- Pydantic: ein gemeinsamer Vertrag für alle Agenten + Validierung der
  LLM-Outputs an der Quelle.
- SQLite: null Betriebsaufwand, eine Datei, reicht für Single-User lokal.
- FastAPI: dünne Kompatibilitäts-Haut für App/MCP/Fremd-Software,
  Pydantic-nativ.
- Schichten + Nicht-Ziele: verhindern Vorbauen; Chaos entsteht durch
  Verwobenheit, nicht durch Fehler.
- settings.py statt config.yaml: kein YAML-Loader/Validierungslayer für einen
  Single-User; Konstanten sind schon typsicher (P-1 Befund 1.4/4.3).

## Bewusste Entscheidungen (Log)
Übernahmen UND Ablehnungen aus P-1 und Decision-Matrizen (je 1-2 Zeilen:
Was, Entscheidung, Warum). Volle Begründung: ARCHITECTURE_REVIEW.md.

- **[P-1 / 1.4] config.yaml + pydantic-settings-Schicht + Feature-Flags** →
  ÜBERNOMMEN (gestrichen). Konfiguration liegt in typisiertem
  `src/config/settings.py` als Konstanten (Modelle, Schwellen, STAGE_GATES,
  Cost-Deckel). Warum: Single-User, kein Deploy/Team — YAML-Loader und Flags
  verdienen ihren Preis nicht; Konstanten sind schon typsicher.
- **[P-1 / 1.7] `src/exceptions.py` (Custom-Exceptions auf Vorrat)** →
  ÜBERNOMMEN (gestrichen). stdlib-Exceptions bis zum konkreten Bedarf. Warum:
  Exceptions definiert man, wenn man sie unterschiedlich fängt, nicht prospektiv.
- **[P-1 / 2.8] Cost-Circuit-Breaker** → ÜBERNOMMEN. Harter Cost-/Call-Deckel
  als Konstante in settings.py. Warum: Obergrenze gegen Kosten-Runaway ist
  nützlicher als reines Cost-Logging.
- **[P-1 / 4.3] STAGE_GATES-Ablage** → als Python-`dict` in settings.py statt
  config.yaml. Warum: Folgeentscheidung aus 1.4.
- **[P-1 / 1.10] Domain-Vorbau in P1 (Correction, ContactRelationship)** →
  ÜBERNOMMEN (P1 schlank). `Correction` erst in P5 (Feedback-Speicher),
  `ContactRelationship` erst in M2 (Account-Map). Warum: keine Modelle für Features
  4-8 Schichten voraus — das ist der Anti-YAGNI, den die Eisernen Regeln verbieten.
  (Nachträglich korrigiert: correction.py war in P1 versehentlich mitgebaut worden.)

Weitere P-1-Befunde (Capture-first, Eval-n=3, Snapshot-als-Kontextgrenze,
Event-Log-Tabelle, Trigger-Generizität, Dual-Framework, Re-Analyse-Dedup,
Won/Lost-Signal u.a.) betreffen spätere Schichten (P4/P5/P6) und werden dort pro
Punkt entschieden und hier ergänzt.

## Architektur (BINDEND)
KEIN autonomes Multi-Agenten-System. Agenten entscheiden nicht selbst und
"reden" nicht miteinander. Ein Orchestrator ruft spezialisierte Einzweck-
Agenten (je ein klarer Prompt), die ausschließlich über das gemeinsame
Datenmodell (Repository) kooperieren. Deterministisch, testbar, günstig.

Ingestion läuft vorerst SYNCHRON (mehrere LLM-Calls pro Aufruf) — perfekt
für die CLI. Für eine spätere responsive App: Background-Jobs (Backlog),
daher keine Businesslogik auf synchrone Ausführung fest verdrahten.

Der Orchestrator verarbeitet generische TRIGGER, nicht nur Notes: ein
Trigger hat {type: NOTES | TIME | EXTERNAL_EVENT, payload}. V1 implementiert
nur NOTES, aber Signatur & Routing sind trigger-generisch, damit Signal-
Monitoring und Stale-Alerts (Backlog) ohne Umbau andocken. Der Router ist
regelbasiert (Signal → Agent); die Struktur muss erlauben, später einen
PLANNING-Modus daneben zu setzen (LLM plant Agent-Abfolge für neuartige
Aufgaben), ohne den regelbasierten Pfad zu ändern.
> Anmerkung P-1 (Befund 1.5): Trigger-Generizität + PLANNING-Tür sind als
> spekulativ markiert. Entscheidung übernehmen/ablehnen erfolgt bei P6.

Schichten von innen nach außen. Verstöße gegen diese Regeln sind Bugs:
1. `src/domain/` — Pydantic-Modelle. Null Logik, null Imports aus anderen Schichten.
2. `knowledge/` — Markdown-Playbooks + `src/knowledge/loader.py`. Agenten
   ziehen sich relevante Playbooks in ihren System-Prompt (Injection).
3. `src/agents/<name>/` — je Agent: `schema.py` (falls eigenes Output-Schema),
   `prompts.py` (System-Prompts als Konstanten), `agent.py` (API-Aufruf,
   Parsing, Validierung, 1 Retry bei Validierungsfehler).
4. `src/repository/` — EINZIGER Datenbankzugang. Agenten importieren NIE
   sqlite3/SQL direkt, nur Repository-Funktionen (get_deal, save_snapshot, …).
5. `src/orchestrator/` — Ingestion: klassifiziert eingehende Texte, routet
   an Agenten, schreibt Ergebnisse über das Repository.
6. `src/api/` — FastAPI, dünne Haut: Endpoints rufen dieselben Funktionen
   wie die CLI. Keine Businesslogik in Endpoints.
7. `src/cli.py` — Einstiegspunkt für alle Befehle.
Querschnitt: `src/config/settings.py` (typisierte Konstanten) und
`src/logging_setup.py` (Logging) — keine eigene Schicht, von überall nutzbar.

## Datenmodell (Kern)
Account → Contacts → Deals → Activities → MeddpiccSnapshots (+ Corrections).
- Contact trägt Alignment-Felder: role_in_deal, influence, disposition,
  relationship_strength, last_touchpoint.
- Kontakt-Änderungen NICHT still überschreiben: jede Alignment-Änderung wird
  als ContactHistory-Eintrag protokolliert (alt → neu, Quelle, Zeitpunkt).
  Konsistent zur append-only-Philosophie.
- Kontakt-Entity-Resolution: erwähnte Personen erst gegen bestehende Kontakte
  des Accounts matchen (Name/Alias), bevor ein neuer angelegt wird — sonst
  Dubletten. Analog zur Deal-Resolution mit Schwelle + Nachfrage.
- Snapshots sind append-only und versioniert (nie überschreiben).
- Snapshot trägt `framework: MEDDICC | MEDDPICC` + Begründung der Wahl
  sowie prompt_version (Hash/Nummer des erzeugenden Prompts) für Rückverfolgung.

## Ingestion-Entscheidungen (BINDEND)
1. **Entity-Resolution:** Deal-Angabe optional. Ohne Angabe schlägt der
   Orchestrator eine Zuordnung mit Confidence vor; unter Schwelle
   (RESOLUTION_THRESHOLD = 0.8) fragt er nach statt zu raten. Falsch
   zugeordnete Notes sind das giftigste Fehlerszenario.
2. **Konflikte:** Nie überschreiben. Activities append-only, Bewertungen
   als neue Snapshots. Widerspruch neu vs. alt → Dimension auf ZU_PRUEFEN
   + Widerspruch als Next-Best-Question ausspielen.
3. **Idempotenz:** SHA-256-Hash über die (normalisierten) Roh-Notes; exaktes
   Duplikat wird erkannt, übersprungen und gemeldet. BEKANNTE GRENZE: fängt
   nur identische Notes, nicht nahezu-identische. Bewusst akzeptiert für v1.

## Qualitätsprinzipien
- Confidence-Tiering überall: GESICHERT / WAHRSCHEINLICH / ZU_PRUEFEN /
  UNBEKANNT. Nur wörtlich Belegbares ist GESICHERT. Research-Ergebnisse
  tragen [FACT] (mit Quelle) oder [ESTIMATE].
- Keine Halluzinationen: fehlt eine Dimension in den Notes → UNBEKANNT.
- Golden-Set-Evals: `tests/golden_set/` enthält Notes + handbewertete
  Soll-Analysen. `python -m src.cli eval` vergleicht Ist vs. Soll.
  ACHTUNG P-1 Befund 2.3: bei n≈3 ist eine Einzel-Metrik statistisch Rauschen —
  bis ≥20 Beispiele qualitativ vergleichen (Ist/Soll nebeneinander), Einzelzahl
  erst einführen, wenn der Datensatz sie trägt. Golden-Set-Deals immer mit
  framework=MEDDPICC erzwingen (sonst passen die Soll-Vorlagen nicht).
- Feedback-Loop: `python -m src.cli correct <deal>` speichert Korrekturen;
  Injektion in künftige Analysen bleibt bis nach M4 zurückgestellt (erst
  Fehlermuster kennen, dann Mechanik).

## Definition of Done (jede Schicht)
1. Tests grün (pytest), inkl. mind. 1 End-to-End-Durchlauf mit Beispieldaten.
2. Beispielaufruf in README dokumentiert.
3. Keine Verstöße gegen Architektur-Regeln.
4. Session-Log unten aktualisiert.
5. ARCHITECTURE.md aktualisiert, falls sich der Datenfluss geändert hat.
6. Git-Commit mit aussagekräftiger Message.

## Arbeitsweise mit Claude Code
- Immer zuerst diese Datei lesen.
- Nur den aktuellen Auftrag umsetzen. Nicht-Ziele im Prompt sind bindend —
  NICHTS vorbauen.
- Bei Architektur-Unklarheit: fragen statt annehmen.
- **Bewusste Entscheidungen / Review-Empfehlungen schlagen den Auftrags-Prompt.**
  Bei Widerspruch zwischen einem Auftrags-Prompt (z.B. Masterplan-Schritt) und den
  "Bewussten Entscheidungen" bzw. einer Review-Empfehlung/Plan-Entscheidung gewinnen
  IMMER die Entscheidungen. Jede beabsichtigte Abweichung wird VOR dem Bauen als
  Frage gestellt — nie danach als Transparenz-Notiz gemeldet.
- **Review-Befunde vollständig behandeln.** Wenn eine Scope-Frage aus einem
  Review-Befund abgeleitet wird, müssen ALLE Teile dieses Befunds surfacet werden,
  nicht nur einer. (Lehre aus P1: Befund 1.10 nannte ContactRelationship UND
  Correction als P1-Vorbau — gefragt wurde nur ContactRelationship, Correction still
  mitgebaut. Das war der Fehler, den diese Regel verhindert.)
- Nach jeder Session: Session-Log ergänzen (Datum, was gebaut, offene Punkte).

## Roadmap
Schicht 0–7 (Setup, Domain, Testdaten, Knowledge Base, Analyzer, Persistenz,
Orchestrator, API), dann Module M1–M4 (Research, Account-Map, Pipeline-
Briefing, Meeting-Prep). Backlog: Outreach, Follow-up-Engine, Objection-
Handling, POC-Scoping, MAP-Generator, Won/Lost, Signal-Monitoring,
MCP-Server, HubSpot-Sync, Tauri-App, Embeddings für Knowledge Base.

## Session-Log
- **2026-07-15 — P-1 (Architecture Review):** ARCHITECTURE_REVIEW.md erstellt
  (Staff-Engineer-Review des Masterplans v5, kein Code). Offen: Entscheidungen
  pro Befund.
- **2026-07-15 — P0 (Projekt-Setup):** Projektgerüst "sales-os" angelegt
  (src/-Schichten als leere Packages, tests/-Struktur, README, ARCHITECTURE.md,
  requirements, .env.example, .gitignore, knowledge/README). Review-
  Entscheidungen angewandt: KEIN config.yaml, KEIN src/exceptions.py, KEINE
  Feature-Flags; stattdessen typisiertes src/config/settings.py (Modelle,
  Schwellen, STAGE_GATES, Cost-Deckel). `src/logging_setup.py` als Logging-
  Basis, `src/cli.py` als argparse-Gerüst mit Platzhalter-Befehlen. venv +
  Dependencies. `python -m src.cli --help` läuft. Keine Logik/Modelle/Prompts.
  Offen: weitere P-1-Befunde bei ihren Schichten entscheiden.
- **2026-07-15 — P1 (Domain-Kern):** Pydantic-Aggregate in `src/domain/`
  (account, contact, deal, activity, meddpicc [DimensionAssessment +
  MeddpiccSnapshot]) + Re-Export in `__init__.py`. IDs uuid4,
  Field-Beschreibungen deutsch, `extra="forbid"`. Ableitungen: Deal.win_probability
  aus settings.STAGE_GATES, Activity.raw_text_hash = SHA-256(raw_text). Snapshot
  validiert erlaubte Dimensions-Keys + paper_process-nur-bei-MEDDPICC. 35 pytest
  grün (tests/domain/). Entscheidung: **ContactRelationship (relationship.py)
  bewusst weggelassen** (P-1 Befund 1.3/1.10, schlank) — kommt bei M2. Kleine
  Feld-Politik-Abweichung vom Prompt: unmarkierte beschreibende Felder (title,
  domain, industry, size_estimate) sind optional (Domain-Philosophie UNBEKANNT).
  Offen: weitere P-1-Befunde bei ihren Schichten.
- **2026-07-15 — P1-Fix (Correction entfernt):** `correction.py` + Test +
  README-Zeile entfernt. Grund: Befund 1.10 empfahl Correction für P5, wurde bei
  der P1-Scope-Frage aber nur für ContactRelationship umgesetzt, nicht für
  Correction (Masterplan-Prompt Punkt 7 hatte de facto Vorrang, ohne Nachfrage).
  1.10 jetzt als Bewusste Entscheidung formalisiert; zwei Präventionsregeln unter
  "Arbeitsweise" ergänzt. 30 pytest grün.
- **2026-07-15 — P2 (Testdaten-Fabrik):** 14 messy Call-Notes in
  `tests/sample_notes/` für 3 fiktive Accounts (nordwind_01-04 = frühe Discovery
  m. Lücken + Budget-Widerspruch; aurelia_01-05 = Spät-Stage m. Paper Process +
  Champion-Wechsel + Budget-Squeeze; meridian_01-05 = mid-stage m. stillem Champion
  + aktivem Wettbewerber Fluxion). Rollen nur ableitbar, nie gelabelt. 3 leere
  Golden-Set-Vorlagen (`tests/golden_set/*.expected.md`, Framework MEDDPICC erzwungen)
  — vom Nutzer von Hand auszufüllen. `sample_notes/README.md` mit Verlaufs-Übersicht.
  Keine Analyse/Bewertung durch Claude. Offen (Nutzer): 3 Vorlagen ausfüllen (Gate P2).
