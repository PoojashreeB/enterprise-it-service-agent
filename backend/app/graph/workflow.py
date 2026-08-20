from langgraph.graph import StateGraph, START, END

from app.graph.state import ServiceDeskState

from app.agents.service_desk_agent import (
    classify_request,
    assess_priority,
    run_agent,
)


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
        "run_agent",
        run_agent
    )

    # ========================================================
    # Flow
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
        "run_agent"
    )

    graph.add_edge(
        "run_agent",
        END
    )

    return graph.compile()
