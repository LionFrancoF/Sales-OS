"""Repository: Deals + Deal-Entity-Resolution (Grundlage fuer P6)."""
from __future__ import annotations

import re

from src.domain.deal import Deal
from src.repository import db
from src.repository.contacts import list_contacts

# Woerter, die fuer das Namens-Matching zu generisch sind.
_STOPWORDS = {"der", "die", "das", "und", "mit", "for", "the", "and", "gmbh", "ag", "inc"}


def save_deal(deal: Deal) -> Deal:
    with db.connect() as conn:
        conn.execute(
            """INSERT INTO deals (id, account_id, name, stage, win_probability,
               amount_estimate, expected_close, framework_override, created_at, updated_at)
               VALUES (:id, :account_id, :name, :stage, :win_probability,
               :amount_estimate, :expected_close, :framework_override, :created_at, :updated_at)""",
            deal.model_dump(mode="json"),
        )
    return deal


def get_deal(deal_id: str) -> Deal:
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM deals WHERE id = ?", (deal_id,)).fetchone()
    if row is None:
        raise LookupError(f"Deal nicht gefunden: {deal_id}")
    return Deal(**dict(row))


def get_deal_by_name(name: str) -> Deal:
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM deals WHERE lower(name) = lower(?)", (name,)).fetchone()
    if row is None:
        raise LookupError(f"Deal nicht gefunden: '{name}'")
    return Deal(**dict(row))


def list_deals() -> list[Deal]:
    with db.connect() as conn:
        rows = conn.execute("SELECT * FROM deals ORDER BY updated_at DESC").fetchall()
    return [Deal(**dict(r)) for r in rows]


def _tokens(name: str) -> list[str]:
    return [t for t in re.findall(r"\w+", name.lower()) if len(t) > 3 and t not in _STOPWORDS]


def _contains_word(text_lower: str, word: str) -> bool:
    return re.search(rf"\b{re.escape(word)}\b", text_lower) is not None


def find_deal_candidates(text: str) -> list[tuple[Deal, float]]:
    """Deal-Entity-Resolution: welche Deals passen zu einem rohen Notes-Text?

    Signale (kumulativ, cap 1.0):
    - Account-Name im Text: +0.5 (staerkster Anker)
    - Deal-Namens-Tokens im Text: bis +0.4 (anteilig)
    - bekannte Kontaktnamen des Accounts im Text: +0.15 je Treffer, max +0.3
    Die Schwelle (RESOLUTION_THRESHOLD) wendet der Orchestrator an — unter
    ihr wird nachgefragt statt geraten (CLAUDE.md, bindend).
    """
    from src.repository.accounts import get_account  # lokal: Zyklusvermeidung

    text_lower = text.lower()
    results: list[tuple[Deal, float]] = []
    for deal in list_deals():
        score = 0.0
        account = get_account(deal.account_id)
        if any(_contains_word(text_lower, t) for t in _tokens(account.name)):
            score += 0.5
        deal_tokens = _tokens(deal.name)
        if deal_tokens:
            hit_ratio = sum(_contains_word(text_lower, t) for t in deal_tokens) / len(deal_tokens)
            score += 0.4 * hit_ratio
        contact_hits = 0
        for contact in list_contacts(deal.account_id):
            name_tokens = [t for t in re.findall(r"\w+", contact.name.lower()) if len(t) > 2]
            if any(_contains_word(text_lower, t) for t in name_tokens):
                contact_hits += 1
        score += min(contact_hits * 0.15, 0.3)
        if score > 0:
            results.append((deal, round(min(score, 1.0), 3)))
    return sorted(results, key=lambda t: -t[1])
