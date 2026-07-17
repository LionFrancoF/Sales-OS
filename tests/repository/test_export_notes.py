"""export-notes: Roh-Notes eines echten Deals chronologisch in die
Privat-Ablage schreiben (Golden-Set aus echten Deals, Entscheidung 17.07.2026).
Testet die innere Funktion mit tmp-Zielordner — bewusst NICHT den echten
tests/sample_notes/private/-Ordner (Lehre aus der Glob-Kollision des
--golden-E2E-Tests mit Demo-Artefakten am 16.07.)."""
from __future__ import annotations

from datetime import datetime, timezone

from src.cli import _export_notes
from src.domain.account import Account
from src.domain.activity import Activity
from src.domain.deal import Deal
from src.repository.accounts import save_account
from src.repository.activities import save_activity
from src.repository.deals import save_deal


def _dt(day: int) -> datetime:
    return datetime(2026, 7, day, 12, 0, tzinfo=timezone.utc)


def test_export_notes_writes_chronological_slug_files(tmp_path):
    account = save_account(Account(name="Echt Kunde AG"))
    deal = save_deal(Deal(account_id=account.id, name="Data Platform", stage="DISCOVERY"))
    # absichtlich in falscher Reihenfolge gespeichert — Export muss chronologisch sortieren
    save_activity(Activity(deal_id=deal.id, type="CALL", occurred_at=_dt(10), raw_text="call zwei"))
    save_activity(Activity(deal_id=deal.id, type="CALL", occurred_at=_dt(3), raw_text="call eins"))

    written = _export_notes(deal, tmp_path / "private")

    assert [p.name for p in written] == ["data_platform_01.txt", "data_platform_02.txt"]
    assert (tmp_path / "private" / "data_platform_01.txt").read_text(encoding="utf-8") == "call eins"
    assert (tmp_path / "private" / "data_platform_02.txt").read_text(encoding="utf-8") == "call zwei"


def test_export_notes_empty_deal_returns_nothing(tmp_path):
    account = save_account(Account(name="Leer GmbH"))
    deal = save_deal(Deal(account_id=account.id, name="Leerer Deal", stage="PROSPECT"))

    assert _export_notes(deal, tmp_path / "private") == []
    assert not (tmp_path / "private").exists()
