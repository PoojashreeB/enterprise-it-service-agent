from types import SimpleNamespace

import pytest

from app.agents import service_desk_agent
from app.graph.workflow import build_service_desk_graph, route_decision
from app.schemas.classification import IntentClassification
from app.schemas.decision import Decision
from app.schemas.priority import PriorityAssessment


# ================================================================
# route_decision
# ================================================================

@pytest.mark.parametrize(
    "decision_value, expected_node",
    [
        ("knowledge", "retrieve_knowledge"),
        ("clarification", "ask_clarification"),
        ("ticket", "create_ticket"),
    ],
)
def test_route_decision_routes_to_expected_node(decision_value, expected_node):
    assert route_decision({"decision": decision_value}) == expected_node


def test_route_decision_falls_back_to_clarification_when_missing():
    assert route_decision({}) == "ask_clarification"


def test_route_decision_falls_back_to_clarification_when_unrecognized():
    assert route_decision({"decision": "something_unexpected"}) == "ask_clarification"


# ================================================================
# Full graph execution
# ================================================================

def _patch_classification(monkeypatch, **overrides):
    defaults = dict(
        intent="vpn_issue",
        category="Network",
        subcategory="VPN",
        confidence=0.9,
    )
    defaults.update(overrides)
    monkeypatch.setattr(
        service_desk_agent,
        "classification_llm",
        SimpleNamespace(invoke=lambda prompt: IntentClassification(**defaults)),
    )


def _patch_priority(monkeypatch, **overrides):
    defaults = dict(
        impact="Medium",
        urgency="Medium",
        priority="P3",
        justification="Affects a single user.",
    )
    defaults.update(overrides)
    monkeypatch.setattr(
        service_desk_agent,
        "priority_llm",
        SimpleNamespace(invoke=lambda prompt: PriorityAssessment(**defaults)),
    )


def _patch_decision(monkeypatch, decision_value):
    monkeypatch.setattr(
        service_desk_agent,
        "decision_llm",
        SimpleNamespace(
            invoke=lambda prompt: Decision(decision=decision_value, reason="Because reasons.")
        ),
    )


def _patch_llm(monkeypatch, content):
    monkeypatch.setattr(
        service_desk_agent,
        "llm",
        SimpleNamespace(invoke=lambda prompt: SimpleNamespace(content=content)),
    )


def test_graph_knowledge_path(monkeypatch):
    _patch_classification(monkeypatch)
    _patch_priority(monkeypatch)
    _patch_decision(monkeypatch, "knowledge")
    monkeypatch.setattr(
        service_desk_agent,
        "retrieve",
        lambda query, top_k: [{"source": "kb-vpn", "content": "Restart your VPN client."}],
    )
    _patch_llm(monkeypatch, "Try restarting your VPN client and reconnecting.")

    graph = build_service_desk_graph()
    result = graph.invoke({"user_query": "VPN is not connecting"})

    assert result["decision"] == "knowledge"
    assert "Restart your VPN client." in result["knowledge"]
    assert result["final_response"] == "Try restarting your VPN client and reconnecting."
    assert "ticket_number" not in result
    assert "clarification_question" not in result


def test_graph_clarification_path(monkeypatch):
    _patch_classification(monkeypatch, confidence=0.2)
    _patch_priority(monkeypatch)
    _patch_decision(monkeypatch, "clarification")
    _patch_llm(monkeypatch, "Could you tell me which application is affected?")

    graph = build_service_desk_graph()
    result = graph.invoke({"user_query": "It doesn't work"})

    assert result["decision"] == "clarification"
    assert result["clarification_question"] == "Could you tell me which application is affected?"
    assert result["final_response"] == "Could you tell me which application is affected?"
    assert "ticket_number" not in result
    assert "knowledge" not in result


def test_graph_ticket_path(monkeypatch):
    _patch_classification(monkeypatch)
    _patch_priority(monkeypatch, priority="P1", impact="High", urgency="High")
    _patch_decision(monkeypatch, "ticket")
    monkeypatch.setattr(
        service_desk_agent,
        "create_ticket_record",
        lambda **kwargs: {"ticket_number": "NET-20260101000000-ABC123"},
    )
    _patch_llm(monkeypatch, "A ticket has been raised for you: NET-20260101000000-ABC123.")

    graph = build_service_desk_graph()
    result = graph.invoke({"user_query": "VPN is completely down for the whole office"})

    assert result["decision"] == "ticket"
    assert result["ticket_number"] == "NET-20260101000000-ABC123"
    assert "NET-20260101000000-ABC123" in result["final_response"]
    assert "knowledge" not in result
    assert "clarification_question" not in result
