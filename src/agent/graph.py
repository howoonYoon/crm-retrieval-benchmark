"""Build the bounded CRM troubleshooting graph."""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from agent.execute_mcp import create_execute_mcp_node
from agent.parse_request import parse_request
from agent.routing import route_after_decide
from agent.state import AgentState


def build_graph(
    decide: Any,
    mcp_client: Any,
):
    """Build and compile the CRM troubleshooting graph."""

    execute_mcp = create_execute_mcp_node(
        mcp_client
    )

    builder = StateGraph(AgentState)

    builder.add_node(
        "parse_request",
        parse_request,
    )
    builder.add_node(
        "decide",
        decide,
    )
    builder.add_node(
        "execute_mcp",
        execute_mcp,
    )

    builder.add_edge(
        START,
        "parse_request",
    )
    builder.add_edge(
        "parse_request",
        "decide",
    )

    builder.add_conditional_edges(
        "decide",
        route_after_decide,
        {
            "execute_mcp": "execute_mcp",
            "end": END,
        },
    )

    builder.add_edge(
        "execute_mcp",
        "decide",
    )

    return builder.compile()