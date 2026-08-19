from langgraph.graph import StateGraph, START, END

from app.graph.state import ServiceDeskState

from app.agents.service_desk_agent import (
    classify_request,
    assess_priority,
    decide_next_step,
    retrieve_knowledge,
    ask_clarification,
    create_ticket,
    generate_response,
)


def route_decision(state: ServiceDeskState):

    decision = state.get("decision")

    if decision == "knowledge":
        return "retrieve_knowledge"

    if decision == "clarification":
        return "ask_clarification"

    if decision == "ticket":
        return "create_ticket"

    # Safe fallback
    return "ask_clarification"


def build_service_desk_graph():

    graph = StateGraph(ServiceDeskState)

    # ========================================================
    # Nodes
    # ========================================================

    graph.add_node(
        "classify_request",
        classify_request
    )

    graph.add_node(
        "assess_priority",
        assess_priority
    )

    graph.add_node(
        "decide_next_step",
        decide_next_step
    )

    graph.add_node(
        "retrieve_knowledge",
        retrieve_knowledge
    )

    graph.add_node(
        "ask_clarification",
        ask_clarification
    )

    graph.add_node(
        "create_ticket",
        create_ticket
    )

    graph.add_node(
        "generate_response",
        generate_response
    )

    # ========================================================
    # Initial Flow
    # ========================================================

    graph.add_edge(
        START,
        "classify_request"
    )

    graph.add_edge(
        "classify_request",
        "assess_priority"
    )

    graph.add_edge(
        "assess_priority",
        "decide_next_step"
    )

    # ========================================================
    # Conditional Decision Routing
    # ========================================================

    graph.add_conditional_edges(
        "decide_next_step",
        route_decision,
        {
            "retrieve_knowledge": "retrieve_knowledge",
            "ask_clarification": "ask_clarification",
            "create_ticket": "create_ticket",
        }
    )

    # ========================================================
    # All Paths → Response
    # ========================================================

    graph.add_edge(
        "retrieve_knowledge",
        "generate_response"
    )

    graph.add_edge(
        "ask_clarification",
        "generate_response"
    )

    graph.add_edge(
        "create_ticket",
        "generate_response"
    )

    # ========================================================
    # End
    # ========================================================

    graph.add_edge(
        "generate_response",
        END
    )

    return graph.compile()