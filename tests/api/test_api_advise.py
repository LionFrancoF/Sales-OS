"""POST /advise — duenne Haut ueber dem Berater (one-shot, stateless)."""
from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from src.api.app import app

client = TestClient(app)


def test_post_advise_returns_answer():
    with patch("src.agents.advisor.agent.advise", return_value=("Rat.", [])) as mock_advise:
        resp = client.post("/advise", json={"question": "Wie priorisiere ich?", "pipeline": True})
    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"] == "Rat." and len(body["prompt_version"]) == 12
    _, kwargs = mock_advise.call_args
    assert kwargs["pipeline"] is True and kwargs["deal_name"] is None


def test_post_advise_unknown_deal_404():
    with patch("src.agents.advisor.agent.advise", side_effect=LookupError("Kein Deal 'X'.")):
        resp = client.post("/advise", json={"question": "F", "deal_name": "X"})
    assert resp.status_code == 404
