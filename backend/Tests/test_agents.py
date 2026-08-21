from types import SimpleNamespace

import pytest
from langchain_core.messages import AIMessage, ToolMessage

from app.agents import service_desk_agent
from app.schemas.classification import IntentClassification
from app.schemas.priority import PriorityAssessment


# ================================================================
# _invoke_with_retry
# ================================================================

def test_invoke_with_retry_retries_transient_failures_then_succeeds():
    calls = {"count": 0}

    class FlakyRunnable:
        def invoke(self, input_):
            calls["count"] += 1
            if calls["count"] < 3:
                raise ValueError("Upstream error: Service temporarily overloaded")
            return "ok"

    result = service_desk_agent._invoke_with_retry(FlakyRunnable(), "prompt")

    assert result == "ok"
    assert calls["count"] == 3


def test_invoke_with_retry_gives_up_after_max_attempts():
    calls = {"count": 0}

    class AlwaysFailingRunnable:
        def invoke(self, input_):
            calls["count"] += 1
            raise ValueError("permanent failure")

    with pytest.raises(ValueError):
        service_desk_agent._invoke_with_retry(AlwaysFailingRunnable(), "prompt")

    assert calls["count"] == 3


# ================================================================
# classify_request
# ================================================================

def test_classify_request_sets_state_from_llm_result(monkeypatch):
    result = IntentClassification(
        intent="reset_password",
        category="Access Management",
        subcategory="Password Reset",
        confidence=0.92,
    )
    monkeypatch.setattr(
        service_desk_agent,
        "classification_llm",
        SimpleNamespace(invoke=lambda prompt: result),
    )

    state = service_desk_agent.classify_request({"user_query": "I forgot my password"})

    assert state["intent"] == "reset_password"
    assert state["category"] == "Access Management"
    assert state["subcategory"] == "Password Reset"
    assert state["confidence"] == 0.92


def test_classify_request_handles_missing_query(monkeypatch):
    captured = {}

    def fake_invoke(prompt):
        captured["prompt"] = prompt
        return IntentClassification(
            intent="unknown",
            category="unknown",
            subcategory="unknown",
            confidence=0.1,
        )

    monkeypatch.setattr(
        service_desk_agent,
        "classification_llm",
        SimpleNamespace(invoke=fake_invoke),
    )

    service_desk_agent.classify_request({})

    assert "(no request text was provided)" in captured["prompt"]


# ================================================================
# assess_priority
# ================================================================

def test_assess_priority_sets_state_from_llm_result(monkeypatch):
    result = PriorityAssessment(
        impact="High",
        urgency="High",
        priority="P1",
        justification="Blocks the user from working entirely.",
    )
    monkeypatch.setattr(
        service_desk_agent,
        "priority_llm",
        SimpleNamespace(invoke=lambda prompt: result),
    )

    state = service_desk_agent.assess_priority(
        {
            "user_query": "VPN is completely down",
            "intent": "vpn_issue",
            "category": "Network",
            "subcategory": "VPN",
            "confidence": 0.8,
        }
    )

    assert state["impact"] == "High"
    assert state["urgency"] == "High"
    assert state["priority"] == "P1"
    assert state["justification"] == "Blocks the user from working entirely."


def test_assess_priority_includes_classification_in_prompt(monkeypatch):
    captured = {}

    def fake_invoke(prompt):
        captured["prompt"] = prompt
        return PriorityAssessment(
            impact="Low",
            urgency="Low",
            priority="P5",
            justification="Minor issue.",
        )

    monkeypatch.setattr(
        service_desk_agent,
        "priority_llm",
        SimpleNamespace(invoke=fake_invoke),
    )

    service_desk_agent.assess_priority(
        {
            "user_query": "My mouse is squeaky",
            "intent": "hardware_issue",
            "category": "Hardware",
            "subcategory": "Peripherals",
            "confidence": 0.5,
        }
    )

    assert "Intent: hardware_issue" in captured["prompt"]
    assert "Category: Hardware" in captured["prompt"]


# ================================================================
# run_agent
# ================================================================

def _fake_agent(monkeypatch, messages, captured=None):
    def fake_invoke(payload):
        if captured is not None:
            captured["payload"] = payload
        return {"messages": messages}

    monkeypatch.setattr(
        service_desk_agent,
        "service_agent",
        SimpleNamespace(invoke=fake_invoke),
    )


def test_run_agent_sets_final_response_from_last_message(monkeypatch):
    messages = [AIMessage(content="Here is how you can fix that.")]
    _fake_agent(monkeypatch, messages)

    state = service_desk_agent.run_agent({"user_query": "Outlook won't open"})

    assert state["final_response"] == "Here is how you can fix that."
    assert state["tools_used"] == []
    assert state["decision"] == "clarification"
    assert "ticket_number" not in state


def test_run_agent_tracks_knowledge_tool_use(monkeypatch):
    messages = [
        ToolMessage(
            content="Restart your VPN client.",
            name="search_knowledge_base",
            tool_call_id="call_1",
        ),
        AIMessage(content="Try restarting your VPN client."),
    ]
    _fake_agent(monkeypatch, messages)

    state = service_desk_agent.run_agent({"user_query": "VPN is not connecting"})

    assert state["decision"] == "knowledge"
    assert state["tools_used"] == ["search_knowledge_base"]
    assert state["final_response"] == "Try restarting your VPN client."


def test_run_agent_tracks_ticket_creation(monkeypatch):
    messages = [
        ToolMessage(
            content="Ticket NET-20260101000000-ABC123 created.",
            name="create_ticket",
            tool_call_id="call_1",
            artifact={"ticket_number": "NET-20260101000000-ABC123"},
        ),
        AIMessage(content="A ticket has been raised for you."),
    ]
    _fake_agent(monkeypatch, messages)

    state = service_desk_agent.run_agent({"user_query": "VPN is down for the whole office"})

    assert state["decision"] == "ticket"
    assert state["ticket_number"] == "NET-20260101000000-ABC123"
    assert "create_ticket" in state["tools_used"]


def test_run_agent_tracks_password_reset(monkeypatch):
    messages = [
        ToolMessage(
            content="[MOCK] A password reset email has been queued for 'jdoe'.",
            name="reset_password",
            tool_call_id="call_1",
            artifact={
                "username": "jdoe",
                "reason": "Requested via the chat assistant.",
                "status": "queued",
            },
        ),
        AIMessage(content="I've queued a password reset email for you."),
    ]
    _fake_agent(monkeypatch, messages)

    state = service_desk_agent.run_agent({"user_query": "I forgot my password, username jdoe"})

    assert state["decision"] == "password_reset"
    assert state["password_reset"] == {
        "username": "jdoe",
        "reason": "Requested via the chat assistant.",
        "status": "queued",
    }
    assert "reset_password" in state["tools_used"]
    assert "ticket_number" not in state


def test_run_agent_prioritizes_ticket_decision_over_knowledge(monkeypatch):
    messages = [
        ToolMessage(
            content="Restart your VPN client.",
            name="search_knowledge_base",
            tool_call_id="call_1",
        ),
        ToolMessage(
            content="Ticket created.",
            name="create_ticket",
            tool_call_id="call_2",
            artifact={"ticket_number": "NET-20260101000000-XYZ999"},
        ),
        AIMessage(content="I raised a ticket for you after trying the standard steps."),
    ]
    _fake_agent(monkeypatch, messages)

    state = service_desk_agent.run_agent({"user_query": "Still broken after restarting"})

    assert state["decision"] == "ticket"
    assert state["ticket_number"] == "NET-20260101000000-XYZ999"
    assert set(state["tools_used"]) == {"search_knowledge_base", "create_ticket"}


def test_run_agent_passes_query_and_context_to_the_agent(monkeypatch):
    captured = {}
    messages = [AIMessage(content="Response")]
    _fake_agent(monkeypatch, messages, captured=captured)

    service_desk_agent.run_agent(
        {
            "user_query": "My mouse is squeaky",
            "intent": "hardware_issue",
            "category": "Hardware",
            "subcategory": "Peripherals",
            "priority": "P5",
            "impact": "Low",
            "urgency": "Low",
            "justification": "Minor issue.",
        }
    )

    sent_messages = captured["payload"]["messages"]
    system_content = sent_messages[0].content
    human_content = sent_messages[1].content

    assert "Category: Hardware" in system_content
    assert "Priority: P5" in system_content
    assert human_content == "My mouse is squeaky"


def test_run_agent_handles_missing_query(monkeypatch):
    captured = {}
    messages = [AIMessage(content="Could you share more details?")]
    _fake_agent(monkeypatch, messages, captured=captured)

    service_desk_agent.run_agent({})

    human_content = captured["payload"]["messages"][1].content
    assert human_content == "(no request text was provided)"
