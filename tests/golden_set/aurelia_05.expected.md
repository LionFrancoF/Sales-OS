# Soll-Bewertung (Golden Set) — Aurelia Bank AG / Deal "Vela Enterprise (Data Modernization)"

> **Framework: MEDDPICC** (Golden-Set immer MEDDPICC erzwingen).
> **Input-Notes:** aurelia_01.txt … aurelia_05.txt (kumuliert, Stand 07.07.2026).
> **Diese Vorlage von HAND ausfuellen** — Referenz ("Soll") fuer den P4-Vergleich.
> Bei Dimensionen ohne Beleg: UNBEKANNT, evidence leer.
> Confidence-Skala: GESICHERT / WAHRSCHEINLICH / ZU_PRUEFEN / UNBEKANNT.
> Trend: ERSTBEWERTUNG / VERBESSERT / STABIL / VERSCHLECHTERT.

## Metrics
- Findings: Klare Zielmetrik vorhanden — regulatorischer Reporting-Cycle soll von 5 auf 1 Tag sinken; qualitativer Pain ("bindet massiv Leute"). Weitere/monetäre Kennzahlen (FTE, €) fehlen noch.
- Confidence: WAHRSCHEINLICH
- Evidence (woertliche Zitate): "cycle aktuell 5 tage ... -> ziel: runter auf 1 tag" (aurelia_01); "regulatorisches reporting bindet massiv leute" (aurelia_01)
- Gaps: keine Monetarisierung (FTE-Tage/€-Ersparnis), kein Payback/ROI; nur eine Zielgröße, weitere Erfolgskennzahlen offen.
- Trend: ERSTBEWERTUNG
- Recommended action: Business-Case mit Miriam quantifizieren (FTE-Tage × Kosten, Wert eines Tages Verzug) und prüfen, ob sich der Nutzen konkret durchrechnen lässt — harter ROI für Ostermann/Einkauf.
- Next question: "Wie viele FTE-Tage bindet der aktuelle 5-Tage-Cycle pro Monat, und was ist ein Tag Verzögerung regulatorisch/kostenseitig wert?"

## Economic Buyer
- Findings: EB ist Ralf Ostermann (CIO); in Note 05 mit eigenen Worten bestätigt, zuvor nur über Katharina vermittelt. Zusage bislang nur mündlich und unter Vorbehalt (Einkauf/Legal).
- Confidence: WAHRSCHEINLICH
- Evidence: "EB: ... Ralf Ostermann (CIO), sie sagt sie hat sein ohr" (aurelia_01); "ich unterschreibe, sobald einkauf und legal gruen sind" (aurelia_05)
- Gaps: keine schriftliche Zusage/Signatur, kein fixer Termin; Zusage an zwei Bedingungen geknüpft.
- Trend: ERSTBEWERTUNG
- Recommended action: mündliche Zusage verschriftlichen und einen konkreten Signatur-Termin nach Einkauf-/Legal-Freigabe vereinbaren.
- Next question: "Wenn Einkauf und Legal grün sind — können wir Signatur verbindlich auf ein konkretes Datum legen?"

## Decision Criteria
- Findings: Vier explizit genannte technische Kriterien (Data Residency EU/DE, BaFin-konforme Audit-Logs, SSO/AD, SLA 99,9); Data Residency + Security bereits erfüllt/abgenommen. Quelle sind Stakeholder-Aussagen aus dem Tech-Deep-Dive (Kliment/InfoSec + Bender), kein offizielles Ausschreibungsdokument.
- Confidence: WAHRSCHEINLICH
- Evidence: "decision criteria ... 1) data residency EU/DE 2) BaFin-konforme audit logs 3) SSO / AD integration 4) SLA 99,9" (aurelia_02); "Andreas gibt gruenes licht (data residency ... geloest)" (aurelia_03)
- Gaps: Quelle ist mündlich/Stakeholder, nicht formal (offizielles RFP-/Einkaufsdokument steht aus); kommerzielle K.o.-Kriterien (Preisgewichtung Einkauf) nicht definiert; unklar ob die vier Kriterien vollständig/offiziell sind.
- Trend: ERSTBEWERTUNG
- Recommended action: die Kriterien gegen das offizielle Einkaufs-/RFP-Dokument abgleichen und die kommerzielle Gewichtung klären.
- Next question: "Sind diese vier Kriterien offiziell (RFP/Einkauf) festgehalten, und gibt es kommerzielle K.o.-Kriterien?"

## Decision Process
- Findings: Ablauf klar beschrieben — Einkauf (Vergleichsangebote, Lieferantenprüfung, ESG) und Legal (DPA, Verträge) parallel; nach beidseitigem "grün" Signatur durch Ostermann; aktuell ca. 3 Wochen vor Abschluss. (Prozess-Wissen gut; die offenen Punkte sind Timing-Risiken, nicht fehlendes Prozess-Verständnis.)
- Confidence: WAHRSCHEINLICH
- Evidence: "Einkauf ... + Legal ... 8-12 wochen procurement ... Ostermann signiert nach legal/einkauf" (aurelia_03); "procurement fast durch, ... signieren in ca 3 wochen" (aurelia_05)
- Gaps: finale Preisrunde (~355k) offen; letzte SLA-Klausel bei Legal offen; BaFin-Sonderprüfung im Herbst als Timing-Risiko.
- Trend: ERSTBEWERTUNG
- Recommended action: kritischen Pfad (SLA-Klausel, Preis) eng takten und ein- bis zweimal vorsichtig nachhaken, bis Reihenfolge und Signatur-Termin glasklar sind.
- Next question: "Was genau muss zwischen heute und Signatur noch passieren, und wer ist bei der letzten SLA-Klausel der Blocker?"

## Paper Process
- Findings: Detailliert bekannt und aktiv — Einkauf (3 Vergleichsangebote, Lieferantenprüfung, ESG-Fragebogen), Legal (DPA + Verträge, 2 Redline-Runden), Security-Fragebogen; Dauer ~8-12 Wochen; aktuell fast durch: DPA final, nur noch 1 SLA-Klausel offen.
- Confidence: GESICHERT
- Evidence: "Frau Neumann (Einkauf): braucht 3 vergleichsangebote formal, lieferantenpruefung, ESG ... Legal: Dr. Wolff ... DPA ... 8-12 wochen procurement" (aurelia_03); "procurement fast durch ... DPA final, nur noch EINE SLA klausel offen" (aurelia_05)
- Gaps: letzte SLA-Klausel (Legal/Wolff) offen; finaler Preis + Signatur ausstehend.
- Trend: ERSTBEWERTUNG
- Recommended action: proaktiv die Extrameile gehen — kurzen Legal-Sync mit Wolff anbieten, um Support/Bereitschaft zu zeigen und die letzte SLA-Klausel aktiv zu schließen, statt auf den langen Prozess zu vertrauen.
- Next question: "Welche Formulierung der offenen SLA-Klausel akzeptiert Ihr Legal, und können wir dazu diese Woche einen kurzen Sync machen?"

## Identify Pain
- Findings: Klarer, regulatorisch getriebener Pain (Reporting langsam/fehleranfällig/personalintensiv, BaFin). Bislang v.a. von Katharina benannt — nicht von mehreren Stakeholdern bestätigt; Auswirkungen und Profiteure über sie hinaus nicht gesichert.
- Confidence: WAHRSCHEINLICH
- Evidence: "regulatorisches reporting bindet massiv leute, cycle aktuell 5 tage, fehleranfaellig" (aurelia_01)
- Gaps: Maßstab nicht erfüllt (Multi-Stakeholder-Bestätigung, klare Auswirkungen, mehrere Profiteure); hing an Katharina, die jetzt raus ist; Quantifizierung offen (→ Metrics).
- Trend: ERSTBEWERTUNG
- Recommended action: Pain mit Miriam und Ostermann gegenchecken — wer außer Katharina spürt ihn, welche konkreten Auswirkungen, wer profitiert von der Lösung.
- Next question: "Wer in Ihrem Team spürt das Reporting-Problem am stärksten, und welche konkreten Folgen hat ein verspäteter Report?"

## Champion
- Findings: Ursprünglich starke Championin Katharina (VP Data, EB-Zugang, Treiberin) weitgehend abgezogen (payments-Programm), nur noch Sponsor; neue potenzielle Championin Miriam Voss baut sich auf, aber Einfluss/Commitment unbewiesen — Champion-Rolle im Übergang, muss verifiziert werden.
- Confidence: ZU_PRUEFEN
- Evidence: "Katharina SEHR sharp ... sie hat sein ohr / woechentl. update" (aurelia_01); "Katharina wurde teilweise ... abgezogen ... mit einem bein ... risiko" (aurelia_04); "Katharina fast raus, nur noch sponsor ... Miriam ... baut sich intern als treiberin auf" (aurelia_05)
- Gaps: Hat Miriam echten EB-Einfluss (wie Katharina)? Ist ihr Commitment belastbar? Ist Katharina als Sponsor noch aktiv nutzbar?
- Trend: ERSTBEWERTUNG
- Recommended action: Miriam gezielt zum Champion entwickeln (Business-Case/Insider-Infos, Test: vertritt sie uns bei Ostermann?), Katharina als Sponsor halten; nicht single-threaded auf eine Person verlassen.
- Next question: "Miriam, würden Sie den internen Business-Case bei Ostermann mitvertreten — und was brauchen Sie dafür von uns?"

## Competition
- Findings: Wettbewerbssituation über den Einkauf belegt — Pflicht zu Vergleichsangeboten + Preisdruck (unser Angebot ~20% über Wettbewerb). Kein namentlich bekannter aktiver Wettbewerber, kein interner Fürsprecher für eine Konkurrenz identifiziert.
- Confidence: WAHRSCHEINLICH
- Evidence: "wir haben die anderen angebote, Sie liegen 20% drueber" (aurelia_04); "3 vergleichsangebote formal" (aurelia_03)
- Gaps: Wettbewerber unbenannt; echte Konkurrenz vs. reines Einkauf-Benchmarking unklar; interner Fürsprecher? Ist der 20%-Abstand Preis oder Scope?
- Trend: ERSTBEWERTUNG
- Recommended action: herausfinden, gegen welche Anbieter der Einkauf vergleicht und ob jemand intern eine Konkurrenz präferiert; erfüllte Security/Data-Residency als Differenzierung gegen reinen Preis stellen.
- Next question: "Gegen welche Anbieter vergleichen Sie konkret, und ist der 20%-Abstand reiner Preis oder Leistungsumfang?"

## Gesamt
- Overall score (0–100): 55
- Score rationale: Prozessual weit (Paper Process GESICHERT, EB-Zusage mündlich, technische Kriterien erfüllt), aber Qualifizierung fragil — kein bestätigter Champion (ZU_PRUEFEN), sechs Dimensionen nur WAHRSCHEINLICH, nur eine GESICHERT, Budget umkämpft. 55 = leicht über Mitte (Procurement fast durch, EB mündlich zugesagt), aber klar unter "stark", weil der Fortschritt teils auf einer abgezogenen Championin ruht.
- Momentum (POSITIV / NEUTRAL / NEGATIV): POSITIV — korrigiert 16.07.2026 (Lion). Harte Belege im letzten Fenster (Call 5) nach Lions Definition; erster direkter EB-Kontakt mit mündlichem Commitment, Paper Process mit Tier-Bewegung (DPA unterschriftsreif, nur noch eine SLA-Klausel), Preis nahezu final. Der Champion-Bruch (Katharina) lag im VORHERIGEN Fenster (Call 4) — Lions Konfliktregel (beide Richtungen hart im SELBEN Fenster → NEUTRAL) greift hier nicht; das Niveau-Risiko Champion deckelt den Score, nicht das Momentum. Das ursprüngliche NEUTRAL-Label entstand VOR der bindenden Momentum-Definition.
- Deal risks:
  1. Champion-Transition — Katharina abgezogen, Miriam unbewiesen, historisch single-threaded, EB-Zugang ungesichert.
  2. Budget-Squeeze — 400k vom Einkauf infrage gestellt (~20% über Wettbewerb), ~355k noch nicht unterschrieben.
  3. Letzte SLA-Klausel bei Legal (Wolff) offen — potenzieller Verzögerer.
  4. BaFin-Sonderprüfung im Herbst → Ressourcenbindung/Timing-Risiko.
  5. Wettbewerber unbenannt, aber realer Preisdruck.
- Next best questions (max 5, priorisiert):
  1. "Miriam, vertreten Sie den Business-Case bei Ostermann mit — was brauchen Sie dafür?"
  2. "Wenn Einkauf und Legal grün sind — fixieren wir Signatur auf ein konkretes Datum?"
  3. "Welche SLA-Formulierung akzeptiert Ihr Legal — kurzer Sync diese Woche?"
  4. "Gegen welche Anbieter vergleicht der Einkauf, und ist der 20%-Abstand Preis oder Scope?"
  5. "Wie viele FTE-Tage bindet der 5-Tage-Cycle, und was kostet ein Tag Verzug?"
- Summary for manager (3 Saetze, forecast-tauglich): Spät-Stage-Deal (~355k), technische Kriterien erfüllt, Paper Process fast durch (DPA final, 1 SLA-Klausel offen), mündliche Signatur-Zusage des EB (CIO Ostermann). Größtes Risiko ist der Champion-Wechsel (treibende VP Data abgezogen, Nachfolgerin Miriam noch unbewiesen) plus Preisdruck vom Einkauf. Forecast: wahrscheinlich, aber nicht sicher — Abschluss hängt an der Signatur nach Einkauf/Legal und daran, Miriam schnell als belastbaren Champion zu etablieren.
