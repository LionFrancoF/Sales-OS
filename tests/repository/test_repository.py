"""Tests der Repository-Schicht: CRUD-Roundtrips, Resolution, Historie, Append-only."""
from __future__ import annotations

import pytest

from src.domain.account import Account
from src.domain.activity import Activity
from src.domain.contact import Contact
from src.domain.correction import Correction
from src.domain.deal import Deal
from src.domain.meddpicc import DimensionAssessment, MeddpiccSnapshot
from src.repository.accounts import get_account, get_account_by_name, list_accounts, save_account
from src.repository.activities import get_activity_by_hash, list_activities, save_activity
from src.repository.contacts import (
    find_contact_candidates,
    get_contact,
    get_contact_history,
    save_contact,
    update_contact_alignment,
)
from src.repository.corrections import get_corrections, save_correction
from src.repository.deals import find_deal_candidates, get_deal_by_name, list_deals, save_deal
from src.repository.snapshots import get_latest_snapshot, list_snapshots, save_snapshot


def _setup_account(name="Nordwind Logistics") -> Account:
    return save_account(Account(name=name, domain="nordwind.example", industry="Logistik"))


def _setup_deal(account: Account, name="Ops-Analytics Rollout") -> Deal:
    return save_deal(Deal(account_id=account.id, name=name, stage="DISCOVERY"))


# ------------------------------------------------------------ Roundtrips

def test_account_roundtrip():
    a = _setup_account()
    assert get_account(a.id) == a
    assert get_account_by_name("nordwind logistics") == a  # case-insensitiv
    assert list_accounts() == [a]


def test_account_not_found_raises_lookup():
    with pytest.raises(LookupError):
        get_account_by_name("gibt es nicht")


def test_deal_roundtrip_preserves_win_probability():
    a = _setup_account()
    d = _setup_deal(a)
    loaded = get_deal_by_name("Ops-Analytics Rollout")
    assert loaded == d
    assert loaded.win_probability == 20  # DISCOVERY-Default aus STAGE_GATES
    assert list_deals() == [d]


def test_contact_roundtrip_with_alignment():
    a = _setup_account()
    c = save_contact(Contact(account_id=a.id, name="Markus Reinhardt", title="Head of Ops",
                             role_in_deal="COACH", influence="MITTEL"))
    assert get_contact(c.id) == c


def test_snapshot_roundtrip_with_nested_dimensions():
    a = _setup_account()
    d = _setup_deal(a)
    snap = MeddpiccSnapshot(
        deal_id=d.id, overall_score=42, momentum="NEGATIV",
        dimensions={"champion": DimensionAssessment(findings="Fan, kein Champion", confidence="ZU_PRUEFEN",
                                                    evidence=["Markus pusht"], gaps=["EB-Zugang"])},
        deal_risks=["Single-Thread"], next_best_questions=["Wer entscheidet?"],
        prompt_version="abc123",
    )
    save_snapshot(snap)
    loaded = get_latest_snapshot(d.id)
    assert loaded == snap
    assert loaded.dimensions["champion"].evidence == ["Markus pusht"]


def test_get_latest_snapshot_orders_by_created_at():
    from datetime import datetime, timezone

    a = _setup_account()
    d = _setup_deal(a)
    old = MeddpiccSnapshot(deal_id=d.id, overall_score=10,
                           created_at=datetime(2026, 1, 1, tzinfo=timezone.utc))
    new = MeddpiccSnapshot(deal_id=d.id, overall_score=60,
                           created_at=datetime(2026, 7, 1, tzinfo=timezone.utc))
    save_snapshot(old)
    save_snapshot(new)
    assert get_latest_snapshot(d.id).overall_score == 60
    assert [s.overall_score for s in list_snapshots(d.id)] == [10, 60]
    assert get_latest_snapshot("unbekannt") is None


def test_activity_dedup_via_unique_hash():
    a = _setup_account()
    d = _setup_deal(a)
    act = Activity(deal_id=d.id, type="CALL", raw_text="gleicher text")
    save_activity(act)
    duplicate = Activity(deal_id=d.id, type="NOTE", raw_text="gleicher text")  # gleicher Hash
    with pytest.raises(ValueError, match="Bereits verarbeitet"):
        save_activity(duplicate)
    assert get_activity_by_hash(act.raw_text_hash).id == act.id
    assert len(list_activities(d.id)) == 1


def test_correction_roundtrip_and_agent_filter():
    a = _setup_account()
    d = _setup_deal(a)
    save_correction(Correction(deal_id=d.id, agent="meddpicc_analyzer",
                               field_path="dimensions.champion.confidence",
                               original_value="WAHRSCHEINLICH", corrected_value="ZU_PRUEFEN"))
    save_correction(Correction(deal_id=d.id, agent="anderer_agent", field_path="x",
                               original_value="a", corrected_value="b"))
    assert len(get_corrections(d.id)) == 2
    only = get_corrections(d.id, agent="meddpicc_analyzer")
    assert len(only) == 1 and only[0].corrected_value == "ZU_PRUEFEN"


# ------------------------------------------------------------ Alignment-Historie

def test_update_contact_alignment_writes_history():
    a = _setup_account()
    c = save_contact(Contact(account_id=a.id, name="Julia Sanders", role_in_deal="CHAMPION"))
    updated = update_contact_alignment(
        c.id, {"role_in_deal": "COACH", "disposition": "NEUTRAL"}, source="note meridian_05"
    )
    assert updated.role_in_deal == "COACH"
    history = get_contact_history(c.id)
    assert len(history) == 2
    role_entry = next(h for h in history if h.field == "role_in_deal")
    assert (role_entry.old_value, role_entry.new_value) == ("CHAMPION", "COACH")
    assert role_entry.source == "note meridian_05"


def test_update_contact_alignment_noop_writes_nothing():
    a = _setup_account()
    c = save_contact(Contact(account_id=a.id, name="X", influence="HOCH"))
    update_contact_alignment(c.id, {"influence": "HOCH"}, source="s")
    assert get_contact_history(c.id) == []


def test_update_contact_alignment_rejects_non_alignment_fields():
    a = _setup_account()
    c = save_contact(Contact(account_id=a.id, name="X"))
    with pytest.raises(ValueError, match="Keine Alignment-Felder"):
        update_contact_alignment(c.id, {"name": "Y"}, source="s")


def test_update_contact_alignment_rejects_invalid_literal():
    a = _setup_account()
    c = save_contact(Contact(account_id=a.id, name="X"))
    with pytest.raises(Exception):
        update_contact_alignment(c.id, {"influence": "MEGA"}, source="s")


# ------------------------------------------------------------ Entity-Resolution

def test_find_deal_candidates_scores_by_signals():
    nordwind = _setup_account("Nordwind Logistics")
    aurelia = save_account(Account(name="Aurelia Bank"))
    d1 = _setup_deal(nordwind, "Ops-Analytics Rollout")
    d2 = save_deal(Deal(account_id=aurelia.id, name="Vela Enterprise", stage="NEGOTIATION"))
    save_contact(Contact(account_id=nordwind.id, name="Markus Reinhardt"))

    text = "Call mit Markus von Nordwind wegen Analytics Rollout"
    candidates = find_deal_candidates(text)
    assert candidates[0][0].id == d1.id
    assert candidates[0][1] > 0.8  # Account + Deal-Tokens + Kontakt
    assert all(deal.id != d2.id for deal, _ in candidates)  # Aurelia matcht nicht


def test_find_deal_candidates_empty_for_unrelated_text():
    a = _setup_account()
    _setup_deal(a)
    assert find_deal_candidates("voellig anderes thema ohne bezug") == []


def test_find_contact_candidates_fuzzy():
    a = _setup_account()
    save_contact(Contact(account_id=a.id, name="Dr. Katharina Bender"))
    save_contact(Contact(account_id=a.id, name="Andreas Kliment"))

    exact = find_contact_candidates(a.id, "dr. katharina bender")
    assert exact[0][1] == 1.0
    partial = find_contact_candidates(a.id, "Katharina Bender")
    assert partial and partial[0][0].name == "Dr. Katharina Bender"
    assert all(c.name != "Andreas Kliment" for c, s in partial if s > 0.5)


def test_unique_first_name_auto_matches():
    """P6-Beobachtung behoben: eindeutiger Vorname im Account-Kontext -> >=0.85 (auto)."""
    a = _setup_account()
    markus = save_contact(Contact(account_id=a.id, name="Markus Reinhardt"))
    save_contact(Contact(account_id=a.id, name="Sabine Vogt"))

    result = find_contact_candidates(a.id, "Markus")
    assert result[0][0].id == markus.id
    assert result[0][1] >= 0.85  # eindeutig -> automatische Zuordnung


def test_ambiguous_first_name_stays_in_ask_band():
    a = _setup_account()
    save_contact(Contact(account_id=a.id, name="Markus Reinhardt"))
    save_contact(Contact(account_id=a.id, name="Markus Weber"))

    result = find_contact_candidates(a.id, "Markus")
    assert result and all(score < 0.8 for _, score in result)  # mehrdeutig -> nachfragen
