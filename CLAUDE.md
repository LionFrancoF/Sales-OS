# CLAUDE.md — Sales OS

## Projektziel
AI-natives Sales-Betriebssystem für Enterprise Sales / Forward Deployed
Engineering — im Kern ein BERATER für komplexe Sales-Situationen, KEIN
RAG-System: Lions Playbooks sind die BRILLE, durch die das System denkt
(Volltext-Injection), nicht eine Datenbank, aus der es zitiert. Lion stellt
freie Fragen (Outreach, Account-Strategie, Signale einschätzen, Buying
Committee); das System antwortet flexibel wie ein starkes LLM — aber immer
durch Lions Methodik und auf Basis der gespeicherten Beleglage. Spezialisierte
Agenten (MEDDPICC-Analyse gebaut; Research u.a. geplant) und der
Ingestion-Orchestrator pflegen dafür das gemeinsame Gedächtnis (Datenmodell).
Das System wächst in Etappen: weitere Wissens-Brillen → echte Pipeline (nach
Lions Job-Pause) → ICP/Produktbeschreibung als eigene Knowledge-Dateien.
Zugleich Portfolio-Projekt: Jede Architektur-Entscheidung muss in 2 Sätzen
erklärbar sein.

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
- **[P-1 / 3.2 + 4.5] Knowledge-Limit-Verhalten** → ÜBERNOMMEN (modifiziert).
  KNOWLEDGE_CHAR_LIMIT 8000→24000→**64000** (finale Entscheidung Lion nach
  vollständiger Wissensbasis); bei Überschreitung LAUTER ValueError mit
  Aufstellung — NIE still trunkieren. Warum: stiller Qualitätsverlust wäre eine
  unsichtbare Regression; das Limit ist Runaway-Backstop, kein Sparinstrument.
  Ladephilosophie: Agenten laden VOLLLAST nach `agents:`-Frontmatter (Lions
  eigene Kuratierung = die Adressierung; „nichts verlieren" ≠ „jeder sieht
  alles"). Topic-Profile je Agent NUR, falls der Golden-Set-Eval in P4
  Unfokussiertheit zeigt — erst messen, dann Mechanik.
- **[P3 / IP-Schutz] knowledge/-Inhalte nicht ins public Repo** → `knowledge/*.md`
  gitignored (nur README committed). Warum: Playbooks sind Lions persönliches
  Sales-IP; Code public (Portfolio), Wissen lokal. Konsequenz: separates Backup
  für knowledge/ nötig (kein Git-Backup mehr).
- **[P3 / Format] Abschnitts-Marker `<!-- topic: x -->`** (Lions Datei-Format)
  statt der ursprünglich spezifizierten `<!-- section: ... -->`-Syntax. Warum:
  der Autor der Inhalte definiert das Format, der Loader passt sich an.
  Zusatz: `status: STUB` wird vom Loader übersprungen (kein Skelett-Rauschen
  in Prompts), `FREIGEGEBEN` wird geladen.
- **[P-1 / 1.6] MEDDICC/MEDDPICC-Auto-Wahl** → ÜBERNOMMEN (gestrichen). V1
  analysiert immer alle 8 MEDDPICC-Dimensionen; `framework`-Feld bleibt im
  Modell, `framework_rationale` dokumentiert die Erzwingung. Warum: weniger
  Verzweigung im schwierigsten Prompt; der MEDDICC-Pfad wäre mangels
  Golden-Set-Beispielen ungetestet. Auto-Wahl später nachrüstbar.
- **[P-1 / 1.8] `compare`-CLI-Befehl** → ÜBERNOMMEN (gestrichen). Der Analyzer
  berechnet `trend` bereits gegen den previous_snapshot; Anzeige kommt in P5
  (`show-deal`). Warum: redundante Oberfläche für dieselbe Information.
- **[P-1 / 1.2] Event-Log-Tabelle** → ÜBERNOMMEN (gestrichen). Keine
  events-Tabelle in P5. Warum: Vorrats-Bau für Backlog-Features; wird mit
  Won/Lost bzw. Signal-Monitoring eingeführt, wenn deren Anforderungen das
  Schema präzise definieren.
- **[P-1 / 1.9 + 4.4] Doppel-Persistenz** → ÜBERNOMMEN (DB only). Snapshots
  bekannter Deals landen NUR in der DB; outputs/-JSON nur für Analysen ohne
  DB-Deal und eval-Leseartefakte. Warum: eine Quelle der Wahrheit, kein
  Divergenz-Risiko.
- **[P-1 / 2.5] Schema-Wandel** → V1-Konvention statt Migrations-Gerüst: bei
  Modelländerung wird die lokale .db gelöscht/neu aufgebaut (Testdaten
  synthetisch reproduzierbar). Migrations-Konvention kommt, sobald echte
  Daten schützenswert sind. Dokumentiert in settings.py.
- **[P5 / LlmCall-Tabelle]** → nicht gebaut (folgt aus 1.1, bereits in
  Tech-Stack dokumentiert: eine Log-Zeile, keine DB-Cost-Tabelle in V1).
- **[P-1 / 1.5] Trigger-Generizität + PLANNING-Tür** → ÜBERNOMMEN (gestrichen).
  `process_note()` direkt statt Trigger-Envelope {NOTES|TIME|EXTERNAL_EVENT}.
  Warum: Speculative Generality — der Umbau von 1 auf 2 reale Trigger ist später
  billig und informiert; die inneren Bausteine (classifier/resolver/router)
  bleiben wiederverwendbar. Architektur-Absatz entsprechend angepasst.
- **[P-1 / 2.4 + 2.6] Transaktionsgrenze & Re-Analyse-Dedup** → EIN Mechanismus:
  die Activity ist der Wiederaufsetzpunkt. Hash existiert + Snapshot referenziert
  die Activity → "bereits verarbeitet", Abbruch. Hash existiert ohne Snapshot
  (Crash) → Fortsetzung mit bestehender Activity. Je Activity max. EIN Snapshot
  (kein Trend-Rauschen). Warum: selbstheilend ohne Transaktions-Maschinerie.
- **[P-1 / 2.7] Won/Lost-Minimalerfassung** → ÜBERNOMMEN. `close_reason`-Feld
  am Deal + `set-stage`-Befehl (--reason Pflicht bei CLOSED_*). Warum: das Warum
  eines geschlossenen Deals ist das einzige nicht nachholbare Realitäts-Signal;
  das Auswertungs-Modul bleibt Backlog.
- **[P-KAL Hypothese A / Konfliktfall] Momentum-Konfliktregel** → ENTSCHIEDEN
  (Lion, 16.07., Referenzfall Voltara): Harte Belege in BEIDE Richtungen im
  selben Bewertungsfenster → NEUTRAL; Altlasten aus früheren Fenstern drücken
  den Score, nicht das Momentum. Steht im meddpicc_playbook (Momentum-Abschnitt).
- **[P-KAL Hypothese B / Referenzen] Momentum-Labels der Alt-Referenzen** →
  KORRIGIERT (Lion, 16.07.): Meridian NEUTRAL→NEGATIV, Aurelia NEUTRAL→POSITIV.
  Warum: beide Labels entstanden VOR der bindenden Momentum-Definition; das
  Modell wandte die Definition korrekt an. Aurelia bleibt POSITIV, weil der
  Champion-Bruch im Vorfenster lag (Konfliktregel greift nicht).
- **[P-KAL Hypothese C / Score-Anker] Referenz-Bänder statt Formel** →
  ENTSCHIEDEN (Lion, 16.07.): Score wird über verbale Bänder mit Golden-Set-
  Eichpunkten geeicht (0–20 Papyrus 15 · 20–35 Nordwind/Hanseatik 25 · 35–50
  Meridian 40/Voltara 45 · 50–65 Aurelia 55 · 65–80 · 80+), NICHT als
  Tier-Summen-Formel. Warum: Lions Referenz-Urteile folgen nachweislich keiner
  linearen Formel (Analyse über 6 Fälle); Bänder wachsen mit dem Set mit.
- **[Golden-Set-Prozess] Erst Beispiele, dann kalibrieren** → Lions Instinkt
  als Regel: Kalibrier-/Referenzentscheidungen werden erst getroffen, wenn
  diverse Stress-Fälle die Definition getestet haben — nicht umgekehrt.
- **[Vision / 17.07.] Berater-Modus als Haupteingang** → ENTSCHIEDEN (Lion).
  System ist im Kern Berater (Brille, kein RAG); `advise` wird zweiter realer
  Eingang (Prinzipien-Prompt, read-only, drei Kontext-Modi: ohne/--deal/
  --pipeline). Freie Beratung bewusst OHNE Golden-Eval in V1 (Richter: Lion;
  Beleg-Kopplung über Confidence-Sprache macht Fehlurteile erkennbar —
  Korrekturen im Gespräch sind Rohmaterial für spätere Berater-Referenzen).
  M-Rollen neu definiert: M1 = neue Fähigkeit (Web-Research), M2 = neue
  Datenstruktur (Beziehungen), M3/M4 = Produktisierung wiederkehrender
  Berater-Fragen — erst bei belegtem Bedarf aus echter Nutzung, nicht vorab.
- **[Wachstums-Regel / 17.07.]** → in Architektur verankert (bindend):
  Wachsen + Verbinden über gemeinsames Datenmodell und geteilte Bausteine,
  nie über autonome Agent-zu-Agent-Aufrufe; Schnittstellen billig erweiterbar
  bauen, Erweiterungen erst bei Bedarf.

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

Das System hat ZWEI reale Eingänge (Vision-Entscheidung 17.07.2026):
1. `process_note(text)` — Daten REIN: klassifizieren, zuordnen, bewerten,
   Gedächtnis pflegen.
2. Der BERATER (`advise`) — Denken RAUS: freie Fragen durch Lions Brille,
   auf Basis des Gedächtnisses (Repository-Kontext), Antwort in Prosa,
   strikt read-only (Festhalten von Ergebnissen läuft über `ingest`).
   Berater-Regel (BINDEND): Sein Prompt enthält NUR Prinzipien (Rolle,
   Brille, Beleg-Disziplin, Annahmen markieren) — NIE aufgabenspezifische
   Anleitungen. Braucht eine Aufgabenart Spezialbehandlung, wird sie als
   eigener Agent produktisiert statt den Berater-Prompt aufzublähen.
Bewusst KEIN generischer Trigger-Envelope und keine PLANNING-Tür (Befund 1.5,
entschieden bei P6). Die inneren Bausteine (classifier, resolver, Routing-
Schritte, Kontext-Assembler) sind getrennt und wiederverwendbar; kommt später
ein weiterer realer Trigger (Signal-Monitoring, Stale-Alerts), wird dann
informiert generalisiert. Der Router ist regelbasiert (Signal → Agent).

WACHSTUMS-REGEL (BINDEND, Lion 17.07.2026): Das System ist auf Wachsen und
Verbinden ausgelegt — es muss stärker werden können, indem Teile kombiniert
werden. Neue Fähigkeiten (Agenten, Brillen, Datenquellen, Werkzeuge) docken
über die bestehenden Schnittstellen an (Repository, Knowledge-Loader,
Router/Orchestrator) und DÜRFEN und SOLLEN vorhandene Bausteine
wiederverwenden und kombinieren (z.B. Berater nutzt künftige
Research-Ergebnisse; Module nutzen den Berater-Kontext-Assembler).
Verbinden heißt: gemeinsames Datenmodell + geteilte, einzeln testbare
Bausteine — NICHT Agenten, die einander autonom aufrufen. Jede neue
Verbindung bleibt deterministisch, testbar und in 2 Sätzen erklärbar.
Schnittstellen werden so gebaut, dass Erweiterung billig ist; die
Erweiterung selbst wird erst gebaut, wenn sie dran ist.

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
MCP-Server, HubSpot-Sync, Tauri-App, Embeddings für Knowledge Base,
Knowledge-Critic (Agent, der Lions Playbooks auf Widersprüche/Lücken gegenliest).

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
- **2026-07-15 — P2-Gate (Golden Set ausgefüllt):** Alle 3 Vorlagen
  (nordwind_04, aurelia_05, meridian_05) im Sparring mit Claude vollständig
  ausgefüllt (8 MEDDPICC-Dimensionen + Gesamt je Deal). Rollen: Claude =
  Faktenzulieferer/kritischer Sparringspartner, alle Urteile (Confidence, Score,
  Momentum) vom Nutzer. Klar diskriminierende Profile: Nordwind (25, NEGATIV,
  6× ZU_PRUEFEN), Aurelia (55, NEUTRAL, 1× GESICHERT), Meridian (40, NEUTRAL,
  2× GESICHERT). Gate P2 erfüllt — Golden Set ist P4-eval-bereit.
- **2026-07-15 — P3 (Knowledge Base):** Loader (`src/knowledge/loader.py`,
  `load_for(agent, topics)`) mit Datei-Auswahl via Frontmatter (agents/topics)
  und Abschnitts-Selektion via `<!-- topic: x -->`; Frontmatter-Handparser (kein
  pyyaml). Lions echte Playbooks verbatim übernommen (meddpicc_playbook ~11k
  Zeichen, cold_call_playbook); 8 Stubs (`status: STUB`, vom Loader übersprungen)
  für die restlichen Dateien. Prompt-Anpassungen nach Review mit Lion: Limit
  24k + laut fehlschlagen statt 8k + still trunkieren (Befund 3.2/4.5); Lions
  Marker-Format; knowledge/*.md gitignored (IP-Schutz, Repo public). 42 pytest
  grün (tests/knowledge/ mit synthetischen Fixtures). Offen: Lion liefert
  restliche Playbooks nach (Loader findet sie automatisch); "Knowledge-Critic"
  (System challenged Playbooks selbst) als Backlog-Kandidat notiert.
- **2026-07-15 — P3-Nachtrag (Wissensbasis komplett):** Alle 11 Playbooks
  geliefert und FREIGEGEBEN (inkl. neuer Datei meddpicc_deal_patterns.md:
  Case-Bibliothek mit Evidenz-Markierung, Frühwarnsignal-Liste, Talk-Tracks,
  Lions bindende Entscheidungen in Abschnitt 5). Loader an Lions Marker-Formen
  angepasst: Multi-Topic (`topic: a, b`), Status-Anhang (`| status: hypothese`),
  und Abschnitts-Marker als präziser Index (zählen auch ohne Frontmatter-Listing).
  44 pytest grün. ENTSCHIEDEN (Lion): Limit auf 64k, Volllast nach
  agents:-Frontmatter; Topic-Profile nur bei Eval-Befund in P4 (siehe
  Bewusste Entscheidungen 3.2+4.5).
- **2026-07-15 — P4 (MEDDPICC-Analyzer, erster Agent):** `src/agents/meddpicc/`
  (schema.py = strikter LLM-Vertrag, alle Felder Pflicht; prompts.py mit
  prompt_version=SHA256-Hash; agent.py mit Structured Outputs via
  messages.parse(), 1 Retry bei Validierungsfehler, Circuit-Breaker 2.8,
  Kosten-Logzeile 1.1; evaluation.py = Golden-Set-Parsing + qualitativer
  Vergleich OHNE Gesamtzahl gemäß 2.3). Modell aus settings.MODEL_ANALYZE
  (Opus 4.8) — der Masterplan-P4-Prompt nannte fälschlich hartcodiert
  claude-sonnet-4-6; CLAUDE.md-Regel + Tiering hatten Vorrang. Hinweis:
  Opus 4.8 akzeptiert kein temperature (API), adaptive thinking aktiv.
  Prompt-Caching live verifiziert (cache_read=24k Tokens, ~16 ct/Analyse).
  CLI: analyze + eval implementiert, compare bewusst nicht (1.8).
  MeddpiccSnapshot um prompt_version-Feld ergänzt (CLAUDE.md-Datenmodell).
  DoD erfüllt: analyze auf allen 3 Test-Accounts, eval gegen Golden Set
  gelaufen (17/24 Confidence-Treffer, Scores Δ +13/−6/+1, prompt_version
  ccaa92ca479d), 58 pytest grün + 1 Echt-API-Test hinter RUN_REAL_API-Flag.
  Offen: Lions Eval-Iterationsphase (Masterplan Teil 5: eval lesen →
  prompts.py/Playbook schärfen → wieder eval); Momentum-Kalibrierung
  auffällig (Modell urteilt extremer als Lions NEUTRAL-Referenzen).
- **2026-07-15 — P5 (Persistenz & Feedback-Speicher):** SQLite hinter
  Repository-Schicht (`src/repository/`: db.py mit Schema, je Aggregat ein
  Modul; Signaturen nehmen/liefern nur Domain-Modelle). 7 Tabellen —
  snapshots/activities/contact_history append-only, raw_text_hash UNIQUE.
  Entity-Resolution-Grundlagen: find_deal_candidates (Account 0.5 + Deal-Tokens
  0.4 + Kontakte 0.3, cap 1.0), find_contact_candidates (exakt/Jaccard/difflib).
  update_contact_alignment protokolliert jede Änderung in contact_history.
  Domain: Correction (aus P1-Deferral zurück) + ContactHistoryEntry neu.
  CLI: add-account/add-deal/add-contact (mit Dubletten-Schutz)/list-deals/
  show-deal/correct; analyze lädt bei --deal den Vorgänger-Snapshot und
  speichert append-only in die DB (DB only, 4.4). Entscheidungen: keine
  Event-Tabelle (1.2), keine LlmCall-Tabelle (1.1), kein Feature-Flag —
  Corrections werden gesammelt, Injektion bleibt unverdrahtet bis nach M4.
  DoD live erfüllt: Account+Deal+Kontakte → analyze (Erstbewertung, DB) →
  show-deal → correct (original_value aus Snapshot aufgelöst) → analyze Note 2
  → erste echte Trend-Bestimmung (3× VERBESSERT exakt bei den neu belegten
  Dimensionen, Score 22→34, 2 append-only Snapshots). 76 pytest grün.
  Offen für P6: Transaktionsgrenze (2.4), Re-Analyse-Dedup (2.6),
  Won/Lost-Minimalerfassung (2.7).
- **2026-07-15 — P6 (Orchestrator/Ingestion, Herzstück):** `src/orchestrator/`
  mit classifier.py (EIN Haiku-Call: Typ + 6 Signale + konservative Kontakt-
  Extraktion, Befund 4.6), resolver.py (regelbasiert, Schwelle 0.8, nachfragen
  statt raten, --deal übersteuert), ingest.py (process_note: Dedup →
  Klassifizieren → Auflösen → Activity ZUERST → Routen). LLM-Helfer nach
  src/agents/llm.py extrahiert (2. Konsument). Entscheidungen (Lion): kein
  Trigger-Envelope (1.5 gestrichen); Activity als Wiederaufsetzpunkt löst
  2.4+2.6 in einem (max. 1 Snapshot je Activity); Won/Lost minimal (2.7:
  close_reason + set-stage, --reason Pflicht bei CLOSED_*); kein Event-Log
  (1.2, Log-Zeilen + IngestReport stattdessen). Analyzer: Widerspruchs-Regel
  (Ingestion-Entscheidung 2) im System-Prompt → neue prompt_version;
  source_activity_ids verdrahtet (Beleg-Kette geschlossen). CLI: ingest
  <datei|-> [--deal], set-stage. DoD live: nordwind_01-04 chronologisch
  ingestiert (Notes 2-4 auto-resolved 0.80), Kontakte erkannt (Markus/Sabine/
  Tobias/Kai/Dr. Kessler als EB), Alignment-Updates mit Historie, Widerspruch
  Note 4 (Budget revidiert) → metrics ZU_PRUEFEN/VERSCHLECHTERT + Klärungsfrage
  in next_best_questions, Score-Verlauf 18→33→31→16, Momentum POSITIV→NEGATIV,
  Dedup-Wiederholung bricht sauber ab. 91 pytest grün. Offen: Lions
  Eval-Iterationsphase (P4); Vorname-only-Erwähnungen landen im Nachfrage-Band
  (konservativ übersprungen bei non-interactive — beobachten).
- **2026-07-15 — P7 (API-Schicht):** `src/api/app.py` — FastAPI als dünne Haut
  über exakt den CLI-Funktionen (process_note, analyze, record_correction,
  Repository): POST /ingest, POST /deals/{id}/analyze, GET /deals,
  GET /deals/{id} (DealDetail: Deal+Account+Kontakte+Snapshot+Korrekturen),
  POST /corrections, GET /export/csv?entity=deals|contacts|activities.
  Fehlerbild: 404 unbekannte Entities, 409 Dedup, 422 mit strukturierter
  Kandidatenliste (API fragt nicht interaktiv nach). Dafür erste eigene
  Exception ResolutionUnclear — konform zu Befund 1.7 (existiert, weil CLI
  und API sie unterschiedlich fangen). record_correction/resolve_field_path
  ins Repository extrahiert (CLI+API teilen sie). Domain-Modelle direkt als
  Response-Modelle. DoD: alle Endpoints via TestClient getestet, kompletter
  Ingest über die API nachgestellt (200→409→422-Pfad), uvicorn-Boot live
  verifiziert (echte P6-Daten via GET /deals, /docs 200). 104 pytest grün.
  Damit sind Schichten 0–7 komplett; als Nächstes M1–M4. Offen: Lions
  Eval-Iterationsphase (P4).
- **2026-07-15 — Eval-Iteration (2 Zyklen) + Vorname-Resolution:**
  Kalibrier-Block im Analyzer-Prompt aus dem Golden-Set-Abgleich (Lions
  Maßstäbe kodiert): GESICHERT braucht formales Artefakt (mündlich bleibt
  mündlich, auch vom EB/Einkauf); EB-Regel (direktes Gespräch notwendig,
  bedingte mündliche Zusage = WAHRSCHEINLICH); Metrics-Leiter (Selbstauskunft
  ZU_PRUEFEN → Treiber-Zielmetrik WAHRSCHEINLICH → kundengerechnete Zahl
  GESICHERT); Momentum = Abwägung, NEUTRAL als Normalfall bei gemischter Lage;
  Signal-Attribution (UNBEKANNT bleibt UNBEKANNT); Competition-Leiter
  (Status-quo-Hypothese ZU_PRUEFEN → belegte unbenannte Angebote WAHRSCHEINLICH
  → benannter aktiver Wettbewerber GESICHERT). Confidence-Treffer 17→19→20/24
  (Aurelia zuletzt 8/8, Nordwind-Lauf-2 8/8); bewusst nach 2 Zyklen gestoppt:
  verbleibende Misses sind flippende Borderline-Zellen (n=3-Rauschen,
  Befund 2.3 — mehr Tuning wäre Overfitting). BEFUND an Lion: Momentum bleibt
  konsistent 1/3 (Modell: Aurelia POSITIV, Meridian NEGATIV vs. Lions NEUTRAL) —
  echte Kalibrierungsdifferenz, keine Zufallsstreuung; ebenso Aurelia-Score
  konstant +15. → Lion entscheidet: Momentum-/Score-Definition im
  meddpicc_playbook präzisieren ODER die zwei NEUTRAL-Referenzen überdenken.
  Außerdem P6-Beobachtung behoben: eindeutiger Vorname im Account-Kontext
  (genau 1 Token-Treffer) → 0.85 auto-Zuordnung statt Nachfrage; mehrdeutig
  bleibt Nachfrage-Band. 107 pytest grün.
- **2026-07-15 — P-KAL (Momentum/Score: Lions Definitionen):** Lions bindende
  Definition „Momentum = Veränderung der Beleglage, NEUTRAL ist Default;
  Score = gewichtete Beleglage + Signal-Bonus max +5" wörtlich ins
  meddpicc_playbook (sein Text, gitignored). Analyzer: momentum_rationale
  (Begründungspflicht: welcher harte Beleg?) + signal_bonus (Pydantic-Deckel
  le=5) in Schema/Snapshot/DB (DB-neu-Konvention) + Erstbewertungs-
  Anwendungsregel (Definitionslücke im Challenge gefunden: Golden Set sind
  Erstbewertungen); Ad-hoc-Momentum/Score-Regeln aus dem Prompt entfernt
  (eine Quelle der Wahrheit = Playbook). correct --golden exportiert
  vorausgefüllte Golden-Set-Kandidaten (tests/golden_set_candidates/,
  gitignored — kann echte Kundendaten enthalten) → organisches Wachstum
  Richtung n>=20. VERIFIKATION (1 Pflicht- + 1 Stabilitätslauf, dann Stopp):
  Scores DEUTLICH besser — Aurelia Δ +15→+11/+12, Meridian Δ −2→0/+2 (exakt),
  Nordwind −1/−3; Bonus genutzt (Aurelia +3, plausibel); Treffer 20/24 u.
  21/24 (keine Regression). Momentum bleibt Aurelia POSITIV/Meridian NEGATIV —
  ABER die momentum_rationales zeigen: das Modell wendet Lions Definition
  KORREKT an (benennt echte harte Belege). HYPOTHESEN an Lion (keine weitere
  Iteration, Befund 2.3): (A) Definitionslücke Konfliktfall — harte Belege in
  BEIDE Richtungen gleichzeitig (Aurelia: EB-Zusage + Champion-Rückzug) sind
  nicht geregelt; Vorschlag-Kandidat „beide Richtungen hart belegt → NEUTRAL".
  (B) Referenz prüfen — Meridian-NEGATIV ist nach Lions EIGENER Definition
  wörtlich begründbar (Julia = „Champion verliert Position"); das
  NEUTRAL-Label entstand vor der Definition. (C) Rest-Score-Lücke Aurelia
  (~+11): Gewichtungsanker der 0-3-Tiers nicht definiert. Entscheidung Lion.
  110 pytest grün.
- **2026-07-16 — P-GS6 (Golden-Set-Ausbau 3→6, Kalibrierung final, Backup):**
  knowledge/ als eigenes privates Git-Repo gesichert (sales-os-knowledge,
  Push verifiziert — P3-Backup-Punkt geschlossen). 3 synthetische Stress-Fälle
  gebaut und von Lion vollständig bewertet (Sparring: Faktenlage je Dimension +
  Optionswahl): hanseatik 25/NEUTRAL (Default-Referenz), voltara 45/NEUTRAL
  (Konfliktfall), papyrus 15/NEUTRAL (Tonalitätsfalle). P-KAL-Hypothesen A/B/C
  entschieden (s. Bewusste Entscheidungen): Konfliktregel + Score-Referenz-
  Bänder ins Playbook (Backup gepusht), Alt-Labels korrigiert (Meridian→NEGATIV,
  Aurelia→POSITIV). Parser-Fix + Regression-Test (Momentum-Zeile kippte bei
  Doppelpunkt im Zusatztext still auf None). Eval-Pflichtlauf über 6 Fälle:
  Scores Δ 0/0/−2/−1/+3/0 (CAVEAT: die Bänder nennen die Eichpunkt-Scores der
  Golden-Deals — deren Score-Läufe sind nicht mehr blind; echter Banktest sind
  künftige Deals). Momentum 4/6: Konfliktregel bei Voltara korrekt angewandt,
  Aurelia/Meridian/Nordwind korrekt. BEFUND an Lion (kein weiteres Tuning,
  Befund 2.3): hanseatik+papyrus NEGATIV statt NEUTRAL mit identischem Muster —
  Modell wertet AUSBLEIBEN angekündigter Aktionen als negative Buyer-Aktion;
  Vorschlag: 1 Klarstellungssatz in Lions Definition. Confidence 33/48 — Alt-
  Fälle stabil (8/8, 6/8, 6/8), neue Fälle 5/8, 5/8, 3/8: tragen Lions
  verschärfte Lesarten aus dem Sparring (EB-Zielmetrik hebt Metrics nicht bei
  Einzelquellen-Rohzahlen; Teil-Artefakt ≠ halbe Dimension; benannter
  Wettbewerber ohne Substanz ≠ WAHRSCHEINLICH; Champion zählt nach heutigem
  Stand) — dokumentiert, bewusst NICHT sofort in den Kalibrier-Block gepflegt.
  Demo correct --golden gelaufen; OFFEN (Entscheidung Lion): Ablage für
  Kandidaten aus ECHTEN Deals (Kundenzitate dürfen nicht ins public Repo,
  eval sucht Notes nur in sample_notes/) → gitignorter Privat-Bereich als
  Kandidat. 112 pytest grün.
- **2026-07-17 — P-GS6b (Kalibrier-Regeln + Privat-Ablage):** Lions 5 Sparring-
  Regeln in den Kalibrier-Block (prompt_version ac1a4beeabbf) + Momentum-
  Klarstellung „Ausbleiben ≠ Gegenbeleg" ins Playbook (gepusht). Privat-Ablage
  gebaut (Entscheidung Lion: Kundenzitate nie ins public Repo):
  tests/{golden_set,sample_notes}/private/ gitignored, find_golden_cases scannt
  private/ mit, neuer CLI-Befehl export-notes <deal> (Roh-Notes aus DB →
  Privat-Ablage, chronologisch; Tests bewusst mit tmp-Zielordner). README
  ergänzt. Verifikationslauf: **Momentum 6/6** (Klarstellung wirkt),
  Scores 4× exakt + Δ−2/−1, Confidence 33→39/48 (Voltara 3→8/8, Papyrus 7/8).
  Verbleibende 9 Misses in 3 Gruppen: (a) 2× Pain-Leiter-Überschärfung — meine
  Kodierung verlangt „realen Vorfall" für WAHRSCHEINLICH, Lions Alt-Referenzen
  (Nordwind/Meridian Pain) geben W auch bei wiederholter, teilquantifizierter
  Artikulation ohne Vorfall → Wording-Fix-Kandidat („ODER"-Klausel);
  (b) 3× UNBEKANNT-Boden — Competition-Leiter Stufe 1 (Status-quo-Hypothese
  = ZP) wird als Boden gelesen, Vor-Stufe „nichts erhoben → UNBEKANNT" fehlt
  in der Leiter selbst → Wording-Fix-Kandidat; (c) 4× echte Grenzfall-Flips
  (Meridian EB G/W + Process, Nordwind Paper, Hanseatik EB) → Rauschen, nicht
  anfassen. Disziplin-Stopp nach diesem Zyklus (Befund 2.3); ob die zwei
  Wording-Fixes einen letzten Mini-Zyklus bekommen, entscheidet Lion.
  116 pytest grün. Haupt-Repo-Push zu GitHub steht aus (wartet auf Lions Go).
- **2026-07-17 — P-GS6c (Mini-Zyklus + ENDGÜLTIGER Tuning-Stopp):** Lions Go
  für alles. Wording-Fixes eingebaut (Pain-Leiter ODER-Klausel, Competition-
  Vorstufe „nichts erhoben → UNBEKANNT"; prompt_version d0dfaebb96be). Finaler
  Lauf: Momentum 6/6 (2. Lauf in Folge), Scores max |Δ2|, Confidence 39/48 —
  Summe wie Vorlauf, aber Zusammensetzung verschoben: die 3 gezielten Fixes
  treffen (Meridian-Pain ✓, Nordwind-Pain ✓, Hanseatik-Competition ✓), dafür
  flippen 3 andere Grenzzellen (Hanseatik Metrics/Paper, Voltara Pain W↔G,
  Papyrus Process). BEFUND: Plateau erreicht — alle Rest-Misses sind
  Nachbarstufen-Flips mit vertretbaren Lesarten in beide Richtungen; weiteres
  Prompt-Tuning würde Rauschen jagen (Befund 2.3 bestätigt sich empirisch).
  Tuning-Stopp ist ENDGÜLTIG; nächster Kalibrier-Anlass erst bei n≥10-12 aus
  echten Deals oder systematischem Fehlermuster im Alltag. Pre-Push-Audit
  bestanden (nur synthetische Daten/Code getrackt; Playbooks, private/,
  Kandidaten, outputs, .env, DB alle ignoriert) → Push zu GitHub (Lions Go).
  116 pytest grün.
