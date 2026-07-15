"""API-Tests (P7): alle Endpoints via TestClient, kompletter Ingest nachgestellt.

LLM-Aufrufe (Classifier/Analyzer) sind gemockt — die API ist duenne Haut,
getestet wird das Fehlerbild (404/409/422) und die Durchleitung.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.app import app
from src.config import settings
from src.domain.account import Account
from src.domain.deal import Deal
from src.orchestrator import ingest as ingest_mod
from src.orchestrator.classifier import Classification, ClassifiedContact, Signals
from src.repository import db
from src.repository.accounts import save_account
from src.repository.deals import save_deal

client = TestClient(app)


@pytest.fixture(autouse=True)
def tmp_db(tmp_path: Path):
    db.set_db_path(tmp_path / "test.db")
    yield
    db.set_db_path(settings.DB_PATH)


@pytest.fixture()
def setup_deal():
    account = save_account(Account(name="Nordwind Logistics"))
    deal = save_deal(Deal(account_id=account.id, name="Ops-Analytics", stage="DISCOVERY"))
    return account, deal


@pytest.fixture(autouse=True)
def mock_llm(monkeypatch):
    """Classifier + Analyzer gemockt (kein echter API-Call in API-Tests)."""
    from src.domain.meddpicc import DimensionAssessment, MeddpiccSnapshot

    def fake_classify(text):
        return Classification(
            activity_type="CALL", summary="Testcall.",
            signals=Signals(meddpicc_relevant=True, neue_kontakte=True, stakeholder_update=False,
                            next_steps=False, termin_zusage=False, wettbewerb=False),
            mentioned_people=["Markus Reinhardt"], mentioned_companies=["Nordwind"],
            contacts=[ClassifiedContact(name="Markus Reinhardt", title="Head of Ops",
                                        role_in_deal=None, influence=None, disposition=None)],
            next_steps=[],
        )

    def fake_analyze(notes, previous_snapshot=None, deal=None, corrections_block="", source_activity_ids=None):
        return MeddpiccSnapshot(
            deal_id=deal.id, source_activity_ids=source_activity_ids or [],
            overall_score=25, momentum="NEUTRAL",
            dimensions={"champion": DimensionAssessment(confidence="ZU_PRUEFEN")},
        )

    monkeypatch.setattr(ingest_mod, "classify", fake_classify)
    import src.agents.meddpicc.agent as agent_mod
    monkeypatch.setattr(agent_mod, "analyze", fake_analyze)
    # /deals/{id}/analyze importiert analyze lokal aus dem Agent-Modul
    import src.api.app as api_mod  # noqa: F401 (Referenz fuer Klarheit)


# ------------------------------------------------------------ Ingest (Kern-DoD)

def test_full_ingest_via_api(setup_deal):
    _, deal = setup_deal
    resp = client.post("/ingest", json={"text": "Call mit Nordwind wegen Ops-Analytics Rollout"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["deal_name"] == "Ops-Analytics"
    assert body["method"] == "auto" and body["confidence"] >= 0.8
    assert any("Snapshot" in a for a in body["actions"])
    assert any("Markus Reinhardt" in a for a in body["actions"])

    # Folgezustand ueber die API sichtbar
    detail = client.get(f"/deals/{deal.id}").json()
    assert detail["latest_snapshot"]["overall_score"] == 25
    assert any(c["name"] == "Markus Reinhardt" for c in detail["contacts"])


def test_ingest_dedup_returns_409(setup_deal):
    payload = {"text": "Call mit Nordwind wegen Ops-Analytics Rollout"}
    assert client.post("/ingest", json=payload).status_code == 200
    resp = client.post("/ingest", json=payload)
    assert resp.status_code == 409
    assert "Bereits verarbeitet" in resp.json()["detail"]


def test_ingest_unclear_resolution_returns_422_with_candidates(setup_deal):
    resp = client.post("/ingest", json={"text": "kurze notiz nordwind"})  # nur Account-Signal 0.5
    assert resp.status_code == 422
    detail = resp.json()["detail"]
    assert detail["candidates"], "Kandidatenliste fehlt"
    assert detail["candidates"][0]["deal"]["name"] == "Ops-Analytics"
    assert 0 < detail["candidates"][0]["confidence"] < settings.RESOLUTION_THRESHOLD
    assert "deal_name" in detail["hint"]


def test_ingest_with_deal_name_overrides(setup_deal):
    resp = client.post("/ingest", json={"text": "fremder text", "deal_name": "Ops-Analytics"})
    assert resp.status_code == 200
    assert resp.json()["method"] == "--deal"


def test_ingest_unknown_deal_name_404(setup_deal):
    resp = client.post("/ingest", json={"text": "x", "deal_name": "Gibt Es Nicht"})
    assert resp.status_code == 404


# ------------------------------------------------------------ Deals

def test_get_deals_lists_all(setup_deal):
    resp = client.get("/deals")
    assert resp.status_code == 200
    assert [d["name"] for d in resp.json()] == ["Ops-Analytics"]


def test_get_deal_detail_includes_account_and_empty_snapshot(setup_deal):
    account, deal = setup_deal
    detail = client.get(f"/deals/{deal.id}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["account"]["name"] == "Nordwind Logistics"
    assert body["latest_snapshot"] is None and body["contacts"] == []


def test_get_deal_unknown_404():
    assert client.get("/deals/unbekannt").status_code == 404


def test_post_analyze_saves_snapshot(setup_deal):
    _, deal = setup_deal
    resp = client.post(f"/deals/{deal.id}/analyze", json={"notes": "neue note"})
    assert resp.status_code == 200
    assert resp.json()["overall_score"] == 25
    assert client.get(f"/deals/{deal.id}").json()["latest_snapshot"] is not None


def test_post_analyze_unknown_deal_404():
    assert client.post("/deals/nix/analyze", json={"notes": "x"}).status_code == 404


# ------------------------------------------------------------ Corrections + Export

def test_post_correction_resolves_original(setup_deal):
    _, deal = setup_deal
    client.post(f"/deals/{deal.id}/analyze", json={"notes": "note"})  # Snapshot anlegen
    resp = client.post("/corrections", json={
        "deal_id": deal.id, "field_path": "dimensions.champion.confidence",
        "corrected_value": "UNBEKANNT", "comment": "zu grosszuegig",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["original_value"] == "ZU_PRUEFEN"  # aus dem letzten Snapshot aufgeloest
    assert body["corrected_value"] == "UNBEKANNT"


def test_post_correction_unknown_deal_404():
    resp = client.post("/corrections", json={
        "deal_id": "nix", "field_path": "x", "corrected_value": "y",
    })
    assert resp.status_code == 404


def test_export_csv_all_entities(setup_deal):
    client.post("/ingest", json={"text": "Call mit Nordwind wegen Ops-Analytics Rollout"})
    for entity in ("deals", "contacts", "activities"):
        resp = client.get(f"/export/csv?entity={entity}")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/csv")
        lines = resp.text.strip().splitlines()
        assert len(lines) >= 2, f"{entity}: Header + mind. 1 Zeile erwartet"
    assert client.get("/export/csv?entity=quatsch").status_code == 422  # Literal-Validierung
