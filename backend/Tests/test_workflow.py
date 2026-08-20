from types import SimpleNamespace

from langchain_core.messages import AIMessage, ToolMessage

from app.agents import service_desk_agent
from app.graph.workflow import build_service_desk_graph
from app.schemas.classification import IntentClassification
from app.schemas.priority import PriorityAssessment


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


def _patch_agent(monkeypatch, messages):
    monkeypatch.setattr(
        service_desk_agent,
        "service_agent",
        SimpleNamespace(invoke=lambda payload: {"messages": messages}),
    )


def test_graph_knowledge_path(monkeypatch):
    _patch_classification(monkeypatch)
    _patch_priority(monkeypatch)
    _patch_agent(
        monkeypatch,
        [
            ToolMessage(
                content="Restart your VPN client.",
                name="search_knowledge_base",
                tool_call_id="call_1",
            ),
            AIMessage(content="Try restarting your VPN client and reconnecting."),
        ],
    )

    graph = build_service_desk_graph()
    result = graph.invoke({"user_query": "VPN is not connecting"})

    assert result["decision"] == "knowledge"
    assert result["tools_used"] == ["search_knowledge_base"]
    assert result["final_response"] == "Try restarting your VPN client and reconnecting."
    assert "ticket_number" not in result


def test_graph_clarification_path(monkeypatch):
    _patch_classification(monkeypatch, confidence=0.2)
    _patch_priority(monkeypatch)
    _patch_agent(
        monkeypatch,
        [AIMessage(content="Could you tell me which application is affected?")],
    )

    graph = build_service_desk_graph()
    result = graph.invoke({"user_query": "It doesn't work"})

    assert result["decision"] == "clarification"
    assert result["tools_used"] == []
    assert result["final_response"] == "Could you tell me which application is affected?"
    assert "ticket_number" not in result


def test_graph_ticket_path(monkeypatch):
    _patch_classification(monkeypatch)
    _patch_priority(monkeypatch, priority="P1", impact="High", urgency="High")
    _patch_agent(
        monkeypatch,
        [
            ToolMessage(
                content="Ticket created.",
                name="create_ticket",
                tool_call_id="call_1",
                artifact={"ticket_number": "NET-20260101000000-ABC123"},
            ),
            AIMessage(content="A ticket has been raised for you: NET-20260101000000-ABC123."),
        ],
    )

    graph = build_service_desk_graph()
    result = graph.invoke({"user_query": "VPN is completely down for the whole office"})

    assert result["decision"] == "ticket"
    assert result["ticket_number"] == "NET-20260101000000-ABC123"
    assert "NET-20260101000000-ABC123" in result["final_response"]


def test_graph_carries_classification_and_priority_into_final_state(monkeypatch):
    _patch_classification(monkeypatch, category="Network", subcategory="VPN")
    _patch_priority(monkeypatch, priority="P2")
    _patch_agent(monkeypatch, [AIMessage(content="Response")])

    graph = build_service_desk_graph()
    result = graph.invoke({"user_query": "VPN issue"})

    assert result["category"] == "Network"
    assert result["subcategory"] == "VPN"
    assert result["priority"] == "P2"
