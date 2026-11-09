"""Launch the local MCP server and verify a real stdio connection."""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from mcp import Client, StdioServerParameters


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = PROJECT_ROOT / "src" / "mcp_server.py"
EXPECTED_SERVER_NAME = "salesforce-crm-troubleshooting"
EXPECTED_TOOLS = {
    "search_documents",
    "get_case_record",
    "get_case_metadata",
    "get_error_logs",
}
MOCK_CASE_ID = "500000000000001AAA"
CALL_TIMEOUT_SECONDS = 20


async def call_tool(client: Client, name: str, arguments: dict[str, Any]):
    """Call one tool with a hard client-side timeout."""
    return await asyncio.wait_for(
        client.call_tool(name, arguments),
        timeout=CALL_TIMEOUT_SECONDS,
    )


async def confirm_invalid_args(
    client: Client,
    name: str,
    arguments: dict[str, Any],
) -> bool:
    """Return true only when the server rejects invalid tool arguments."""
    try:
        result = await call_tool(client, name, arguments)
    except Exception:
        return True
    return bool(result.is_error)


async def run_smoke_test() -> dict[str, Any]:
    """Verify initialization, discovery, schemas, calls, and validation over stdio."""
    
    # StdioServerParameters: stdio 방식으로 MCP 서버 실행할때 필요한 설정
    server = StdioServerParameters(
        command=sys.executable, #실행중인 Python interpreter 로 실행
        args=[str(SERVER_PATH)],
        cwd=PROJECT_ROOT,
    )

    async with Client(server, read_timeout_seconds=CALL_TIMEOUT_SECONDS) as client:
        # Entering Client performs MCP initialization and protocol negotiation.
        server_info = client.server_info
        if server_info is None:
            raise RuntimeError("The MCP server did not provide identification metadata.")
        if server_info.name != EXPECTED_SERVER_NAME:
            raise RuntimeError(
                f"Connected to unexpected MCP server: {server_info.name!r}"
            )

        listed = await asyncio.wait_for(
            client.list_tools(),
            timeout=CALL_TIMEOUT_SECONDS,
        )
        tools_by_name = {tool.name: tool for tool in listed.tools}
        if set(tools_by_name) != EXPECTED_TOOLS:
            raise RuntimeError(f"Unexpected MCP tools: {sorted(tools_by_name)}")

        search_schema = tools_by_name["search_documents"].input_schema
        case_schema = tools_by_name["get_case_record"].input_schema
        schema_checks = {
            "query_required": search_schema.get("required") == ["query"],
            "top_k_range": search_schema["properties"]["top_k"].get("minimum") == 1
            and search_schema["properties"]["top_k"].get("maximum") == 10,
            "strategy_allowlist": search_schema["properties"]["strategy"].get("enum")
            == ["bm25", "dense", "hybrid_rrf"],
            "case_id_allowlist": case_schema["properties"]["case_id"].get("const")
            == MOCK_CASE_ID,
        }
        if not all(schema_checks.values()):
            raise RuntimeError(f"MCP schema validation failed: {schema_checks}")

        search_result = await call_tool(
            client,
            "search_documents",
            {
                "query": "Email-to-Case routing address",
                "top_k": 1,
                "strategy": "bm25",
            },
        )
        case_result = await call_tool(
            client,
            "get_case_record",
            {"case_id": MOCK_CASE_ID},
        )
        metadata_result = await call_tool(client, "get_case_metadata", {})
        logs_result = await call_tool(
            client,
            "get_error_logs",
            {"case_id": MOCK_CASE_ID},
        )
        successful_results = (
            search_result,
            case_result,
            metadata_result,
            logs_result,
        )
        if any(result.is_error for result in successful_results):
            raise RuntimeError("At least one valid MCP tool call failed")

        mock_checks = {
            "case_record": case_result.structured_content.get("is_mock") is True,
            "case_metadata": metadata_result.structured_content.get("is_mock") is True,
            "error_logs": logs_result.structured_content.get("is_mock") is True,
        }
        if not all(mock_checks.values()):
            raise RuntimeError(f"Mock markers are missing: {mock_checks}")

        invalid_args = {
            "missing_query": await confirm_invalid_args(
                client, "search_documents", {"strategy": "bm25"}
            ),
            "top_k_below_minimum": await confirm_invalid_args(
                client,
                "search_documents",
                {"query": "Case", "top_k": 0, "strategy": "bm25"},
            ),
            "top_k_above_maximum": await confirm_invalid_args(
                client,
                "search_documents",
                {"query": "Case", "top_k": 11, "strategy": "bm25"},
            ),
            "strategy_not_allowlisted": await confirm_invalid_args(
                client,
                "search_documents",
                {"query": "Case", "strategy": "unsupported"},
            ),
            "case_id_not_allowlisted": await confirm_invalid_args(
                client,
                "get_case_record",
                {"case_id": "500000000000999AAA"},
            ),
        }
        if not all(invalid_args.values()):
            raise RuntimeError(f"Invalid arguments were accepted: {invalid_args}")

        return {
            "status": "ok",
            "initialize": {
                "server_name": server_info.name,
                "server_version": server_info.version,
                "protocol_version": str(client.protocol_version),
            },
            "tools_list": sorted(tools_by_name),
            "schema_checks": schema_checks,
            "tools_call": {
                "search_documents_evidence": len(
                    search_result.structured_content["evidence"]
                ),
                "case_record": "ok",
                "case_metadata": "ok",
                "error_logs": logs_result.structured_content["count"],
            },
            "invalid_args": invalid_args,
            "mock_checks": mock_checks,
            "call_timeout_seconds": CALL_TIMEOUT_SECONDS,
        }


def main() -> None:
    """Run the smoke test and emit one machine-readable result."""
    print(json.dumps(asyncio.run(run_smoke_test()), ensure_ascii=False))


if __name__ == "__main__":
    main()
