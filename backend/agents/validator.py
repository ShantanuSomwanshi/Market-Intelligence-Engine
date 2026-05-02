from ..config import get_settings
from ..state import (
    REPORT_SECTIONS,
    ContactRecord,
    RunState,
    ValidationIssue,
    append_event,
    clear_retry,
    increment_retry,
)


async def run(state: RunState) -> RunState:
    clear_retry(state)
    issues: list[ValidationIssue] = []
    max_retries = get_settings().max_validator_retries

    for section in REPORT_SECTIONS:
        if section not in state.report:
            issues.append(ValidationIssue(target_node=_section_to_node(section), reason=f"Missing section: {section}"))

    for item in state.report.get("contact_intelligence", []):
        record = ContactRecord.model_validate(item)
        for field_name in ["email", "phone", "linkedin_url"]:
            field = getattr(record, field_name)
            if field.status == "verified" and not field.value:
                issues.append(
                    ValidationIssue(
                        target_node="contact_intelligence",
                        reason=f"Verified field missing value for {record.person_name or record.role_title}: {field_name}",
                    )
                )

    supported_facts = {
        item.get("snippet", "") or item.get("title", "")
        for item in state.research_context.get("evidence", [])
    }
    for item in state.report.get("personalized_outreach", []):
        for fact in item.get("fact_references", []):
            if fact and fact not in supported_facts:
                issues.append(
                    ValidationIssue(
                        target_node="outreach_generation",
                        reason=f"Unsupported outreach fact reference: {fact}",
                    )
                )

    state.validation_issues = issues
    if issues:
        issue = issues[0]
        if state.retry_counts.get(issue.target_node, 0) < max_retries:
            increment_retry(state, issue.target_node, issue.reason)
        else:
            state.low_confidence = True
            state.errors.append(f"Retry budget exhausted for {issue.target_node}: {issue.reason}")
            append_event(state, "validator_exhausted", issue.reason, target_node=issue.target_node)
        return state

    append_event(state, "validator_passed", "All required sections and validation checks passed.")
    return state


def _section_to_node(section_name: str) -> str:
    mapping = {
        "company_overview": "company_overview",
        "market_position": "market_position",
        "competitor_mapping": "competitor_mapping",
        "brand_activity": "brand_activity",
        "events_footprint": "events_footprint",
        "strategic_watchouts": "strategic_watchouts",
        "decision_makers": "decision_makers",
        "contact_intelligence": "contact_intelligence",
        "personalized_outreach": "outreach_generation",
        "outreach_tracking_logic": "tracking_logic",
    }
    return mapping.get(section_name, "validator")
