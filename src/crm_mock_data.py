"""Deterministic read-only CRM fixtures used until a Salesforce adapter exists."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


MOCK_CASE_ID = "500000000000001AAA"

_CASE_RECORDS: dict[str, dict[str, Any]] = {
    MOCK_CASE_ID: {
        "Id": MOCK_CASE_ID,
        "CaseNumber": "00001042",
        "Subject": "Email-to-Case message did not create the expected Case",
        "Status": "New",
        "Priority": "High",
        "Origin": "Email",
        "AccountId": "001000000000001AAA",
        "ContactId": "003000000000001AAA",
        "OwnerId": "005000000000001AAA",
        "CreatedDate": "2026-11-09T08:42:13Z",
        "LastModifiedDate": "2026-11-09T09:17:05Z",
    }
}

_CASE_FIELDS: list[dict[str, Any]] = [
    {"name": "Id", "label": "Case ID", "type": "id", "updateable": False},
    {
        "name": "CaseNumber",
        "label": "Case Number",
        "type": "string",
        "updateable": False,
    },
    {"name": "Subject", "label": "Subject", "type": "string", "updateable": True},
    {
        "name": "Status",
        "label": "Status",
        "type": "picklist",
        "updateable": True,
        "picklist_values": ["New", "Working", "Escalated", "Closed"],
    },
    {
        "name": "Priority",
        "label": "Priority",
        "type": "picklist",
        "updateable": True,
        "picklist_values": ["Low", "Medium", "High"],
    },
    {"name": "Origin", "label": "Case Origin", "type": "picklist", "updateable": True},
    {
        "name": "AccountId",
        "label": "Account ID",
        "type": "reference",
        "reference_to": ["Account"],
        "updateable": True,
    },
    {
        "name": "ContactId",
        "label": "Contact ID",
        "type": "reference",
        "reference_to": ["Contact"],
        "updateable": True,
    },
    {
        "name": "OwnerId",
        "label": "Owner ID",
        "type": "reference",
        "reference_to": ["User", "Group"],
        "updateable": True,
    },
    {
        "name": "CreatedDate",
        "label": "Created Date",
        "type": "datetime",
        "updateable": False,
    },
    {
        "name": "LastModifiedDate",
        "label": "Last Modified Date",
        "type": "datetime",
        "updateable": False,
    },
]

_ERROR_LOGS: dict[str, list[dict[str, Any]]] = {
    MOCK_CASE_ID: [
        {
            "log_id": "crm-log-0001",
            "timestamp": "2026-11-09T09:16:58Z",
            "level": "ERROR",
            "source": "RecordTriggeredFlow",
            "error_code": "FLOW_TRIGGER_FAILURE",
            "message": "Case_After_Save failed while updating the related Account.",
            "details": "The flow attempted an Account update without the required field access.",
        },
        {
            "log_id": "crm-log-0002",
            "timestamp": "2026-11-09T08:42:14Z",
            "level": "WARN",
            "source": "EmailToCase",
            "error_code": "ROUTING_ADDRESS_REVIEW",
            "message": "The inbound email routing address requires configuration review.",
            "details": "Verify routing-address activation and forwarding configuration.",
        },
    ]
}


def get_case_record(case_id: str) -> dict[str, Any]:
    """Return one mock Case record by Salesforce ID."""
    normalized_case_id = case_id.strip()
    if not normalized_case_id:
        raise ValueError("case_id must not be empty")
    if normalized_case_id not in _CASE_RECORDS:
        raise ValueError(f"Case record not found: {normalized_case_id}")

    return {
        "schema_version": "1.0",
        "status": "ok",
        "data_source": "mock",
        "is_mock": True,
        "record": deepcopy(_CASE_RECORDS[normalized_case_id]),
    }


def get_case_metadata() -> dict[str, Any]:
    """Return mock Salesforce describe metadata for the Case object."""
    return {
        "schema_version": "1.0",
        "status": "ok",
        "data_source": "mock",
        "is_mock": True,
        "object": {
            "api_name": "Case",
            "label": "Case",
            "queryable": True,
            "createable": True,
            "updateable": True,
            "fields": deepcopy(_CASE_FIELDS),
        },
    }


def get_error_logs(case_id: str) -> dict[str, Any]:
    """Return mock diagnostic log entries associated with a Case ID."""
    normalized_case_id = case_id.strip()
    if not normalized_case_id:
        raise ValueError("case_id must not be empty")
    if normalized_case_id not in _CASE_RECORDS:
        raise ValueError(f"Case record not found: {normalized_case_id}")

    logs = deepcopy(_ERROR_LOGS.get(normalized_case_id, []))
    return {
        "schema_version": "1.0",
        "status": "ok",
        "data_source": "mock",
        "is_mock": True,
        "case_id": normalized_case_id,
        "count": len(logs),
        "logs": logs,
    }
