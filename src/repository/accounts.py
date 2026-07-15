"""Repository: Accounts (mutabler Zustand)."""
from __future__ import annotations

from src.domain.account import Account
from src.repository import db
from src.repository._serde import dump_json, load_json


def _to_row(a: Account) -> dict:
    d = a.model_dump(mode="json")
    d["research_profile"] = dump_json(d["research_profile"]) if d["research_profile"] is not None else None
    return d


def _from_row(row) -> Account:
    d = dict(row)
    d["research_profile"] = load_json(d["research_profile"], None)
    return Account(**d)


def save_account(account: Account) -> Account:
    with db.connect() as conn:
        conn.execute(
            """INSERT INTO accounts (id, name, domain, industry, size_estimate,
               research_profile, created_at, updated_at)
               VALUES (:id, :name, :domain, :industry, :size_estimate,
               :research_profile, :created_at, :updated_at)""",
            _to_row(account),
        )
    return account


def get_account(account_id: str) -> Account:
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
    if row is None:
        raise LookupError(f"Account nicht gefunden: {account_id}")
    return _from_row(row)


def get_account_by_name(name: str) -> Account:
    with db.connect() as conn:
        row = conn.execute(
            "SELECT * FROM accounts WHERE lower(name) = lower(?)", (name,)
        ).fetchone()
    if row is None:
        raise LookupError(f"Account nicht gefunden: '{name}'")
    return _from_row(row)


def list_accounts() -> list[Account]:
    with db.connect() as conn:
        rows = conn.execute("SELECT * FROM accounts ORDER BY name").fetchall()
    return [_from_row(r) for r in rows]
