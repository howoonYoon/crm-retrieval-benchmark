"""Let the model select the next MCP tool or produce a response."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from langchain_core.messages import SystemMessage

from agent.state import AgentState


SYSTEM_PROMPT = """
You are a bounded Salesforce CRM troubleshooting agent.

Use only the provided MCP tools.

Tool selection guidance:
- search_documents:
  Use for general Salesforce documentation and troubleshooting procedures.
- get_case_record:
  Use to inspect a specific Salesforce Case record.
- get_case_metadata:
  Use to inspect Case field definitions and updateability.
- get_error_logs:
  Use to inspect diagnostic logs for a specific Case.

Rules:
- Call at most one tool per response.
- Use only the tools necessary to answer the user's question.
- Never invent a Case ID.
- If a specific Case must be inspected but the extracted Case ID is missing,
  do not call a tool. Ask the user only for the Case ID.
- Do not repeat an identical tool call.
- If the existing evidence is sufficient, do not call another tool.
- If the required evidence cannot be obtained, explain that it cannot be
  verified.
- Never invent records, logs, facts, or sources.
"""


# MCP Tool → OpenAI Function Schema
def to_model_tool_schema(tool: Any) -> dict[str, Any]:
    """Convert one MCP tool definition into a model tool schema."""

    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.input_schema,
        },
    }


# 각 Evidence를 dictionary 로 변환
def serialize_evidence(state: AgentState) -> list[dict[str, Any]]:
    """Convert evidence into JSON-compatible dictionaries."""

    serialized = []

    for evidence in state["evidence"]:
        if hasattr(evidence, "model_dump"):
            serialized.append(evidence.model_dump())
        else:
            serialized.append(evidence)

    return serialized


#LangGraph에서 사용할 decide 노드를 생성하는 함수
#=>LLM이 현재까지 수집한 Evidence를 확인하고, 다음 MCP Tool을 호출할지 아니면 사용자에게 답변할지 결정
def create_decide_node(
    model: Any,
    mcp_tools: list[Any],
) -> Callable[[AgentState], Any]:
    """Create a decide node with discovered MCP tools bound to the model."""

    model_tool_schemas = [
        to_model_tool_schema(tool)
        for tool in mcp_tools
    ]

    model_with_tools = model.bind_tools(
        model_tool_schemas,
        tool_choice="auto",
        parallel_tool_calls=False
    ) # 도구 실행 요청 만들수 있도록 LLM 설정

    # 이렇게 내부에 만들면 decide 가 model_with_tools 계속 사용가능하고
    # LangGraph 실행될 때마다 bind_tools()를 다시 할 필요없음
    async def decide(state: AgentState) -> dict[str, Any]:
        context = {
            "case_id": state["case_id"],
            "tool_call_count": state["tool_call_count"],
            "tool_call_limit": 4,
            "attempted_calls": sorted(
                state["attempted_calls"]
            ),
            "evidence": serialize_evidence(state),
        }

        input_messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            SystemMessage(
                content=(
                    "Current runtime state:\n"
                    + json.dumps( #딕셔너리 json문자열로 변환
                        context,
                        ensure_ascii=False,
                        default=str,
                    )
                )
            ),
            *state["messages"],
        ]

        # 4회에 도달하면 tool을 bind하지 않은 모델로 답변만 생성한다.
        if state["tool_call_count"] >= 4:
            response = await model.ainvoke(input_messages) #바인딩하지 않은 LLM 호출 >> 추가 Tool call 없이 지금까지 수집한 evidence로 답변
        else:
            response = await model_with_tools.ainvoke(
                input_messages 
            ) # 바인딩된 LLM 호출

        # LangGraph 가 해당필드 업데이트
        return {
            "messages": [response],
        }

    return decide