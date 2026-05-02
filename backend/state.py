from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


NodeStatus = Literal["waiting", "running", "completed", "failed", "retrying"]
RunStatus = Literal["idle", "queued", "running", "completed", "failed"]

REPORT_SECTIONS = [
    "company_overview",
    "market_position",
    "competitor_mapping",
    "brand_activity",
    "events_footprint",
    "strategic_watchouts",
    "decision_makers",
    "contact_intelligence",
    "personalized_outreach",
    "outreach_tracking_logic",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class EvidenceItem(BaseModel):
    title: str
    snippet: str
    source_url: str
    source_type: str
    published_at: str = ""
    confidence: float = 0.5


class ContactField(BaseModel):
    value: str = ""
    status: Literal["verified", "not_found"] = "not_found"
    confidence: float = 0.0
    source: str = ""
    trust_state: Literal["verified", "not_found", "rejected"] = "not_found"


class DecisionMaker(BaseModel):
    name: str = ""
    role_title: str
    role_relevance: str
    source_url: str = ""
    confidence: float = 0.0


class ContactRecord(BaseModel):
    person_name: str
    role_title: str
    email: ContactField = Field(default_factory=ContactField)
    phone: ContactField = Field(default_factory=ContactField)
    linkedin_url: ContactField = Field(default_factory=ContactField)
    overall_status: Literal["verified_partial", "verified_contactable", "not_found"] = "not_found"
    verification_notes: List[str] = Field(default_factory=list)


class ValidationIssue(BaseModel):
    target_node: str
    reason: str
    severity: Literal["warning", "error"] = "error"


class NodeSnapshot(BaseModel):
    id: str
    label: str
    status: NodeStatus = "waiting"
    detail: str = ""
    retries: int = 0
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class RunInput(BaseModel):
    company_name: str = Field(..., min_length=1)
    category_description: str = Field(..., min_length=1)


class RunState(BaseModel):
    run_id: str
    input: RunInput
    started_at: str = Field(default_factory=utc_now)
    updated_at: str = Field(default_factory=utc_now)
    status: RunStatus = "queued"
    nodes: List[NodeSnapshot] = Field(default_factory=list)
    research_context: Dict[str, Any] = Field(default_factory=dict)
    report: Dict[str, Any] = Field(default_factory=dict)
    tracking: Dict[str, Any] = Field(default_factory=dict)
    derived_insights: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    event_log: List[Dict[str, Any]] = Field(default_factory=list)
    validation_issues: List[ValidationIssue] = Field(default_factory=list)
    retry_counts: Dict[str, int] = Field(default_factory=dict)
    current_node_id: Optional[str] = None
    retry_target: Optional[str] = None
    retry_reason: str = ""
    low_confidence: bool = False


class RunSummary(BaseModel):
    run_id: str
    company_name: str
    category_description: str
    status: str
    created_at: str
    updated_at: str
    output_path: Optional[str] = None


def append_event(run: RunState, event_type: str, message: str, **extra: Any) -> RunState:
    run.updated_at = utc_now()
    event = {"type": event_type, "message": message, "timestamp": run.updated_at}
    event.update(extra)
    run.event_log.append(event)
    return run


def get_node(run: RunState, node_id: str) -> Optional[NodeSnapshot]:
    for node in run.nodes:
        if node.id == node_id:
            return node
    return None


def update_node_status(run: RunState, node_id: str, status: NodeStatus, detail: str = "") -> RunState:
    node = get_node(run, node_id)
    if node is None:
        return append_event(run, "node_missing", f"Node '{node_id}' does not exist.")

    now = utc_now()
    node.status = status
    node.detail = detail
    run.current_node_id = node_id
    run.updated_at = now

    if status == "running":
        node.started_at = now
    if status in {"completed", "failed"}:
        node.completed_at = now

    run.event_log.append(
        {
            "type": "node_status",
            "node_id": node_id,
            "status": status,
            "detail": detail,
            "timestamp": now,
        }
    )
    return run


def increment_retry(run: RunState, node_id: str, reason: str) -> RunState:
    run.retry_counts[node_id] = run.retry_counts.get(node_id, 0) + 1
    node = get_node(run, node_id)
    if node is not None:
        node.retries = run.retry_counts[node_id]
        node.status = "retrying"
        node.detail = reason
    run.retry_target = node_id
    run.retry_reason = reason
    return append_event(run, "retry_scheduled", reason, target_node=node_id, attempt=run.retry_counts[node_id])


def clear_retry(run: RunState) -> RunState:
    run.retry_target = None
    run.retry_reason = ""
    run.validation_issues = []
    return run


def set_report_section(run: RunState, section_name: str, payload: Any) -> RunState:
    run.report[section_name] = payload
    run.updated_at = utc_now()
    return run


def ensure_report_shape(run: RunState) -> Dict[str, Any]:
    return {section: run.report.get(section) for section in REPORT_SECTIONS}
