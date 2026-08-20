from types import SimpleNamespace

import pytest

from app.agents import service_desk_agent
from app.schemas.classification import IntentClassification
from app.schemas.priority import PriorityAssessment
from app.schemas.decision import Decision


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
# decide_next_step
# ================================================================

@pytest.mark.parametrize("decision_value", ["knowledge", "clarification", "ticket"])
def test_decide_next_step_sets_state(monkeypatch, decision_value):
    result = Decision(decision=decision_value, reason="Some reasoning.")
    monkeypatch.setattr(
        service_desk_agent,
        "decision_llm",
        SimpleNamespace(invoke=lambda prompt: result),
    )

    state = service_desk_agent.decide_next_step({"user_query": "Something is broken"})

    assert state["decision"] == decision_value


# ================================================================
# retrieve_knowledge
# ================================================================

def test_retrieve_knowledge_with_results(monkeypatch):
    documents = [
        {"source": "kb-1", "content": "Restart the VPN client."},
        {"source": "kb-2", "content": "Check your network cable."},
    ]
    monkeypatch.setattr(
        service_desk_agent,
        "retrieve",
        lambda query, top_k: documents,
    )

    state = service_desk_agent.retrieve_knowledge({"user_query": "VPN is not connecting"})

    assert state["retrieved_documents"] == documents
    assert "kb-1" in state["knowledge"]
    assert "Restart the VPN client." in state["knowledge"]
    assert "kb-2" in state["knowledge"]


def test_retrieve_knowledge_with_no_results(monkeypatch):
    monkeypatch.setattr(
        service_desk_agent,
        "retrieve",
        lambda query, top_k: [],
    )

    state = service_desk_agent.retrieve_knowledge({"user_query": "Obscure issue"})

    assert state["retrieved_documents"] == []
    assert state["knowledge"] == "No relevant enterprise knowledge was found."


# ================================================================
# ask_clarification
# ================================================================

def test_ask_clarification_sets_state(monkeypatch):
    monkeypatch.setattr(
        service_desk_agent,
        "llm",
        SimpleNamespace(
            invoke=lambda prompt: SimpleNamespace(
                content="Which application are you trying to access?"
            )
        ),
    )

    state = service_desk_agent.ask_clarification(
        {
            "user_query": "I can't access it",
            "intent": "access_issue",
            "category": "Access Management",
            "subcategory": "unknown",
            "confidence": 0.3,
        }
    )

    assert state["clarification_question"] == "Which application are you trying to access?"


# ================================================================
# create_ticket
# ================================================================

def test_create_ticket_sets_ticket_number(monkeypatch):
    captured = {}

    def fake_create_ticket_record(**kwargs):
        captured.update(kwargs)
        return {"ticket_number": "NET-20260101000000-ABC123"}

    monkeypatch.setattr(
        service_desk_agent,
        "create_ticket_record",
        fake_create_ticket_record,
    )

    state = service_desk_agent.create_ticket(
        {
            "category": "Network",
            "subcategory": "VPN",
            "priority": "P1",
            "impact": "High",
            "urgency": "High",
            "justification": "Cannot work at all.",
            "user_query": "VPN is down",
        }
    )

    assert state["ticket_number"] == "NET-20260101000000-ABC123"
    assert captured["category"] == "Network"
    assert captured["user_query"] == "VPN is down"


def test_create_ticket_defaults_missing_fields(monkeypatch):
    captured = {}

    def fake_create_ticket_record(**kwargs):
        captured.update(kwargs)
        return {"ticket_number": "TCK-20260101000000-ZZZ999"}

    monkeypatch.setattr(
        service_desk_agent,
        "create_ticket_record",
        fake_create_ticket_record,
    )

    service_desk_agent.create_ticket({})

    assert captured["category"] == ""
    assert captured["user_query"] == ""


# ================================================================
# generate_response
# ================================================================

def test_generate_response_includes_knowledge_when_decision_is_knowledge(monkeypatch):
    captured = {}

    def fake_invoke(prompt):
        captured["prompt"] = prompt
        return SimpleNamespace(content="Try restarting your VPN client.")

    monkeypatch.setattr(
        service_desk_agent,
        "llm",
        SimpleNamespace(invoke=fake_invoke),
    )

    state = service_desk_agent.generate_response(
        {
            "user_query": "VPN not connecting",
            "decision": "knowledge",
            "knowledge": "Restart the VPN client and reconnect.",
        }
    )

    assert state["final_response"] == "Try restarting your VPN client."
    assert "Restart the VPN client and reconnect." in captured["prompt"]


def test_generate_response_includes_clarification_when_decision_is_clarification(monkeypatch):
    captured = {}

    def fake_invoke(prompt):
        captured["prompt"] = prompt
        return SimpleNamespace(content="Could you tell me which app you mean?")

    monkeypatch.setattr(
        service_desk_agent,
        "llm",
        SimpleNamespace(invoke=fake_invoke),
    )

    state = service_desk_agent.generate_response(
        {
            "user_query": "It won't open",
            "decision": "clarification",
            "clarification_question": "Which application won't open?",
        }
    )

    assert state["final_response"] == "Could you tell me which app you mean?"
    assert "Which application won't open?" in captured["prompt"]


def test_generate_response_includes_ticket_number_when_decision_is_ticket(monkeypatch):
    captured = {}

    def fake_invoke(prompt):
        captured["prompt"] = prompt
        return SimpleNamespace(content="A ticket has been raised for you.")

    monkeypatch.setattr(
        service_desk_agent,
        "llm",
        SimpleNamespace(invoke=fake_invoke),
    )

    state = service_desk_agent.generate_response(
        {
            "user_query": "My laptop won't boot",
            "decision": "ticket",
            "ticket_number": "HW-20260101000000-AAA111",
            "justification": "Requires on-site hardware diagnosis.",
        }
    )

    assert state["final_response"] == "A ticket has been raised for you."
    assert "HW-20260101000000-AAA111" in captured["prompt"]
    assert "Requires on-site hardware diagnosis." in captured["prompt"]
