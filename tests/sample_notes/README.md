# Sample Notes — synthetische Testdaten (P2 + Golden-Set-Ausbau)

Sechs fiktive Enterprise-B2B-Accounts, je ein Deal, je 3–5 chronologische Call-Notes
als eigene `.txt`. Verkauftes Produkt durchgehend: **"Vela"** (AI-native Daten-/
Automations-Plattform). Die Notes sind **absichtlich messy** (Stichpunkte, Denglisch,
Abkürzungen, Tippfehler, Smalltalk, interne Randnotizen in `[intern: …]`).

**Wichtig:** Stakeholder-Rollen (Economic Buyer, Champion, Blocker …) sind nie gelabelt —
sie sollen aus dem Verhalten *ableitbar* sein. Diese Übersicht beschreibt nur die
**Szenario-Anlage** (Reifegrad + eingebaute Dynamik), keine MEDDPICC-Bewertung.

## Die Verläufe

### A — Nordwind Logistics (Logistik/Kontraktlogistik) · `nordwind_01…04`
Frühe **Discovery mit vielen Lücken**. Kontakt über einen enthusiastischen Ops-Leiter,
aber der eigentliche Entscheider (CFO, "Dr. Kessler") wird nie erreicht; IT ist skeptisch.
**Eingebauter Widerspruch:** In Call 2 signalisiert der Ops-Leiter ~150k Budget — in Call 4
ist das Budget "dieses Jahr eigentlich nicht da" (revidiert). Zusätzlich **kühlt der
Haupttreiber ab** (schwer erreichbar, kein Next Step). Viel UNBEKANNT-Material, single-threaded.

### B — Aurelia Bank AG (Financial Services, stark reguliert) · `aurelia_01…05`
**Weit fortgeschritten, inkl. Paper Process.** Starke Treiberin (VP Data), früher klarer
Economic Buyer (CIO), quantifizierter Pain (Reporting 5 Tage → 1 Tag), explizite Decision
Criteria (Data Residency, BaFin-Audit-Logs, SSO, SLA). Ab Call 3 dominiert der **Paper
Process** (Einkauf 8–12 Wochen, Legal-Redlines, DPA, Security-Fragebogen).
**Eingebaute Widersprüche:** (1) die Treiberin wird ab Call 4 in ein anderes Programm
abgezogen — **Champion wechselt Rolle**, eine neue Person (Miriam Voss) übernimmt; (2) das
in Call 1 "genehmigte" 400k-Budget wird ab Call 4 vom Einkauf gedrückt (~320–355k). Spät-Stage.

### C — Meridian MedTech (Medizintechnik, MDR-reguliert) · `meridian_01…05`
**Mittendrin, mit stillem Champion und aktivem Wettbewerber.** Die Direktorin Digital ist
im 1:1 begeistert, aber **auffällig leise in größeren Runden** (stiller Champion); der
IT-Chef ist reserviert und favorisiert den Wettbewerber **"Fluxion"**.
**Eingebaute Dynamik/Widersprüche:** Fluxion entwickelt sich von "nebensächlich" (Call 2)
über "aktives POC-Angebot" (Call 3) zu "**POC bereits gestartet**" (Call 5); die Championin
sagt in Call 2/3 "voll an Bord, Q3 live", ist aber in Call 5 **seit ~3 Wochen abgetaucht**
(Rolle nach Umstrukturierung unklar). EB (CFO) engagiert, aber abwartend. Single-threading-Risiko.

### D — Hanseatik Retail Group (Omnichannel-Einzelhandel) · `hanseatik_01…03` *(Golden-Set-Ausbau, Momentum-Stressfall)*
**Solide Mid-Stage-Discovery, die zuletzt auf der Stelle tritt.** Strukturierte
BI-Leiterin treibt (Frauke Petersen), IT (Jan Okonkwo) kritisch-konstruktiv, klarer Pain
(Aktionsauswertung 10–14 Tage, Flop-Aktionen 80–120k Marge). **Eingebaute Dynamik:** Die
letzte Note ist positiv im Ton und bringt neue Anekdoten — aber der COO-Termin (Bettina
Clasen) bleibt angekündigt statt erfolgt, kein neuer Termin fixiert, keine Dimension
bewegt sich. Anlage: *Veränderung der Beleglage = keine.*

### E — Voltara Energie AG (Energieversorger, reguliert) · `voltara_01…04` *(Golden-Set-Ausbau, Momentum-Stressfall)*
**Später Mid-Stage mit Doppelereignis in der letzten Note.** Starker Treiber
(Dr. Brandt, Leiter Netzwirtschaft), CFO (Riegler) direkt gesprochen mit bedingter
mündlicher Zusage (Security-Freigabe + Business Case → Beschaffung Q3), formaler
Security-Review (CIO-Office Diehm), Wettbewerber PowerGrid als Pflichtübung.
**Eingebauter Konflikt:** In `voltara_04` fallen ZWEI harte Ereignisse in dieselbe Note —
die schriftliche Security-Freigabe (Bedingung des EB erfüllt) UND die Kündigung des
Treibers (weg zum 01.09., Nachfolge offen). Anlage: *harte Belege in beide Richtungen
gleichzeitig.*

### F — Papyrus Verlagsgruppe (Medien/Verlag) · `papyrus_01…03` *(Golden-Set-Ausbau, Momentum-Stressfall)*
**Frühe Stage, maximale Begeisterung, null Substanz.** Enthusiastischer Digital
Director (Leon Bachmann), Team applaudiert in der Demo, GF (Sartorius) nur vom
Hörensagen („fand die Idee im Flur auch spannend"). **Eingebaute Falle:** Die letzte
Note ist die euphorischste — und enthält keine einzige Buyer-Aktion, keine Zahl, kein
Dokument, keinen Termin, keinen zweiten Stakeholder. Anlage: *Tonalität vs. Beleglage.*

## Dateien
- Notes: `nordwind_01…04.txt`, `aurelia_01…05.txt`, `meridian_01…05.txt`,
  `hanseatik_01…03.txt`, `voltara_01…04.txt`, `papyrus_01…03.txt` (24 Dateien).
- Golden-Set-Referenzen (ausgefüllt) in `tests/golden_set/`:
  `nordwind_04.expected.md`, `aurelia_05.expected.md`, `meridian_05.expected.md`
  (je die letzte, informationsreichste Note pro Account; Framework MEDDPICC erzwungen).
- Golden-Set-Vorlagen (leer, von Hand auszufüllen) in `tests/golden_set/drafts/`:
  `hanseatik_03.expected.md`, `voltara_04.expected.md`, `papyrus_03.expected.md` —
  **nach dem Ausfüllen nach `tests/golden_set/` verschieben** (unausgefüllte Dateien
  würden dort pytest/eval brechen, deshalb der Unterordner).
