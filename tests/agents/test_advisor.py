"""Berater-Agent: Prompt-Aufbau, History-Fuehrung, Kontext-Einbau — LLM gemockt."""
from __future__ import annotations

from unittest.mock import patch

from src.agents.advisor import agent as advisor_agent
from src.agents.advisor.prompts import PROMPT_VERSION, SYSTEM_PROMPT


def _mock_call_text(captured: dict):
    def fake(*, model, system, messages, max_tokens, thinking=None):
        captured["model"] = model
        captured["system"] = system
        captured["messages"] = [dict(m) for m in messages]
        return "Beraterantwort."
    return fake


def test_first_turn_builds_context_and_history():
    captured: dict = {}
    with patch.object(advisor_agent.llm, "call_text", _mock_call_text(captured)), \
         patch.object(advisor_agent, "load_for", return_value="WISSEN"):
        answer, history = advisor_agent.advise("Wie starte ich bei Voltara?")

    assert answer == "Beraterantwort."
    # System: [Prinzipien][Knowledge mit cache_control]
    assert captured["system"][0]["text"] == SYSTEM_PROMPT
    assert "WISSEN" in captured["system"][1]["text"]
    assert captured["system"][1]["cache_control"] == {"type": "ephemeral"}
    # Erste Message traegt Kontext-Kennzeichnung + Frage
    first = captured["messages"][0]["content"]
    assert "LIONS FRAGE" in first and "Wie starte ich bei Voltara?" in first
    assert "Methodik-Frage" in first  # ohne --deal/--pipeline explizit gekennzeichnet
    # History fortgeschrieben: [user, assistant]
    assert [m["role"] for m in history] == ["user", "assistant"]


def test_followup_turn_appends_plain_question():
    captured: dict = {}
    history = [
        {"role": "user", "content": "erste frage mit kontext"},
        {"role": "assistant", "content": "erste antwort"},
    ]
    with patch.object(advisor_agent.llm, "call_text", _mock_call_text(captured)), \
         patch.object(advisor_agent, "load_for", return_value="WISSEN"):
        _, new_history = advisor_agent.advise("Und was sage ich dem CFO?", history=history)

    # Folgefrage geht roh in den Verlauf (kein neuer Kontextblock)
    assert captured["messages"][2]["content"] == "Und was sage ich dem CFO?"
    assert len(new_history) == 4 and new_history[3]["role"] == "assistant"


def test_deal_context_is_injected_via_assembler():
    captured: dict = {}
    with patch.object(advisor_agent.llm, "call_text", _mock_call_text(captured)), \
         patch.object(advisor_agent, "load_for", return_value="WISSEN"), \
         patch.object(advisor_agent, "build_deal_context", return_value="=== DEAL-KONTEXT: X ==="):
        advisor_agent.advise("Frage", deal_name="X")
    assert "=== DEAL-KONTEXT: X ===" in captured["messages"][0]["content"]


def test_topics_are_passed_to_loader():
    captured: dict = {}
    with patch.object(advisor_agent.llm, "call_text", _mock_call_text(captured)), \
         patch.object(advisor_agent, "load_for", return_value="WISSEN") as loader:
        advisor_agent.advise("Frage", topics=["negotiation"])
    loader.assert_called_once_with("advisor", topics=["negotiation"])


def test_prompt_version_is_stable_hash():
    assert len(PROMPT_VERSION) == 12
