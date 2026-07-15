# Architecture Review — Sales OS (v5, Plan-Freeze)

Reviewer-Rolle: Staff Engineer. Kein Code geändert. Bewertungsmaßstab durchgehend:
**Ein Solo-Entwickler baut ein lokales Single-User-Tool, das nebenbei Portfolio ist.**
Dieser eine Satz entscheidet fast jeden Befund unten. Der Plan widerspricht sich in
genau diesem Punkt: Die `CLAUDE.md` predigt "Einfachheit schlägt Perfektion" und
"Ist das heute wirklich notwendig?" — der Plan selbst spezifiziert dann einen Event-
Bus, ein Graph-Modell, eine Config-Management-Schicht, Feature-Flags und Reproduzier-
barkeits-Metadaten, bevor der erste Prompt läuft.

## Kern-Diagnose in einem Satz
Der Plan ist für **20 Entwickler entworfen und von 1 ausgeführt**. Fast alles, was ich
unter Frage 6 in die "20-Dev-Spalte" schreibe, steht bereits in der V1-Spezifikation.
Diese Differenz IST der Befund; die Einzelpunkte sind nur Belege.

---

## 0. Was richtig ist (nicht anfassen — damit die Kritik zielt)

- **Nicht-autonome Agenten über shared State (Repository).** Deterministisch, testbar,
  günstig. Genau die richtige Wahl gegen den Multi-Agenten-Hype. Behalten.
- **Append-only Snapshots für Trend.** Sauber. Ermöglicht `trend` ohne Extra-Buchhaltung.
- **Entity-Resolution mit Schwelle + "fragen statt raten".** Die Intuition "falsch
  zugeordnete Note = giftigster Fehler" ist korrekt und selten so klar benannt.
- **Modell-Tiering (Haiku klassifiziert / Opus analysiert).** Vernünftig, spart real Geld.
- **Confidence-Tiering als Produktprinzip.** Für ein Sales-Tool, wo halluzinierte
  "Fakten" teuer sind, ist das die richtige Härte.
- **Domain-first schichten.** Instinkt richtig — nur die *Anzahl* Schichten ist für Solo falsch.

Alles andere unten ist Angriffsfläche.

---

## 1. Overengineered für V1 (konkret)

**Befund 1.1 — Reproduzierbarkeits- & Cost-Metadaten (prompt_hash, knowledge_version, model, temperature, timestamp + LLM-Cost-Tracking + eval_log.csv → LlmCall-Tabelle).**
- Beobachtung: An jedem Analyse-Lauf hängen 5 Metadatenfelder plus ein DB-migriertes
  Cost-Ledger.
- Begründung: Das ist MLOps-Zeremonie aus einer CI-gegateten Team-Pipeline. Du bist ein
  Nutzer mit einem API-Key. Cost pro Call in einer Tabelle zu führen ist Buchhaltung ohne
  Leser. `knowledge_version` als Hash der Playbooks zu tracken lohnt erst, wenn mehrere
  Leute Playbooks parallel ändern.
- Empfehlung: Für V1 EINE `logging.info`-Zeile pro Call (model, tokens, grober Cent-Betrag).
  `prompt_version` (schon in `MeddpiccSnapshot`) reicht für Rückverfolgung. Cost-Tabelle
  und eval_log.csv streichen, bis du sie tatsächlich liest.

**Befund 1.2 — Event-Log-Tabelle ab Schicht 5.**
- Beobachtung: Append-only Audit jeder Agenten-Aktion, begründet mit "später gratis für
  Won/Lost, Signal-Monitoring, Debugging".
- Begründung: Klassisches YAGNI mit Vorrats-Rechtfertigung. Du baust das Audit-Substrat
  für Backlog-Features, die vielleicht nie kommen. "Billig jetzt" ist die Standard-Falle:
  billig zu bauen, teuer im kognitiven Rauschen jeder Schicht.
- Empfehlung: Streichen. Einführen, wenn Won/Lost oder Signal-Monitoring konkret gebaut
  wird — die brauchen es dann und definieren sein Schema präzise.

**Befund 1.3 — ContactRelationship-Graph + paths_to_power (P1 + P9).**
- Beobachtung: Beziehungskanten-Modell in Schicht 1, Pfad-zu-Power-Analyse in M2.
- Begründung: Du hast null Kontakte und null Kanten. "Weg zum Economic Buyer über X→Y" ist
  Fantasie-Architektur, solange kein einziger echter Account gemappt ist. Die Kanten
  bleiben monatelang leer; die Analyse läuft ins Nichts.
- Empfehlung: Komplett aus V1 streichen. Wiederkommen, wenn du ≥1 realen Account manuell
  gemappt hast und den Schmerz spürst, die Kanten NICHT zu haben.

**Befund 1.4 — config.yaml + pydantic-settings-Validierungsschicht + Feature-Flags.**
- Beobachtung: YAML im Root, geladen/validiert von `settings.py`, plus Flags
  (ENABLE_RESEARCH / ENABLE_FEEDBACK_INJECTION / ENABLE_CACHE).
- Begründung: Flags entkoppeln Deploy von Release über ein Team/über Nutzer hinweg. Du hast
  einen Nutzer und keinen Deploy. YAML+Loader+Validierung ist eine Schicht, die nichts
  verdient, solange kein Nicht-Engineer Config editiert — du editierst Python fließend.
- Empfehlung: Ein typisiertes `settings.py` mit Konstanten (inkl. STAGE_GATES als dict).
  Typsicher ist es damit schon. YAML reintun, wenn du es je einem Nicht-Entwickler gibst.
  Flags durch Code-Präsenz ersetzen: Feature da = an.

**Befund 1.5 — Trigger-generischer Orchestrator (NOTES|TIME|EXTERNAL_EVENT) + "PLANNING-Modus-Tür".**
- Beobachtung: Generischer Trigger-Envelope und Router-Struktur, obwohl nur NOTES gebaut wird;
  zusätzlich Struktur, die einen späteren LLM-Planner "ohne Umbau" erlaubt.
- Begründung: Speculative Generality in Reinform. Du entwirfst das Routing für Trigger, die
  nicht existieren, und lässt Platz für einen Modus, den du nicht planst. Die "kein-Umbau"-
  Versprechung ist fast immer falsch — die zweite Trigger-Art bringt Anforderungen mit, die
  dein heutiger Envelope nicht vorhersieht.
- Empfehlung: `process_note(text, deal=None)` direkt bauen. Generalisieren, wenn die zweite
  Trigger-Art real ankommt. Der Umbau von einem konkreten Fall auf zwei ist billig und
  informiert; der Vorbau auf N ist teuer und blind.

**Befund 1.6 — MEDDICC/MEDDPICC-Dual-Framework mit Auto-Wahl + Begründung.**
- Beobachtung: Der Analyzer wählt Framework, begründet die Wahl, `framework_override` sticht.
- Begründung: Extra-Verzweigung im *schwierigsten* Prompt für marginalen Nutzen. Die
  Golden-Set-Deals erzwingen ohnehin MEDDPICC — die Dual-Logik ist also nicht mal getestet.
- Empfehlung: V1 immer MEDDPICC. `framework`-Feld behalten (billig), Auto-Wahl-Logik streichen.

**Befund 1.7 — Custom-Exception-Hierarchie vorab in P0.**
- Beobachtung: EntityNotFound, ResolverError, KnowledgeError, AgentError, EvaluationError
  definiert, bevor Code existiert, der sie wirft.
- Begründung: Exceptions definiert man, wenn man sie *unterschiedlich fangen* muss, nicht auf
  Vorrat. Fünf leere Klassen sind fünf Entscheidungen, die noch keinen Nutzen haben.
- Empfehlung: Pro Bedarf einführen. Bis dahin `ValueError`/`LookupError` mit klarer Message.

**Befund 1.8 — `compare`-CLI-Befehl (P4).**
- Beobachtung: Eigener Befehl "alt.json vs neu.json".
- Begründung: Der Analyzer berechnet `trend` bereits gegen `previous_snapshot`. `compare` ist
  redundante Oberfläche für dieselbe Information.
- Empfehlung: Streichen. Trend im `show-deal`/analyze-Output zeigen.

**Befund 1.9 — Doppelte Persistenz (Datei in outputs/ UND DB), "for now".**
- Beobachtung: Snapshots landen parallel als JSON-Datei und in SQLite.
- Begründung: Zwei Quellen der Wahrheit = doppelte Buchhaltung und Divergenz-Risiko.
- Empfehlung: Ab P5 ist die DB die einzige Wahrheit. `dump`-Befehl für On-Demand-JSON.

**Befund 1.10 — Der Plan verletzt seine eigene Regel "keine Vorgriffe".**
- Beobachtung: P1 (Domain) enthält schon ContactRelationship (für P9), win_probability +
  STAGE_GATES (für M3), Correction (für P5).
- Begründung: Die Domain-Schicht lädt Felder für Features 8 Schichten voraus. Genau der
  Anti-YAGNI, den die "Eisernen Regeln" verbieten. Die Regel ist gut; sie wird gebrochen.
- Empfehlung: P1 auf das reduzieren, was P2–P4 wirklich brauchen: Account, Contact (Basis +
  role/influence/disposition), Deal (stage), Activity, MeddpiccSnapshot. Rest bei seiner Schicht.

---

## 2. Was fehlt

**Befund 2.1 — Der Capture-Schritt. Das eigentliche Adoptionsrisiko.**
- Beobachtung: Das ganze System nimmt an, dass du `.txt`-Dateien pastest und `ingest note.txt`
  tippst. Kein Wort dazu, ob du das nach einem echten Call tatsächlich tun wirst.
- Begründung: Der Flaschenhals eines persönlichen Sales-Tools ist NICHT die Analyse — es ist,
  ob die Notiz überhaupt reinkommt. Wenn Capture Reibung hat, bleibt die DB leer und jeder
  Downstream-Agent ist wertlos. Der Plan investiert 11 Prompts in Downstream und 0 in Capture.
- Empfehlung: Vor M-Modulen den dümmsten möglichen Capture-Pfad bauen und selbst 2 Wochen
  benutzen: `ingest -` (stdin-paste) muss reibungslos sein; evtl. ein Alias/Hotkey. Erst wenn
  du selbst täglich fütterst, lohnt der Rest.

**Befund 2.2 — Kontext-/Größenmanagement der Prompts.**
- Beobachtung: `analyze(notes, previous_snapshot, deal)` — offen, ob ALLE Notes und der volle
  vorige Snapshot bei jedem Lauf mitgehen.
- Begründung: Notes akkumulieren. Bei Deal #1 mit 20 Activities wächst Kontext, Latenz und
  Cost pro `ingest` superlinear. Es gibt keine Fenster-/Kompaktierungsstrategie.
- Empfehlung: Den Snapshot als Kompaktierungsgrenze nutzen: an den Analyzer nur
  `[letzter Snapshot] + [neue Note]` geben, nicht die Roh-Historie. Das begrenzt Kontext und
  Kosten unabhängig vom Deal-Alter. (Siehe 4.1.)

**Befund 2.3 — Golden-Set mit n=3 macht die Eval-Zahl bedeutungslos.**
- Beobachtung: 3 handbewertete Notes; `eval` liefert eine gewichtete Gesamtzahl.
- Begründung: Eine Metrik aus n=3 ist Rauschen. Eine Prompt-Änderung, die den Score bewegt,
  ist statistisch nicht von Zufall unterscheidbar. Das Eval-Harness ist aufwändig; der
  Datensatz macht es sinnlos. P4 nennt die Eval-Iteration "wo Qualität entsteht" — auf n=3.
- Empfehlung: Plan zum Wachsen auf ≥20–30 Beispiele ergänzen. Bis dahin: Eval qualitativ
  (Ist vs. Soll nebeneinander), keine Einzelzahl vorgaukeln. (Siehe 4.2.)

**Befund 2.4 — Transaktionsgrenze bei synchroner Multi-Call-Ingestion.**
- Beobachtung: Ein `ingest` macht mehrere LLM-Calls und mehrere DB-Writes (Activity, Snapshot,
  Kontakte, Events).
- Begründung: Wenn Call 3 von 5 fehlschlägt — Activity persistiert, Snapshot nicht — in welchem
  Zustand ist die DB? Keine Transaktionsgrenze definiert. Append-only mildert, löst es nicht.
- Empfehlung: `ingest` in EINE SQLite-Transaktion klammern (Activity zuerst, dann Rest, commit
  am Ende) oder klaren Wiederaufsetzpunkt definieren. Mindestens dokumentieren.

**Befund 2.5 — Kein Schema-Migrationspfad.**
- Beobachtung: DB-Schema "aus Domain-Modellen abgeleitet".
- Begründung: Fügst du einem Pydantic-Modell ein Feld hinzu, migriert die SQLite-Tabelle nicht
  mit. Du wirst wiederholt die `.db` löschen — also Daten wegwerfen, genau das Gegenteil von
  "Daten überleben Neustart".
- Empfehlung: Simple Migrations-Konvention (nummerierte `migrations/NNN.sql` + `schema_version`-
  Pragma) oder bewusst dokumentieren "V1: bei Modelländerung DB neu, Testdaten reproduzierbar".

**Befund 2.6 — Re-Analyse-Dedup fehlt; Trend wird verschmutzt.**
- Beobachtung: Idempotenz ist Hash über Roh-Note. Aber `analyze` desselben Deals ohne neue Note
  erzeugt jedes Mal einen NEUEN append-only Snapshot.
- Begründung: Die Snapshot-Historie füllt sich mit identischen Re-Runs; `trend` (Snapshot-zu-
  Snapshot) rechnet dann Rauschen. Das Dedup schützt Notes, nicht Analysen.
- Empfehlung: Snapshot nur schreiben, wenn sich Input-Hash (Notes + previous_snapshot_id) oder
  Ergebnis ändert. Sonst "unverändert" melden.

**Befund 2.7 — Kein Ground-Truth-Signal (Won/Lost).**
- Beobachtung: Der Feedback-Loop erfasst nur DEINE Korrekturen an der LLM.
- Begründung: Das wertvollste Trainingssignal — hat der Deal geschlossen? war der "Champion"
  wirklich Champion? — ist ins Backlog verschoben. Ohne Realitäts-Rückkopplung optimierst du
  auf deine eigene Meinung, nicht auf Ausgang.
- Empfehlung: Won/Lost minimal früh erfassen (Deal-Stage CLOSED_WON/LOST + ein Freitext
  "warum"). Kostet fast nichts, ist aber das einzige nicht nachholbare Signal aus der Realität.

**Befund 2.8 — Kein Cost-Circuit-Breaker.**
- Beobachtung: Cost wird akribisch geloggt, aber nirgends gedeckelt.
- Begründung: Ein Research-Lauf (5–8 Queries × 2–3 volle Seiten × Opus-Synthese) plus Retries
  kann teuer werden; eine Schleife hat keinen Anschlag.
- Empfehlung: Harter Call-/Token-Deckel pro Kommando in `settings.py`, überschritten → Abbruch
  mit Meldung. Ironischerweise nützlicher als das ganze Cost-Ledger.

---

## 3. Spätere Bottlenecks

**Befund 3.1 — Synchrone Ingestion × wachsender Kontext.** Erste harte Wand. Jedes `ingest`
re-runt Klassifizierung + MEDDPICC (Opus) über die volle Historie, wenn 2.2 nicht gelöst ist.
Latenz und Cost pro Note steigen mit Deal-Alter. → 2.2/4.1 lösen das vorab.

**Befund 3.2 — Knowledge-Char-Limit (8000) mit stiller Priorisierungs-Trunkierung.** Wächst die
Wissensbasis (10 Dateien, sektioniert), wirft der Loader stumm Inhalt über dem Limit weg. Stille
Trunkierung genau des Wissens, das Qualität *definiert*, ist eine unsichtbare Qualitätsregression.
Der Bottleneck sitzt auf dem, was das Tool gut macht. → 4.5.

**Befund 3.3 — Eval-Gate mit n=3.** Der gesamte Qualitätsprozess (P4: "2–4 Iterationszyklen")
ruht auf 3 Beispielen. Du overfittest Prompts auf 3 Notes und nennst es Fortschritt. → 2.3/4.2.

**Befund 3.4 — SQLite-Single-Writer × FastAPI × späteres Tauri/MCP.** Für Single-User-CLI ok.
Sobald API (P7) nebenläufige Requests oder Signal-Monitoring async schreibt, wird der eine
Writer zum Nadelöhr. Vorhersehbar, nicht dringend.

**Befund 3.5 — Prompt-Caching-Annahme bricht leicht.** 90 % Ersparnis nur, wenn das
System+Knowledge-Prefix byte-identisch über Calls ist. `corrections_block` und per-Deal-Kontext
zerschießen die Cache-Grenze, wenn die Reihenfolge nicht diszipliniert ist (Cachefähiges zuerst,
Variables ganz hinten). Risiko: du zahlst vollen Preis und glaubst, du sparst.
- Empfehlung: Prefix-Reihenfolge festnageln: `[System] [Knowledge] | [Corrections] [Deal-Kontext]
  [Note]`. Cache-Grenze exakt nach Knowledge. In einem Test verifizieren (cache_read_tokens > 0).

---

## 4. Was ich anders bauen würde — und wie

**4.1 — Ingestion-State:** Snapshot IST der komprimierte Deal-Zustand. Analyzer bekommt
`[letzter Snapshot] + [neue Note]`, nie die Roh-Historie. Bounded context, konstante Kosten.

**4.2 — Eval:** Die Zahl-aus-n=3 weglassen. Bis ≥20 Beispiele: `eval` zeigt Ist vs. Soll
nebeneinander (Diff), Mensch urteilt. Zahl einführen, wenn der Datensatz sie trägt. Das Harness
ist gut — es hungert nur nach Daten.

**4.3 — Config:** config.yaml + pydantic-settings + Flags → ein typisiertes `settings.py`
(Konstanten + STAGE_GATES-dict). YAML zurückholen, wenn ein Nicht-Engineer tunt.

**4.4 — Persistenz:** Kein Parallel-File+DB. DB = Wahrheit ab P5, `dump` für JSON on demand.

**4.5 — Knowledge-Loader:** Statt stiller Char-Trunkierung: jeder Agent benennt explizit die
Sektionen, die er will; überschreitet die Auswahl das Budget → **laut fehlschlagen**, du wählst.
Nie stumm Qualität wegwerfen.

**4.6 — Classifier+Resolver+Router:** Statt drei separater LLM-Stufen ein gut geprompteter Call,
der Klassifizierung + Extraktion + Zuordnungsvorschläge in einem Rutsch liefert; deterministischer
Code nur dort, wo das Modell nachweislich unzuverlässig ist. Weniger Calls, weniger Latenz,
weniger Glue.

---

## 5. Komplett streichen (V1)

- ContactRelationship + paths_to_power (1.3) — null Daten.
- Event-Log-Tabelle (1.2) — mit Won/Lost/Signal-Monitoring nachziehen.
- LLM-Cost-Tabelle + eval_log.csv + LlmCall-Migration (1.1) — eine Log-Zeile reicht.
- Feature-Flags (1.4) — Code-Präsenz = Feature an.
- MEDDICC/MEDDPICC-Auto-Wahl (1.6) — immer MEDDPICC.
- Trigger-Envelope + PLANNING-Modus-Gerüst (1.5) — NOTES direkt.
- `compare`-Befehl (1.8) — redundant mit trend.
- Custom-Exceptions vorab (1.7) — pro Bedarf.
- Doppelte Persistenz (1.9) — DB only.
- research-apply/ingest-linkedin-Politur + Account-Map-Auto-Run-nach-Ingest — M-Tier, später.

Grober Effekt: ~40–50 % der V1-Spezifikationsfläche fällt weg, ohne dass ein *heutiges*
Feature verschwindet.

---

## 6. Solo vs. 20 Entwickler (der aufschlussreichste Punkt)

**Solo (dein realer Fall):** Schichten kollabieren.
`domain/` (Pydantic) + ein `store.py` (SQLite, KEINE Repository-Abstraktion) + `agents/`
(2–3 Prompt+Call-Funktionen) + `cli.py`. Kein Orchestrator-Abstraktum — eine `process_note()`
mit if/elif auf Signale. Keine API, bis ein Consumer existiert. ~6–8 Dateien.
Repository-Pattern, Trigger-Genericität, Config-Schicht, Flags, Event-Log existieren, um
Veränderung über Menschen zu managen, die keinen Kopf teilen. Du teilst deinen Kopf mit dir
selbst. Die Rechtfertigung "austauschbar für HubSpot/Postgres/Fremd-CRM" ist eine
Produkt-/20-Dev-Sorge, in ein Solo-Tool geschmuggelt. YAGNI, bis ein zweites Backend real ist.

**20 Entwickler:** Jetzt verdienen Grenzen ihren Preis — aber du zögest sie anders:
Repository wird echtes Interface mit Postgres-Impl (SQLite überlebt Nebenläufigkeit nicht);
Orchestrator wird Job-Queue (async, Retries, Idempotenz-Keys); Agenten werden unabhängig
deploy-/ownbar mit Contract-Tests auf ihren I/O-Schemata; Knowledge-Base wird versioniertes,
reviewtes Artefakt; Eval wird CI-gegatet auf großem Datensatz.

**Die Pointe:** Der Plan *architektiert wie für 20* (Interfaces, Schichten, Flags, Audit-Log,
Reproduzierbarkeits-Metadaten) und wird *von 1 ausgeführt*. Der Abstand zwischen beiden Spalten
ist exakt der Overhead des Plans — und fast der ganze 20-Dev-Inhalt steht schon in V1.

---

## 7. Wie Anthropic / OpenAI / Linear das strukturieren würden

**Linear — Scope-Disziplin:** Dünnste vertikale Scheibe, die ein echter Nutzer täglich anfasst:
Note pasten → MEDDPICC-Analyse → beim nächsten Mal wiedersehen. Ein Binary, ein Datastore, keine
Schicht ohne heutiges Feature dahinter. Sie löschen ~60 % dieses Plans und shippen in einer
Woche, dann diktiert echte Nutzung den nächsten Schnitt. Ihr Fokus läge auf dem Capture-Loop
(Befund 2.1), nicht auf der Architektur.

**Anthropic / OpenAI — als AI-Produkt:** Sie invertieren die Betonung. Der Wert steckt in
Prompts und Eval, nicht in der Plumbing. Ernstes Eval-Harness ZUERST (Dutzende bewertete
Beispiele, nicht 3), Prompts als versionierte Artefakte mit echter Regression-Suite, App-Skelett
bewusst dumm. Sie lehnen sich stärker aufs Modell: ein gut geprompteter Call für
Klassifizierung+Extraktion+Resolution statt handgebauter Pipeline, deterministischer Code nur wo
das Modell versagt (Befund 4.6). Sie würden keine starren Confidence-/Framework-Enums vorab
hart-codieren, sondern *messen*, wo das Modell scheitert, und dort constrainen. Instrumentierung
für **Eval**, nicht für Cost-Accounting.

**Gemeinsamer Faden:** Alle drei würden das *eigene* Prinzip des Plans — "Ist das heute wirklich
notwendig?" — deutlich härter durchziehen als der Plan es tut.

---

## Widersprüche im Dokument (nebenbei, aber real)

- **Modell hartcodiert & falsch getiert:** P4 sagt `agent.py` nutzt `claude-sonnet-4-6` —
  während `CLAUDE.md` "NIE hartcodieren" fordert UND MEDDPICC-Analyse auf `MODEL_ANALYZE =
  opus-4-8` legt. Dreifachverstoß: hartcodiert, veraltet, falsches Tier. → aus `settings.py`
  ziehen, Opus für Analyse.
- **"Keine Vorgriffe" vs. Domain-Vorbau:** siehe Befund 1.10.
- **"Einfachheit schlägt Perfektion" (CLAUDE.md) vs. Event-Bus/Graph/Config-Schicht/Flags in
  V1:** das Dokument sagt A und spezifiziert B.

---

## Priorisierte Handlungsliste (wenn du nur 5 Dinge übernimmst)

1. **Capture zuerst** (2.1) — sonst ist alles andere Deko.
2. **Golden-Set auf ≥20 wachsen ODER Eval-Zahl weglassen** (2.3/4.2).
3. **Snapshot als Kontext-Grenze** (2.2/4.1) — verhindert den ersten Bottleneck.
4. **Schichten für Solo kollabieren** (Frage 6) — Repository/Orchestrator/Config-Schicht/Flags raus.
5. **Streich-Liste 5 anwenden** — Graph, Event-Log, Cost-Tabelle, Dual-Framework, Trigger-Envelope.

Alles hier ist ein Vorschlag zum Ablehnen. Ablehnung ist ein legitimer, dokumentierter Ausgang —
solange sie bewusst ist. Genau dafür ist dieses Review da.
