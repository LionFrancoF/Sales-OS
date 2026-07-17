"""Kontext-Assembler des Beraters: reine Repository-Aufbereitung, ohne LLM.
Nutzt die tmp-DB-Fixture aus conftest.py."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.agents.advisor.context import build_deal_context, build_pipeline_context
from src.domain.account import Account
from src.domain.activity import Activity
from src.domain.contact import Contact
from src.domain.deal import Deal
from src.domain.meddpicc import DimensionAssessment, MeddpiccSnapshot
from src.repository.accounts import save_account
from src.repository.activities import save_activity
from src.repository.contacts import save_contact
from src.repository.deals import save_deal
from src.repository.snapshots import save_snapshot


def _dims() -> dict:
    keys = ["metrics", "economic_buyer", "decision_criteria", "decision_process",
            "paper_process", "identify_pain", "champion", "competition"]
    return {k: DimensionAssessment(findings=f"befund {k}", confidence="ZU_PRUEFEN",
                                   gaps=[f"luecke {k}"]) for k in keys}


def _setup_deal_with_everything():
    account = save_account(Account(name="Voltara Energie", industry="Energie"))
    deal = save_deal(Deal(account_id=account.id, name="Meldewesen", stage="EVALUATION"))
    save_contact(Contact(account_id=account.id, name="Anette Riegler", title="CFO",
                         role_in_deal="ECONOMIC_BUYER"))
    save_snapshot(MeddpiccSnapshot(
        deal_id=deal.id, dimensions=_dims(), overall_score=45, momentum="NEUTRAL",
        momentum_rationale="Konfliktfall", score_rationale="r", signal_bonus=0,
        framework="MEDDPICC", framework_rationale="erzwungen", prompt_version="test",
        deal_risks=["Champion-Klippe", "Ausschreibungsrisiko", "Case unbestaetigt"],
        next_best_questions=["Wer treibt nach Brandt?"],
        summary_for_manager="s1. s2. s3.",
    ))
    save_activity(Activity(deal_id=deal.id, type="CALL",
                           occurred_at=datetime(2026, 7, 9, 10, 0, tzinfo=timezone.utc),
                           raw_text="freigabe durch UND brandt geht", summary="Doppelereignis"))
    save_activity(Activity(deal_id=deal.id, type="CALL",
                           occurred_at=datetime(2026, 6, 16, 10, 0, tzinfo=timezone.utc),
                           raw_text="cfo termin", summary="Riegler-Termin"))
    return deal


def test_deal_context_contains_all_layers():
    _setup_deal_with_everything()
    ctx = build_deal_context("Meldewesen")
    assert "Voltara Energie" in ctx and "EVALUATION" in ctx
    assert "Anette Riegler" in ctx and "ECONOMIC_BUYER" in ctx
    assert "Score 45" in ctx and "NEUTRAL" in ctx
    assert "Champion-Klippe" in ctx                       # Risiken
    assert "freigabe durch UND brandt geht" in ctx        # Roh-Text NUR der juengsten Note
    assert "cfo termin" not in ctx                        # aeltere nur als Kurzzeile
    assert "Riegler-Termin" in ctx


def test_deal_context_unknown_deal_raises_lookup():
    with pytest.raises(LookupError):
        build_deal_context("gibt es nicht")


def test_pipeline_context_digest():
    _setup_deal_with_everything()
    a2 = save_account(Account(name="Papyrus Verlag"))
    save_deal(Deal(account_id=a2.id, name="Churn-Analytics", stage="PROSPECT"))
    ctx = build_pipeline_context()
    assert "2 Deals" in ctx
    assert "Meldewesen @ Voltara Energie" in ctx and "Score 45" in ctx
    assert "Churn-Analytics @ Papyrus Verlag" in ctx and "noch keine Analyse" in ctx


def test_pipeline_context_empty_db():
    assert "keine Deals" in build_pipeline_context()
