# Soll-Bewertung (Golden Set) — Nordwind Logistics / Deal "Ops-Analytics Rollout"

> **Framework: MEDDPICC** (Golden-Set immer MEDDPICC erzwingen — auch bei duenner Datenlage).
> **Input-Notes:** nordwind_01.txt … nordwind_04.txt (kumuliert, Stand 09.07.2026).
> **Diese Vorlage von HAND ausfuellen** — sie ist die Referenz ("Soll"), gegen die der
> Analyzer in P4 verglichen wird. Bei Dimensionen ohne Beleg: UNBEKANNT, evidence leer.
> Confidence-Skala: GESICHERT / WAHRSCHEINLICH / ZU_PRUEFEN / UNBEKANNT.
> Trend (Erstbewertung): ERSTBEWERTUNG / VERBESSERT / STABIL / VERSCHLECHTERT.

## Metrics
- Findings: Erste quantitative Anhaltspunkte (Tobias verbringt "50-60% der Woche" mit manuellen Reports; Monatsabschluss dauert 8 Tage), aber keine Zielgröße, kein €-Wert, kein Business-Case — und ein einzelner, unvalidierter Selbstbericht.
- Confidence: ZU_PRUEFEN
- Evidence (woertliche Zitate): "Tobias macht die ganzen reports manuell, sagt er verbringt 50-60% der woche damit" (nordwind_02); "monatsabschluss dauert 8 tage" (nordwind_02)
- Gaps: kein Zielwert/€-Nutzen, nicht multi-bestätigt, kein Business-Case.
- Trend: ERSTBEWERTUNG
- Recommended action: die Zeitverschwendung monetarisieren (FTE-Kosten, Fehlerkosten) und über Tobias hinaus bei weiteren Personen bestätigen.
- Next question: "Wie viele Personentage pro Monat gehen unternehmensweit in manuelles Reporting, und was kostet der 8-Tage-Monatsabschluss?"

## Economic Buyer
- Findings: Wahrscheinlicher EB = Dr. Kessler (CFO), aber erst spät und nur vermutet identifiziert ("wohl doch die CFO") und bis heute nie eingebunden — sie kennt das Thema nicht. Kein Zugang, keine Validierung.
- Confidence: ZU_PRUEFEN
- Evidence: "Frau Dr. Kessler ... muss das eh absegnen" (nordwind_03); "Kessler = ist wohl doch die CFO ... ABER ... NOCH NICHT eingebunden, kennt das thema gar nicht" (nordwind_04)
- Gaps: EB nie kontaktiert; Identität nur vermutet; kein Zugang über Markus hinaus.
- Trend: ERSTBEWERTUNG
- Recommended action: Zuerst einen belastbaren Business-Case bauen (harte Zahlen/Metrics, Zeit-/Kostenersparnis, konkrete Mitarbeiter-Situationen); parallel verifizieren, ob die gehörten Namen (Kessler) wirklich die Entscheider sind; erst mit Case den EB aktiv involvieren. Achtung: Zugang nicht zu lange aufschieben — genau hier ist der Deal ins Stocken geraten.
- Next question: "Markus, ist Frau Dr. Kessler tatsächlich die Budget-Entscheiderin für so ein Vorhaben — und wer sonst sitzt mit am Tisch?"

## Decision Criteria
- Findings: Keine artikulierten Entscheidungskriterien. Einziger schwacher, nicht als Kriterium bestätigter Hinweis: Sabines Fokus auf Security/Data-Location.
- Confidence: UNBEKANNT
- Evidence: (keine — es sind keine Entscheidungskriterien artikuliert)
- Gaps: keine definierten Kriterien; unklar, woran Erfolg gemessen wird; kommerzielle/EB-Kriterien fehlen; Sabines Security-Interesse noch nicht zu einem Kriterium verdichtet.
- Trend: ERSTBEWERTUNG
- Recommended action: mehr Stakeholder involvieren und auf Basis der bisherigen Aussagen (v.a. Sabines Security-Fokus) gezielt nachfragen und nett challengen, um die echten Entscheidungskriterien herauszuarbeiten.
- Next question: "Woran würden Sie und Frau Vogt eine Lösung final festmachen — welche Kriterien müssen zwingend erfüllt sein?"

## Decision Process
- Findings: Prozess weitgehend unklar ("neblig"); nur Fragmente — Freigabe läuft "über Markus und die IT" und Kessler "muss absegnen". Kein definierter Ablauf, keine Schritte, kein Timing.
- Confidence: ZU_PRUEFEN
- Evidence: "das laeuft ueber mich und die IT" (nordwind_01); "Frau Dr. Kessler ... muss das eh absegnen ... decision process bleibt neblig" (nordwind_03)
- Gaps: kein definierter Ablauf/Timeline; unklar, wie Freigabe und Budget-Genehmigung wirklich laufen.
- Trend: ERSTBEWERTUNG
- Recommended action: den Freigabeprozess konkret erfragen (Schritte, Beteiligte, Weg der Budget-Freigabe).
- Next question: "Wie läuft bei Ihnen eine Investitionsfreigabe in dieser Größenordnung konkret ab — welche Schritte, wer unterschreibt?"

## Paper Process
- Findings: Kein tatsächlich bekannter Paper Process (keine Procurement-/Legal-/Vertragsschritte beschrieben). Interpretation als schwaches Signal: Sabines gefordertes Security-Audit könnte auf ein formales Vendor-Vetting/Freigabe-Verfahren hindeuten — dem ist nachzugehen.
- Confidence: ZU_PRUEFEN
- Evidence: "will erst nen security audit sehen" (nordwind_04); "Sabine ... will wissen ... security? wo liegen die daten" (nordwind_02)
- Gaps: eigentlicher Beschaffungs-/Legal-/Vertragsweg unbekannt; unklar, ob das Audit Teil eines formalen Prozesses ist.
- Trend: ERSTBEWERTUNG
- Recommended action: dem Security-Audit-Signal nachgehen — erfragen, ob dahinter ein formaler Freigabe-/Beschaffungsprozess steht (und welche Schritte dazugehören).
- Next question: "Ist das Security-Audit Teil eines formalen Freigabeprozesses — welche Schritte gehören sonst noch dazu?"

## Identify Pain
- Findings: Realer, von mehreren Personen genannter Pain — manuelles, langsames, fehleranfälliges Reporting, keine standortübergreifende Transparenz ("fliegen blind"), 8-Tage-Monatsabschluss. Durch mehrere Stimmen gestützt (Markus, Tobias, Sabine).
- Confidence: WAHRSCHEINLICH
- Evidence: "reporting dauert ewig, alles excel, wir fliegen blind" (nordwind_01); "pain klar: manuelle reports, fehleranfaellig, zu langsam" (nordwind_02)
- Gaps: kein Compelling Event / keine quantifizierte Dringlichkeit; Auswirkungen nicht in €/Risiko gefasst; treibender Kontakt (Markus) kühlt ab.
- Trend: ERSTBEWERTUNG
- Recommended action: Pain quantifizieren und ein Compelling Event herausarbeiten (was kostet es, wenn nichts geschieht?), um Dringlichkeit zu erzeugen.
- Next question: "Was ist der konkrete Schaden pro Monat, wenn das Reporting so bleibt — verpasste Entscheidungen, Fehler, Kosten?"

## Champion
- Findings: Markus (Head of Ops) war engagiert und hat intern gepusht, aber ohne Nachweis von Macht/EB-Zugang (nie zu Kessler gebracht) und in Note 04 abkühlend — eher Coach/Fan als validierter Champion; muss verifiziert werden.
- Confidence: ZU_PRUEFEN
- Evidence: "Markus pusht, sagt er will das ins management bringen" (nordwind_03); "Markus selbst klingt deutlich weniger heiss ... kein next step vereinbart" (nordwind_04)
- Gaps: Macht/Einfluss unbewiesen; kein EB-Zugang geliefert; Verlässlichkeit fraglich (abkühlend).
- Trend: ERSTBEWERTUNG
- Recommended action: Markus als Champion testen (bringt er uns zu Kessler?) und parallel einen zweiten Draht aufbauen (Multi-Threading), falls er sich als bloßer Coach erweist.
- Next question: "Markus, würden Sie uns zu Frau Dr. Kessler mitnehmen und das Thema gemeinsam vorstellen?"

## Competition
- Findings: Kein konkurrierender Anbieter erwähnt. Als Hypothese: der eigentliche Wettbewerber ist der Status quo / "keine Entscheidung" (Excel + Trägheit), der aktuell zu gewinnen scheint (Budget weg, Deal stockt) — zu verifizieren.
- Confidence: ZU_PRUEFEN
- Evidence: "budget ist dieses jahr eigentlich nicht da" (nordwind_04); "kein next step vereinbart, Markus: ich meld mich wenn ich mehr weiss" (nordwind_04)
- Gaps: kein benannter Vendor-Wettbewerber; unklar, ob die Inaktion dauerhaft gewinnt oder reaktivierbar ist.
- Trend: ERSTBEWERTUNG
- Recommended action: die "keine Entscheidung"-Konkurrenz aktiv angehen — Dringlichkeit/Compelling Event schaffen; parallel prüfen, ob ein Vendor-Wettbewerber im Hintergrund existiert.
- Next question: "Wenn Sie das Thema jetzt nicht angehen — was ist der Plan B, und was müsste passieren, damit es Priorität bekommt?"

## Gesamt
- Overall score (0–100): 25
- Score rationale: Frühe, dünn qualifizierte Discovery — sechs Dimensionen ZU_PRUEFEN, eine UNBEKANNT, EB nie erreicht, Budget revidiert, Champion fraglich. Einziger Anker ist ein realer, mehrfach genannter Pain (WAHRSCHEINLICH), auf dem man aufbauen könnte. 25 = niedrig, aber nicht null, weil der Pain eine Reaktivierung erlaubt; ohne Dringlichkeit + EB-Zugang jedoch Disqualifikations-Kandidat.
- Momentum (POSITIV / NEUTRAL / NEGATIV): NEGATIV
- Deal risks:
  1. Kein EB-Zugang — Kessler (CFO) nie eingebunden; Deal single-threaded auf Markus.
  2. Budget verschwunden — 150k-Signal revidiert ("dieses Jahr nicht da", evtl. 2027).
  3. Champion fraglich — Markus eher Coach/Fan, kühlt ab, kein next step.
  4. Kein Compelling Event / keine Dringlichkeit — Status quo (Inaktion) gewinnt.
  5. Discovery zu dünn — Kriterien/Prozess unklar, IT (Sabine) skeptisch/neutral.
- Next best questions (max 5, priorisiert):
  1. "Markus, ist Frau Dr. Kessler die Budget-Entscheiderin — bringen Sie uns zu ihr?"
  2. "Was kostet das manuelle Reporting pro Monat konkret (Personentage, Fehler)?"
  3. "Was müsste passieren, damit das Thema dieses Jahr Priorität + Budget bekommt?"
  4. "Woran würden Sie und Frau Vogt eine Lösung final festmachen?"
  5. "Wie läuft eine Investitionsfreigabe dieser Größe bei Ihnen konkret ab?"
- Summary for manager (3 Saetze, forecast-tauglich): Frühe Discovery, seit Monaten nicht über einen enthusiastischen, aber machtlosen Ops-Kontakt (Markus) hinausgekommen; der eigentliche EB (CFO Kessler) wurde nie eingebunden. Das Budget-Signal (150k) ist revidiert, es gibt kein Compelling Event, und der Kontakt kühlt ab — der Status quo gewinnt. Forecast: dieses Jahr unwahrscheinlich; es gibt reale Pains als Anker, aber ohne erzwungene Dringlichkeit + EB-Zugang gehört der Deal zurückgestellt (2027) oder disqualifiziert.
