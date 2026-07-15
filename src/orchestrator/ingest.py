"""Ingestion-Orchestrierung: process_note() — der eine reale Eingang (Befund 1.5:
bewusst KEIN Trigger-Envelope; generalisiert wird, wenn ein zweiter Trigger real ist).

Ablauf: Dedup -> Klassifizieren (Haiku) -> Deal aufloesen -> Activity zuerst
persistieren (append-only) -> Routen (Analyzer/Kontakte/Next-Steps).

Robustheit statt Transaktionsklammer (Befunde 2.4 + 2.6 in einem Mechanismus):
- Die Activity ist der WIEDERAUFSETZPUNKT: existiert ihr Hash bereits, wird
  geprueft, ob die Verarbeitung komplett war (Snapshot referenziert die
  Activity). Komplett -> Abbruch "bereits verarbeitet am <datum>". Unvollstaendig
  (z.B. Crash nach Activity-Save) -> Fortsetzung mit der bestehenden Activity.
- Je Activity entsteht maximal EIN Snapshot (kein Re-Analyse-Rauschen im Trend).

Kein Event-Log (Befund 1.2, Entscheidung Lion) — jeder Schritt schreibt eine
Log-Zeile und landet im IngestReport.
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field

from src.domain.activity import Activity
from src.domain.contact import Contact
from src.domain.deal import Deal
from src.orchestrator.classifier import Classification, ClassifiedContact, classify
from src.orchestrator.resolver import AskFn, resolve_deal
from src.repository.activities import get_activity_by_hash, save_activity
from src.repository.contacts import find_contact_candidates, save_contact, update_contact_alignment
from src.repository.snapshots import get_latest_snapshot, list_snapshots, save_snapshot

log = logging.getLogger("sales_os.orchestrator")

_CONTACT_AUTO_THRESHOLD = 0.8  # analog zur Deal-Resolution (CLAUDE.md-Datenmodell)
_CONTACT_ASK_THRESHOLD = 0.5   # darunter: eindeutig neu


@dataclass
class IngestReport:
    """Zusammenfassung eines Ingest-Laufs (die CLI rendert daraus das Terminal-Bild)."""

    deal_name: str = ""
    confidence: float = 0.0
    method: str = ""                      # --deal | auto | nachgefragt | wiederaufnahme
    activity_id: str = ""
    activity_type: str = ""
    signals: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)      # was ausgefuehrt wurde
    changes: list[str] = field(default_factory=list)      # Diff-artig: was sich geaendert hat
    aborted: str | None = None                            # gesetzt bei Dedup-Abbruch


def _normalized_hash(text: str) -> str:
    """SHA-256 ueber normalisierten Roh-Text (Whitespace-Raender; bekannte Grenze:
    faengt nur identische Notes — bewusst akzeptiert fuer v1, CLAUDE.md)."""
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


def _snapshot_exists_for(activity_id: str, deal_id: str) -> bool:
    return any(activity_id in s.source_activity_ids for s in list_snapshots(deal_id))


def process_note(
    text: str,
    deal_name: str | None = None,
    source: str = "",
    ask: AskFn | None = None,
) -> IngestReport:
    """Verarbeitet eine rohe Notiz komplett. Wirft ValueError bei unklarer Zuordnung."""
    if not text.strip():
        raise ValueError("Leerer Text — nichts zu verarbeiten.")
    report = IngestReport()

    # --- 1) Dedup / Wiederaufsetzpunkt (vor jedem LLM-Call, kostet nichts) ---
    text_hash = _normalized_hash(text)
    existing: Activity | None = None
    try:
        existing = get_activity_by_hash(text_hash)
    except LookupError:
        pass
    if existing is not None:
        if _snapshot_exists_for(existing.id, existing.deal_id):
            report.aborted = (
                f"Bereits verarbeitet am {existing.occurred_at:%Y-%m-%d %H:%M} "
                f"(Activity {existing.id[:8]}…). Abbruch ohne Nebenwirkungen."
            )
            log.info("dedup: %s", report.aborted)
            return report
        log.warning("dedup: Activity %s existiert ohne Snapshot — setze Verarbeitung fort.", existing.id[:8])
        report.method = "wiederaufnahme"

    # --- 2) Klassifizieren (ein Haiku-Call: Typ + Signale + Extraktion) ---
    classification = classify(text)
    report.activity_type = classification.activity_type
    report.signals = [name for name, on in classification.signals.model_dump().items() if on]
    log.info("classifier: type=%s signale=%s", classification.activity_type, ",".join(report.signals) or "-")

    # --- 3) Deal aufloesen (NIE raten) ---
    if existing is not None:
        from src.repository.deals import get_deal
        deal = get_deal(existing.deal_id)
        confidence = 1.0
    else:
        deal, confidence, report.method = resolve_deal(text, deal_name, ask)
    report.deal_name = deal.name
    report.confidence = confidence

    # --- 4) Activity ZUERST persistieren (append-only; Beleg-Kette) ---
    if existing is None:
        summary = classification.summary
        if classification.next_steps:
            summary += " | Next Steps: " + "; ".join(classification.next_steps)
        activity = save_activity(Activity(
            deal_id=deal.id,
            type=classification.activity_type,
            raw_text=text,
            raw_text_hash=text_hash,
            summary=summary,
            source=source,
        ))
        report.actions.append(f"Activity gespeichert ({classification.activity_type}, append-only)")
        log.info("activity: %s gespeichert (deal=%s)", activity.id[:8], deal.name)
    else:
        activity = existing
        report.actions.append("Bestehende Activity wiederverwendet (Wiederaufnahme)")

    # --- 5) Routen ---
    signals = classification.signals
    if signals.meddpicc_relevant:
        _route_meddpicc(text, deal, activity, report)
    if signals.neue_kontakte or signals.stakeholder_update:
        _route_contacts(classification, deal, activity, report, ask)
    if signals.next_steps or signals.termin_zusage:
        report.actions.append(
            "Next Steps/Termin als Activity-Metadaten festgehalten (Follow-up-Agent: Backlog)"
        )
        log.info("router: next_steps/termin in Activity-Summary festgehalten")
    if not any([signals.meddpicc_relevant, signals.neue_kontakte, signals.stakeholder_update,
                signals.next_steps, signals.termin_zusage]):
        report.actions.append("Keine Routing-Signale — nur Activity abgelegt")
    return report


def _route_meddpicc(text: str, deal: Deal, activity: Activity, report: IngestReport) -> None:
    """MEDDPICC-Agent mit Vorgaenger-Snapshot; max. ein Snapshot je Activity (Befund 2.6)."""
    from src.agents.meddpicc.agent import analyze  # lazy: schwere Deps nur bei Bedarf

    if _snapshot_exists_for(activity.id, deal.id):
        report.actions.append("Analyse uebersprungen — Snapshot fuer diese Note existiert bereits (Befund 2.6)")
        log.info("router: snapshot fuer activity %s existiert — skip", activity.id[:8])
        return
    previous = get_latest_snapshot(deal.id)
    snapshot = analyze(text, previous_snapshot=previous, deal=deal, source_activity_ids=[activity.id])
    save_snapshot(snapshot)
    report.actions.append(
        f"MEDDPICC-Snapshot gespeichert (Score {snapshot.overall_score}, {snapshot.momentum}"
        + (", Erstbewertung)" if previous is None else ")")
    )
    log.info("router: snapshot %s gespeichert (score=%d)", snapshot.id[:8], snapshot.overall_score)

    if previous is not None:
        for key, dim in snapshot.dimensions.items():
            old = previous.dimensions.get(key)
            if old and old.confidence != dim.confidence:
                report.changes.append(f"{key}: {old.confidence} → {dim.confidence}")
        report.changes.append(f"score: {previous.overall_score} → {snapshot.overall_score}")
        if previous.momentum != snapshot.momentum:
            report.changes.append(f"momentum: {previous.momentum} → {snapshot.momentum}")


def _route_contacts(
    classification: Classification, deal: Deal, activity: Activity,
    report: IngestReport, ask: AskFn | None,
) -> None:
    """Kontakte: erst Resolution gegen Bestand (Dubletten!), dann anlegen/aktualisieren."""
    source_ref = f"ingest:{activity.id[:8]}"
    for person in classification.contacts:
        candidates = find_contact_candidates(deal.account_id, person.name)
        best_score = candidates[0][1] if candidates else 0.0

        if best_score >= _CONTACT_AUTO_THRESHOLD:
            _update_existing(candidates[0][0], person, source_ref, report)
        elif best_score >= _CONTACT_ASK_THRESHOLD:
            options = [f"Bestehenden Kontakt '{candidates[0][0].name}' aktualisieren ({best_score:.2f})",
                       f"'{person.name}' als NEUEN Kontakt anlegen", "Ueberspringen"]
            choice = ask(f"Person '{person.name}' aehnelt einem bestehenden Kontakt:", options) if ask else None
            if choice == 0:
                _update_existing(candidates[0][0], person, source_ref, report)
            elif choice == 1:
                _create_contact(person, deal, report)
            else:
                report.actions.append(f"Kontakt '{person.name}' uebersprungen (Zuordnung unklar)")
                log.info("router: kontakt '%s' uebersprungen", person.name)
        else:
            _create_contact(person, deal, report)


def _evidenced_alignment(person: ClassifiedContact) -> dict:
    """Nur belegbare Felder (konservativ) — Rest bleibt UNKLAR/UNBEKANNT."""
    changes = {}
    if person.role_in_deal:
        changes["role_in_deal"] = person.role_in_deal
    if person.influence:
        changes["influence"] = person.influence
    if person.disposition:
        changes["disposition"] = person.disposition
    return changes


def _update_existing(contact: Contact, person: ClassifiedContact, source_ref: str, report: IngestReport) -> None:
    changes = _evidenced_alignment(person)
    if not changes:
        report.actions.append(f"Kontakt '{contact.name}' erkannt — keine neuen belegbaren Alignment-Infos")
        return
    updated = update_contact_alignment(contact.id, changes, source=source_ref)
    diff = ", ".join(f"{k}={v}" for k, v in changes.items())
    report.actions.append(f"Kontakt '{updated.name}' aktualisiert ({diff}) — Historie protokolliert")
    log.info("router: kontakt '%s' aktualisiert: %s", updated.name, diff)


def _create_contact(person: ClassifiedContact, deal: Deal, report: IngestReport) -> None:
    contact = save_contact(Contact(
        account_id=deal.account_id,
        name=person.name,
        title=person.title,
        **_evidenced_alignment(person),  # Rest: Domain-Defaults (UNKLAR/UNBEKANNT)
    ))
    report.actions.append(f"Neuer Kontakt angelegt: {contact.name} ({contact.role_in_deal})")
    log.info("router: neuer kontakt '%s' (%s)", contact.name, contact.role_in_deal)
