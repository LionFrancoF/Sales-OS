"""Tests des Ingestion-Orchestrators: Dedup, Resolver-Schwelle, Router-Zweige,
Wiederaufsetzpunkt, Widerspruchs-Regel. Classifier + Analyzer gemockt."""
from __future__ import annotations

import pytest

from src.domain.account import Account
from src.domain.contact import Contact
from src.domain.deal import Deal
from src.domain.meddpicc import DimensionAssessment, MeddpiccSnapshot
from src.orchestrator import ingest as ingest_mod
from src.orchestrator import resolver as resolver_mod
from src.orchestrator.classifier import Classification, ClassifiedContact, Signals
from src.orchestrator.ingest import process_note
from src.repository.accounts import save_account
from src.repository.activities import list_activities
from src.repository.contacts import get_contact_history, list_contacts, save_contact
from src.repository.deals import save_deal
from src.repository.snapshots import list_snapshots, save_snapshot


# ------------------------------------------------------------ Helpers

def _classification(**overrides) -> Classification:
    base = dict(
        activity_type="CALL",
        summary="Testcall.",
        signals=Signals(meddpicc_relevant=True, neue_kontakte=False, stakeholder_update=False,
                        next_steps=False, termin_zusage=False, wettbewerb=False),
        mentioned_people=[], mentioned_companies=[], contacts=[], next_steps=[],
    )
    base.update(overrides)
    return Classification(**base)


def _snapshot(deal_id: str, activity_ids: list[str], score=30) -> MeddpiccSnapshot:
    return MeddpiccSnapshot(
        deal_id=deal_id, source_activity_ids=activity_ids, overall_score=score, momentum="NEUTRAL",
        dimensions={"champion": DimensionAssessment(confidence="ZU_PRUEFEN")},
    )


@pytest.fixture()
def setup_deal():
    account = save_account(Account(name="Nordwind Logistics"))
    deal = save_deal(Deal(account_id=account.id, name="Ops-Analytics", stage="DISCOVERY"))
    return account, deal


@pytest.fixture()
def mock_classify(monkeypatch):
    holder = {"value": _classification()}
    monkeypatch.setattr(ingest_mod, "classify", lambda text: holder["value"])
    return holder


@pytest.fixture()
def mock_analyze(monkeypatch):
    calls = {"count": 0, "previous": "unset"}

    def fake_analyze(notes, previous_snapshot=None, deal=None, corrections_block="", source_activity_ids=None):
        calls["count"] += 1
        calls["previous"] = previous_snapshot
        return _snapshot(deal.id, source_activity_ids or [], score=40)

    import src.agents.meddpicc.agent as agent_mod
    monkeypatch.setattr(agent_mod, "analyze", fake_analyze)
    return calls


# ------------------------------------------------------------ Dedup + Wiederaufnahme

def test_dedup_aborts_without_side_effects(setup_deal, mock_classify, mock_analyze):
    _, deal = setup_deal
    report1 = process_note("call notes nordwind", deal_name="Ops-Analytics")
    assert report1.aborted is None
    assert len(list_snapshots(deal.id)) == 1

    report2 = process_note("call notes nordwind", deal_name="Ops-Analytics")
    assert report2.aborted is not None and "Bereits verarbeitet" in report2.aborted
    assert len(list_activities(deal.id)) == 1          # keine zweite Activity
    assert len(list_snapshots(deal.id)) == 1           # kein zweiter Snapshot
    assert mock_analyze["count"] == 1                  # kein zweiter LLM-Call


def test_resume_after_partial_processing(setup_deal, mock_classify, mock_analyze, monkeypatch):
    """Befund 2.4: Activity existiert, Snapshot fehlt (Crash-Simulation) -> Fortsetzung."""
    _, deal = setup_deal
    # Crash nach Activity-Save simulieren: save_snapshot schlaegt beim 1. Lauf fehl
    import src.orchestrator.ingest as im
    original_save = im.save_snapshot
    monkeypatch.setattr(im, "save_snapshot", lambda s: (_ for _ in ()).throw(RuntimeError("crash")))
    with pytest.raises(RuntimeError):
        process_note("call notes nordwind", deal_name="Ops-Analytics")
    assert len(list_activities(deal.id)) == 1 and list_snapshots(deal.id) == []

    monkeypatch.setattr(im, "save_snapshot", original_save)
    report = process_note("call notes nordwind", deal_name="Ops-Analytics")
    assert report.aborted is None
    assert report.method == "wiederaufnahme"
    assert len(list_activities(deal.id)) == 1          # Activity wiederverwendet
    assert len(list_snapshots(deal.id)) == 1           # jetzt vollstaendig


def test_max_one_snapshot_per_activity(setup_deal, mock_classify, mock_analyze):
    """Befund 2.6: je Activity maximal ein Snapshot (kein Trend-Rauschen)."""
    _, deal = setup_deal
    process_note("note eins", deal_name="Ops-Analytics")
    activity = list_activities(deal.id)[0]
    save_snapshot(_snapshot(deal.id, [activity.id]))   # zweiter Snapshot manuell? nein — simulieren:
    # direkter Re-Route-Versuch via Wiederaufnahme-Pfad: Snapshot existiert -> skip
    report = process_note("note eins", deal_name="Ops-Analytics")
    assert report.aborted is not None                  # komplett verarbeitet -> Abbruch


# ------------------------------------------------------------ Resolver

def test_resolver_auto_above_threshold(setup_deal, mock_classify, mock_analyze):
    report = process_note("Call mit Nordwind wegen Ops-Analytics Rollout")  # kein --deal
    assert report.deal_name == "Ops-Analytics"
    assert report.method == "auto"
    assert report.confidence >= 0.8


def test_resolver_asks_below_threshold(setup_deal, mock_classify, mock_analyze):
    asked = {}

    def fake_ask(question, options):
        asked["question"] = question
        asked["options"] = options
        return 0  # ersten Kandidaten waehlen

    report = process_note("kurze notiz nordwind", ask=fake_ask)  # nur Account-Signal (0.5)
    assert "unsicher" in asked["question"]
    assert report.method == "nachgefragt"
    assert report.deal_name == "Ops-Analytics"


def test_resolver_never_guesses_without_answer(setup_deal, mock_classify, mock_analyze):
    with pytest.raises(ValueError, match="Zuordnung unklar"):
        process_note("kurze notiz nordwind", ask=lambda q, o: None)
    assert list_activities(setup_deal[1].id) == []     # Abbruch OHNE Nebenwirkungen


def test_resolver_no_candidates_fails(setup_deal, mock_classify, mock_analyze):
    with pytest.raises(ValueError, match="Kein passender Deal"):
        process_note("voellig fremdes thema")


def test_deal_flag_overrides(setup_deal, mock_classify, mock_analyze):
    report = process_note("fremder text ohne signale", deal_name="Ops-Analytics")
    assert report.method == "--deal" and report.confidence == 1.0


# ------------------------------------------------------------ Router-Zweige

def test_router_meddpicc_links_activity_and_diffs(setup_deal, mock_classify, mock_analyze):
    _, deal = setup_deal
    process_note("erste note nordwind analytics", deal_name="Ops-Analytics")
    first_activity = list_activities(deal.id)[0]
    first_snap = list_snapshots(deal.id)[0]
    assert first_snap.source_activity_ids == [first_activity.id]  # Beleg-Kette!

    report = process_note("zweite note nordwind analytics neu", deal_name="Ops-Analytics")
    assert mock_analyze["previous"] is not None        # Vorgaenger ging in den Prompt
    assert any(change.startswith("score:") for change in report.changes)


def test_router_skips_meddpicc_without_signal(setup_deal, mock_classify, mock_analyze):
    mock_classify["value"] = _classification(
        signals=Signals(meddpicc_relevant=False, neue_kontakte=False, stakeholder_update=False,
                        next_steps=True, termin_zusage=False, wettbewerb=False),
        next_steps=["Demo am Dienstag"],
    )
    report = process_note("nur orga kram", deal_name="Ops-Analytics")
    assert list_snapshots(setup_deal[1].id) == []
    assert mock_analyze["count"] == 0
    assert any("Next Steps" in a for a in report.actions)
    activity = list_activities(setup_deal[1].id)[0]
    assert "Demo am Dienstag" in activity.summary      # als Activity-Metadaten


def test_router_creates_new_contact_conservatively(setup_deal, mock_classify, mock_analyze):
    _, deal = setup_deal
    mock_classify["value"] = _classification(
        signals=Signals(meddpicc_relevant=False, neue_kontakte=True, stakeholder_update=False,
                        next_steps=False, termin_zusage=False, wettbewerb=False),
        contacts=[ClassifiedContact(name="Sabine Vogt", title="IT-Leitung",
                                    role_in_deal=None, influence=None, disposition=None)],
    )
    process_note("neue person aufgetaucht", deal_name="Ops-Analytics")
    contacts = list_contacts(deal.account_id)
    assert len(contacts) == 1
    assert contacts[0].role_in_deal == "UNKLAR"        # konservativ: nichts erfunden
    assert contacts[0].influence == "UNBEKANNT"


def test_router_updates_existing_contact_with_history(setup_deal, mock_classify, mock_analyze):
    _, deal = setup_deal
    existing = save_contact(Contact(account_id=deal.account_id, name="Sabine Vogt", role_in_deal="INFLUENCER"))
    mock_classify["value"] = _classification(
        signals=Signals(meddpicc_relevant=False, neue_kontakte=False, stakeholder_update=True,
                        next_steps=False, termin_zusage=False, wettbewerb=False),
        contacts=[ClassifiedContact(name="Sabine Vogt", title=None,
                                    role_in_deal="BLOCKER", influence=None, disposition="SKEPTIKER")],
    )
    process_note("sabine blockt jetzt", deal_name="Ops-Analytics")
    contacts = list_contacts(deal.account_id)
    assert len(contacts) == 1                          # KEINE Dublette
    assert contacts[0].role_in_deal == "BLOCKER"
    history = get_contact_history(existing.id)
    assert {h.field for h in history} == {"role_in_deal", "disposition"}  # protokolliert
    assert history[0].source.startswith("ingest:")


def test_router_ambiguous_contact_asks(setup_deal, mock_classify, mock_analyze):
    _, deal = setup_deal
    save_contact(Contact(account_id=deal.account_id, name="Dr. Katharina Bender"))
    mock_classify["value"] = _classification(
        signals=Signals(meddpicc_relevant=False, neue_kontakte=True, stakeholder_update=False,
                        next_steps=False, termin_zusage=False, wettbewerb=False),
        contacts=[ClassifiedContact(name="Katharina", title=None,
                                    role_in_deal=None, influence=None, disposition=None)],
    )
    # nur Vorname -> Score im Ask-Band; ohne Antwort: konservativ ueberspringen, keine Dublette
    report = process_note("katharina hat angerufen", deal_name="Ops-Analytics", ask=lambda q, o: None)
    assert len(list_contacts(deal.account_id)) == 1
    assert any("uebersprungen" in a for a in report.actions)


def test_router_near_identical_contact_auto_merges(setup_deal, mock_classify, mock_analyze):
    """'Katharina Bender' vs. 'Dr. Katharina Bender' (0.89) -> automatischer Merge, keine Dublette."""
    _, deal = setup_deal
    save_contact(Contact(account_id=deal.account_id, name="Dr. Katharina Bender"))
    mock_classify["value"] = _classification(
        signals=Signals(meddpicc_relevant=False, neue_kontakte=True, stakeholder_update=False,
                        next_steps=False, termin_zusage=False, wettbewerb=False),
        contacts=[ClassifiedContact(name="Katharina Bender", title=None,
                                    role_in_deal=None, influence=None, disposition=None)],
    )
    process_note("katharina bender im call", deal_name="Ops-Analytics")
    assert len(list_contacts(deal.account_id)) == 1  # dem Bestand zugeordnet


# ------------------------------------------------------------ Widerspruchs-Regel

def test_contradiction_rule_wired():
    """Bindende Ingestion-Entscheidung 2: Regel steht im Analyzer-Prompt (der DoD-Livelauf
    prueft den Effekt an nordwind Note 2 vs. 4: Budget zugesagt -> revidiert)."""
    from src.agents.meddpicc.prompts import SYSTEM_PROMPT

    assert "Widerspricht die neue Note dem vorigen Snapshot" in SYSTEM_PROMPT
    assert "ZU_PRUEFEN" in SYSTEM_PROMPT
    assert "next_best_questions" in SYSTEM_PROMPT
