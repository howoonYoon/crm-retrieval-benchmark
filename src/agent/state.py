"""State and structured result models for the bounded CRM agent."""

from typing import Annotated, Any, Literal, TypedDict
from pydantic import BaseModel, Field
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

FinalStatus = Literal[
    "needs_input",
    "answered",
    "cannot_verify",
]
ToolStatus = Literal[
    "success",
    "empty",
    "tool_error",
    "timeout",
    "invalid_schema",
    "rejected"
]
EvidenceType = Literal[
    "document",
    "case",
    "metadata",
    "log"
]


class ToolCallRecord(BaseModel):
    tool_name: str
    arguments: dict[str, Any]
    status: ToolStatus
    error: str | None = None

class Evidence(BaseModel):
    evidence_type: EvidenceType
    summary: str
    source_ref: str
    data: dict[str,Any] = Field(default_factory=dict)

class Source(BaseModel):
    title: str
    reference: str

class AgentAnswer(BaseModel):
    status: FinalStatus
    confirmed_facts: list[str] = Field(default_factory=list) #근거로 확인된 사실
    possible_causes: list[str] = Field(default_factory=list) #가능성이 있지만 확정되지 않은 원인
    unverified_items: list[str] = Field(default_factory=list) #확인하지 못한 정보
    recommended_steps: list[str] = Field(default_factory=list) # 문제 해결을 위해 권장하는 작업
    sources: list[Source] = Field(default_factory=list) #근거 출처
    message: str | None = None # 사용자에게 보여줄 간단한 설명

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage],add_messages]
    
    case_id: str |None
    evidence: list[dict[str,Any]]

    attempted_calls: set[str]
    tool_call_count: int

    answer: AgentAnswer | None
