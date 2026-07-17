# Session-Log-Archiv — Sales OS

Vollständige Historie aller Sessions (ausgelagert aus CLAUDE.md am 17.07.2026,
damit die bindenden Regeln dort nicht unter Protokoll begraben werden).
Konvention: Der JÜNGSTE Eintrag steht in CLAUDE.md; beim nächsten Eintrag
wandert der vorherige hierher.

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
