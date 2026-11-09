"""Local stdio entry point for the CRM retrieval MCP server."""

import logging
import sys
from typing import Annotated, Any, Literal

from mcp.server import MCPServer
from pydantic import Field

from crm_mock_data import (
    get_case_metadata as load_case_metadata,
    get_case_record as load_case_record,
    get_error_logs as load_error_logs,
)
from search_documents import search_documents as run_document_search


TopK = Annotated[int, Field(ge=1, le=10)]
MockCaseId = Literal["500000000000001AAA"]


mcp = MCPServer(
    name="salesforce-crm-troubleshooting",
    version="0.1.0",
    description="Provides tools for diagnosing Salesforce CRM Case issues using documentation retrieval, Case records, field metadata, and error logs. Supports read-only troubleshooting.",
)


@mcp.tool()
def search_documents(
    query: str,
    top_k: TopK = 5,
    strategy: Literal["bm25", "dense", "hybrid_rrf"] = "hybrid_rrf",
) -> dict[str, Any]:
    """Search the local Salesforce documentation corpus for troubleshooting evidence."""
    return run_document_search(query=query, top_k=top_k, strategy=strategy)


@mcp.tool()
def get_case_record(case_id: MockCaseId) -> dict[str, Any]:
    """Get a read-only mock Salesforce Case record by its Case ID."""
    return load_case_record(case_id)


@mcp.tool()
def get_case_metadata() -> dict[str, Any]:
    """Get read-only mock Salesforce field metadata for the Case object."""
    return load_case_metadata()


@mcp.tool()
def get_error_logs(case_id: MockCaseId) -> dict[str, Any]:
    """Get read-only mock diagnostic logs associated with a Salesforce Case ID."""
    return load_error_logs(case_id)


def main() -> None:
    """Run the server over stdin/stdout until the client disconnects."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
        force=True,
    )
    logging.getLogger(__name__).info("Starting MCP server over stdio")
    mcp.run(transport="stdio") # stdio : 표준입출력 사용해서 메세지 주고받음


if __name__ == "__main__":
    main()
