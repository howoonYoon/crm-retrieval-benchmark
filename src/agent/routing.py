"""Conditional routing for the LangGraph agent."""

from __future__ import annotations
from typing import Literal
from langchain_core.messages import AIMessage
from agent.state import AgentState


def route_after_decide(
    state: AgentState,
) -> Literal["execute_mcp", "end"]:
    """Route tool calls to execution and text responses to end."""

    if not state["messages"]:
        raise RuntimeError("No messages after decide node")

    last_message = state["messages"][-1]

    if (
        isinstance(last_message, AIMessage)
        and last_message.tool_calls
    ):
        return "execute_mcp"

    return "end"