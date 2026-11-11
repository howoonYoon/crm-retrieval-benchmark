"""Parse a user request before the agent selects an MCP tool."""

from __future__ import annotations

import re
from typing import Any

from langchain_core.messages import HumanMessage

from agent.state import AgentAnswer, AgentState


# Salesforce Case ID는 500으로 시작하는 15자 또는 18자 ID
CASE_ID_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])"
    r"(500[A-Za-z0-9]{12}(?:[A-Za-z0-9]{3})?)"
    r"(?![A-Za-z0-9])"
)


def get_latest_user_text(state: AgentState) -> str:
    """Return the latest non-empty user message."""

    for message in reversed(state["messages"]):
        if not isinstance(message, HumanMessage):
            continue

        if isinstance(message.content, str):
            text = message.content.strip()

            if text:
                return text

    return ""


def extract_case_id(text: str) -> str | None:
    """Extract a Salesforce Case ID from text."""

    match = CASE_ID_PATTERN.search(text)

    if match is None:
        return None

    return match.group(1)



def parse_request(state: AgentState) -> dict[str, Any]:
    """Extract request data and request a missing Case ID when necessary."""

    question = get_latest_user_text(state)

    if not question:
        return {
            "case_id": None,
            "answer": AgentAnswer(
                status="needs_input",
                message="확인할 질문을 입력해 주세요.",
            ),
        }

    return {
        "case_id": extract_case_id(question),
        "answer": None,
    }