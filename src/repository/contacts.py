"""Repository: Contacts + Alignment-Historie + Kontakt-Entity-Resolution.

CLAUDE.md (bindend): Alignment-Aenderungen NIE still ueberschreiben — jede
Aenderung erzeugt einen append-only ContactHistory-Eintrag (alt -> neu,
Quelle, Zeitpunkt). Erwaehnte Personen werden erst gegen bestehende Kontakte
des Accounts gematcht (find_contact_candidates), bevor ein neuer angelegt
wird — sonst Dubletten.
"""
from __future__ import annotations

from difflib import SequenceMatcher

from src.domain.contact import Contact
from src.domain.contact_history import ContactHistoryEntry
from src.repository import db

# Nur diese Felder duerfen ueber update_contact_alignment geaendert werden.
ALIGNMENT_FIELDS = frozenset(
    {"role_in_deal", "influence", "disposition", "relationship_strength", "last_touchpoint", "notes"}
)


def _from_row(row) -> Contact:
    return Contact(**dict(row))


def save_contact(contact: Contact) -> Contact:
    with db.connect() as conn:
        conn.execute(
            """INSERT INTO contacts (id, account_id, name, title, email, phone, linkedin_url,
               role_in_deal, influence, disposition, relationship_strength, last_touchpoint, notes)
               VALUES (:id, :account_id, :name, :title, :email, :phone, :linkedin_url,
               :role_in_deal, :influence, :disposition, :relationship_strength, :last_touchpoint, :notes)""",
            contact.model_dump(mode="json"),
        )
    return contact


def get_contact(contact_id: str) -> Contact:
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,)).fetchone()
    if row is None:
        raise LookupError(f"Kontakt nicht gefunden: {contact_id}")
    return _from_row(row)


def list_all_contacts() -> list[Contact]:
    """Alle Kontakte (CSV-Export, P7)."""
    with db.connect() as conn:
        rows = conn.execute("SELECT * FROM contacts ORDER BY account_id, name").fetchall()
    return [_from_row(r) for r in rows]


def list_contacts(account_id: str) -> list[Contact]:
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT * FROM contacts WHERE account_id = ? ORDER BY name", (account_id,)
        ).fetchall()
    return [_from_row(r) for r in rows]


def find_contact_candidates(account_id: str, name: str) -> list[tuple[Contact, float]]:
    """Kontakt-Resolution: aehnliche bestehende Kontakte des Accounts (Dubletten-Schutz).

    Score: 1.0 bei exaktem Namen (case-insensitiv), sonst max(Token-Jaccard,
    difflib-Ratio). Zusatzregel (P6-Beobachtung): ein Einzel-Token-Name
    ("Markus"), der im Account-Kontext GENAU EINEN Kontakt per Namens-Token
    trifft, ist eindeutig -> 0.85 (automatische Zuordnung statt Nachfrage);
    treffen mehrere, bleibt es im Nachfrage-Band. Kandidaten ab 0.3,
    absteigend sortiert; die Schwelle wendet der Orchestrator an (P6).
    """
    needle = name.strip().lower()
    needle_tokens = set(needle.split())
    contacts = list_contacts(account_id)

    results: list[tuple[Contact, float]] = []
    for contact in contacts:
        existing = contact.name.strip().lower()
        if existing == needle:
            score = 1.0
        else:
            tokens = set(existing.split())
            jaccard = len(needle_tokens & tokens) / len(needle_tokens | tokens) if tokens else 0.0
            ratio = SequenceMatcher(None, needle, existing).ratio()
            score = max(jaccard, ratio)
        if score >= 0.3:
            results.append((contact, round(score, 3)))

    # Vorname-Eindeutigkeit: genau EIN Kontakt traegt das Token -> sichere Zuordnung
    if len(needle_tokens) == 1:
        token = next(iter(needle_tokens))
        token_hits = [c for c in contacts if token in c.name.strip().lower().split()]
        if len(token_hits) == 1:
            hit = token_hits[0]
            results = [(c, max(s, 0.85) if c.id == hit.id else s) for c, s in results]
            if all(c.id != hit.id for c, _ in results):
                results.append((hit, 0.85))

    return sorted(results, key=lambda t: -t[1])


def update_contact_alignment(contact_id: str, changes: dict, source: str) -> Contact:
    """Aendert Alignment-Felder und protokolliert JEDE Aenderung in contact_history."""
    unknown = set(changes) - ALIGNMENT_FIELDS
    if unknown:
        raise ValueError(f"Keine Alignment-Felder: {sorted(unknown)} (erlaubt: {sorted(ALIGNMENT_FIELDS)})")

    contact = get_contact(contact_id)
    updated = contact.model_copy(update=changes)
    Contact.model_validate(updated.model_dump())  # Literals/Typen hart validieren

    entries: list[ContactHistoryEntry] = []
    for field, new_value in changes.items():
        old_value = getattr(contact, field)
        if old_value == new_value:
            continue
        entries.append(
            ContactHistoryEntry(
                contact_id=contact_id, field=field,
                old_value=str(old_value), new_value=str(new_value), source=source,
            )
        )
    if not entries:
        return contact  # nichts geaendert, nichts protokolliert

    with db.connect() as conn:
        row = updated.model_dump(mode="json")
        conn.execute(
            """UPDATE contacts SET role_in_deal=:role_in_deal, influence=:influence,
               disposition=:disposition, relationship_strength=:relationship_strength,
               last_touchpoint=:last_touchpoint, notes=:notes WHERE id=:id""",
            row,
        )
        for e in entries:
            conn.execute(
                """INSERT INTO contact_history (id, contact_id, field, old_value, new_value, source, ts)
                   VALUES (:id, :contact_id, :field, :old_value, :new_value, :source, :ts)""",
                e.model_dump(mode="json"),
            )
    return updated


def get_contact_history(contact_id: str) -> list[ContactHistoryEntry]:
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT * FROM contact_history WHERE contact_id = ? ORDER BY ts", (contact_id,)
        ).fetchall()
    return [ContactHistoryEntry(**dict(r)) for r in rows]
