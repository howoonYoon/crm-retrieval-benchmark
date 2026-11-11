
"""Convert MCP tool results into Evidence objects."""

from typing import Any

from agent.state import Evidence


def normalize_evidence(
    tool_name: str,
    data: dict[str, Any],
) -> list[Evidence]:
    """Normalize a successful MCP response."""

    if data.get("status") != "ok":
        raise ValueError("MCP result status is not 'ok'.")

    if tool_name == "search_documents":
        documents = data.get("evidence")

        if not isinstance(documents, list):
            raise ValueError("Missing document evidence.")

        return [
            Evidence(
                evidence_type="document",
                summary=str(doc.get("excerpt", "")),
                source_ref=str(
                    doc.get("source_ref")
                    or doc.get("url")
                    or doc.get("doc_id")
                    or "unknown"
                ),
                data=doc,
            )
            for doc in documents
            if isinstance(doc, dict)
        ]

    if tool_name == "get_case_record":
        record = data.get("record")

        if not isinstance(record, dict):
            raise ValueError("Missing Case record.")

        return [
            Evidence(
                evidence_type="case",
                summary=(
                    f"Case {record.get('CaseNumber', '')}: "
                    f"status={record.get('Status', 'unknown')}, "
                    f"priority={record.get('Priority', 'unknown')}"
                ),
                source_ref=str(record.get("Id", "unknown")),
                data=record,
            )
        ]

    if tool_name == "get_case_metadata":
        metadata = data.get("object")

        if not isinstance(metadata, dict):
            raise ValueError("Missing Case metadata.")

        return [
            Evidence(
                evidence_type="metadata",
                summary="Salesforce Case object metadata.",
                source_ref="salesforce:Case:describe",
                data=metadata,
            )
        ]

    if tool_name == "get_error_logs":
        logs = data.get("logs")

        if not isinstance(logs, list):
            raise ValueError("Missing error logs.")

        return [
            Evidence(
                evidence_type="log",
                summary=str(log.get("message", "")),
                source_ref=str(log.get("log_id", "unknown")),
                data=log,
            )
            for log in logs
            if isinstance(log, dict)
        ]

    raise ValueError(f"Unsupported MCP tool: {tool_name}")
