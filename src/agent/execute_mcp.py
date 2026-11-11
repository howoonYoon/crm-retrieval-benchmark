
"""Validate and execute MCP tool calls."""
# MCP Tool 실행 후 결과를 LangGraph의 AgentState 에 반영하도록 반환

import asyncio
import json
from typing import Any, Callable

from langchain_core.messages import AIMessage, ToolMessage

from agent.mcp_client import MCPClient
from agent.normalize_evidence import normalize_evidence
from agent.state import AgentState, Evidence, ToolCallRecord


MAX_TOOL_CALLS = 4
TOOL_TIMEOUT_SECONDS = 10

CASE_ID_TOOLS = {
    "get_case_record",
    "get_error_logs",
}

# 중복 호출 구분
def make_call_key(name: str, args: dict) -> str:
    """Create a unique key for duplicate detection."""
    return json.dumps(
        {"tool": name, "arguments": args},
        sort_keys=True,
        ensure_ascii=False,
    ) #json 문자열 생성


# tool 실행 결과를 state 업데이트로 변환
def build_result(
    state: AgentState,
    call: dict, # llm 이 요청한 tool call
    status: str, # 실행결과 상태
    data: Any = None, #서버에서 반환한 데이터
    error: str | None = None,
    evidence: list[Evidence] | None = None,
    attempted: bool = True,
) -> dict[str, Any]:
    """Build a ToolMessage and State update."""

    name = call["name"]
    args = call.get("args", {})

    record = ToolCallRecord(
        tool_name=name,
        arguments=args,
        status=status,
        error=error,
    )

    # 실제 도구 실행 결과를 LLM 에게 전달하기 위한 메시지
    message = ToolMessage(
        content=json.dumps(
            {
                "status": status,
                "data": data,
                "error": error,
            },
            ensure_ascii=False,
            default=str,
        ),
        tool_call_id=call["id"], #LLM이 요청한 Tool call
    )

    updates = {
        "messages": [message],
        "tool_calls": [
            *state.get("tool_calls", []),
            record,
        ],
        "tool_call_count": min(
            MAX_TOOL_CALLS,
            state["tool_call_count"] + 1,
        ),
    }

    if attempted:
        updates["attempted_calls"] = {
            *state["attempted_calls"],
            make_call_key(name, args),
        }

    if evidence:
        updates["evidence"] = [
            *state["evidence"],
            *evidence,
        ]

    return updates


# LangGraph 노드 생성
def create_execute_mcp_node(
    mcp_client: MCPClient,
) -> Callable:
    """Create a LangGraph MCP execution node."""

    async def execute_mcp(
        state: AgentState,
    ) -> dict[str, Any]:

        # 1. Get the LLM's tool call
        last_message = state["messages"][-1]

        if not isinstance(last_message, AIMessage):
            raise RuntimeError("Expected AIMessage.")

        calls = last_message.tool_calls

        if not calls:
            raise RuntimeError("No tool call to execute.")

        # 2. Reject multiple tool calls
        if len(calls) > 1:
            results = [
                build_result(
                    state,
                    call,
                    status="rejected",
                    error="Only one tool call is allowed.",
                    attempted=False,
                )
                for call in calls
            ]

            return {
                "messages": [
                    r["messages"][0] for r in results
                ],
                "tool_calls": [
                    *state.get("tool_calls", []),
                    *[
                        r["tool_calls"][-1]
                        for r in results
                    ],
                ],
                "tool_call_count": min(
                    MAX_TOOL_CALLS,
                    state["tool_call_count"] + len(calls),
                ),
            }

        call = calls[0]
        name = call["name"]
        args = call.get("args", {})

        # 3. Check tool call limit
        if state["tool_call_count"] >= MAX_TOOL_CALLS:
            result = build_result(
                state,
                call,
                status="rejected",
                error="Tool call limit reached.",
                attempted=False,
            )
            result["tool_call_count"] = state["tool_call_count"]
            return result

        # 4. Block duplicate calls
        call_key = make_call_key(name, args)

        if call_key in state["attempted_calls"]:
            return build_result(
                state,
                call,
                status="rejected",
                error="Duplicate tool call.",
                attempted=False,
            )

        # 5. Validate Case ID
        if name in CASE_ID_TOOLS:
            case_id = state["case_id"]

            if case_id is None:
                return build_result(
                    state,
                    call,
                    status="rejected",
                    error="Case ID required. Ask the user.",
                )

            if args.get("case_id") != case_id:
                return build_result(
                    state,
                    call,
                    status="rejected",
                    error="Case ID mismatch.",
                )

        # 6. Execute MCP tool
        try:
            result = await asyncio.wait_for(
                mcp_client.call_tool(name, args),
                timeout=TOOL_TIMEOUT_SECONDS,
            )

            if result.is_error:
                return build_result(
                    state,
                    call,
                    status="tool_error",
                    error=str(result.content),
                )

            data = result.structured_content

            if not isinstance(data, dict):
                raise ValueError(
                    "MCP result has no structured content."
                )

            # 7. Normalize evidence
            evidence = normalize_evidence(name, data)

            return build_result(
                state,
                call,
                status="success" if evidence else "empty",
                data=data,
                evidence=evidence,
            )

        except TimeoutError:
            return build_result(
                state,
                call,
                status="timeout",
                error="MCP tool execution timed out.",
            )

        except ValueError as exc:
            return build_result(
                state,
                call,
                status="invalid_schema",
                error=str(exc),
            )

        except Exception as exc:
            return build_result(
                state,
                call,
                status="tool_error",
                error=str(exc),
            )

    return execute_mcp
