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
Nur der jüngste Eintrag steht hier — die vollständige Historie liegt in
**SESSIONS.md** (Konvention: beim nächsten Eintrag wandert der vorherige dorthin).

- **2026-07-17 — P-ADV (Berater-Modus V1 + Wissens-Extraktion Teil 2):**
  Vision-Umsetzung nach Grundgesetz-Anpassung. (1) BERATER gebaut:
  `src/agents/advisor/` (Prinzipien-Prompt gemäß Berater-Regel, prompt_version;
  agent.py mit llm.call_text — neuer Text-Call im gemeinsamen LLM-Helper mit
  Breaker+Kosten-Log; context.py = wiederverwendbarer Kontext-Assembler, nur
  Repository, ohne LLM testbar). CLI `advise "<frage>" [--deal | --pipeline |
  --topics a,b] [-i]`; Mehrrunden nur in-memory (kein Konversations-Speicher,
  kein Vorbau). MODEL_ADVISE=Opus. Berater-Brille kuratiert (7 Playbooks mit
  advisor-Frontmatter): 58.001 Zeichen — unter 64k mit ~6k Luft. DoD live:
  Beratungsfrage mit Deal-Kontext — Modell widerspricht der Fragen-Prämisse
  (CFO-Zugang verfrüht), wendet Playbook-Regeln situativ an, markiert
  ANNAHME/ZU_PRUEFEN, findet Datums-Diskrepanz in Demo-Daten; 27 ct/46s.
  (2) Extraktion Teil 2 integriert: negotiation_playbook.md NEU (12. Datei,
  Verhandlungs-Lücke geschlossen) + 7 Playbooks erweitert (12 Discovery-Frage-
  Paare, Buyer's Decision Map als LESE-Schema — Aussagen bewusst KEINE harten
  Momentum-Belege, Lions kalibrierte Definition bleibt maßgeblich; Momentum-
  Käuferverhalten, Evidence over Opinion, CoI, MAP-Adoptions-Test, EB-vor-
  Procurement, Disqual-Regeln, C-Suite-Personas, Trigger-Taxonomie, ICP 5 Fits,
  Sequencing, Social Selling, Reference Ladder, Follow-up-Kadenz). Dabei
  KORRIGIERT (Fremdextraktion enthielt falsche Architektur-Annahmen): kein
  Trigger-Envelope gebaut (1.5), STAGE_GATES liegen in settings.py nicht
  config.yaml (1.4). 64k-Limit erstmals live ausgelöst (meeting_prep 64.095) →
  Kuratierung zurückgenommen statt Limit erhöht; Topic-Profile rücken näher.
  125 pytest grün (9 neue: Kontext-Assembler + Advisor gemockt). Offen: Lions
  Review der neuen Playbook-Abschnitte; Beobachtungsphase Berater-Nutzung
  (welche Fragen wiederholen sich → Produktisierungs-Kandidaten).
