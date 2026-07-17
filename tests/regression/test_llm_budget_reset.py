"""Regression (2026-07-17): Die Breaker-Zaehler in src/agents/llm.py waren
prozess-global ohne Reset. In langlebigen Prozessen (uvicorn-API, advise -i)
akkumulierten sie ueber Nutzer-Aktionen hinweg — nach 25 Calls haette der
Breaker die API dauerhaft bzw. das Berater-Gespraech ab Turn 25 abgewuergt.
Fix: reset_budget() pro Nutzer-Aktion (API-Middleware, advise-i-Turn)."""
from __future__ import annotations

import pytest

from src.agents import llm
from src.config import settings


def test_breaker_trips_then_reset_clears(monkeypatch):
    llm.reset_budget()
    monkeypatch.setattr(llm, "_calls_this_command", settings.MAX_LLM_CALLS_PER_COMMAND)
    with pytest.raises(RuntimeError, match="Circuit-Breaker"):
        llm._check_circuit_breaker()
    llm.reset_budget()
    llm._check_circuit_breaker()  # darf nach Reset nicht mehr werfen


def test_api_resets_budget_per_request(monkeypatch):
    from fastapi.testclient import TestClient

    from src.api.app import app

    monkeypatch.setattr(llm, "_calls_this_command", settings.MAX_LLM_CALLS_PER_COMMAND)
    client = TestClient(app)
    client.get("/deals")  # beliebiger Request — Middleware muss Budget zuruecksetzen
    assert llm._calls_this_command == 0
