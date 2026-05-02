from ..services import get_provider
from ..state import DecisionMaker, RunState, set_report_section


async def run(state: RunState) -> RunState:
    provider = get_provider()
    evidence = state.research_context.get("evidence", [])
    facts = [item.get("snippet", "") or item.get("title", "") for item in evidence[:3] if item]
    evidence_refs = [
        {
            "title": item.get("title", ""),
            "snippet": item.get("snippet", ""),
            "source_url": item.get("source_url", ""),
            "source_type": item.get("source_type", ""),
        }
        for item in evidence[:3]
    ]
    decision_makers = [
        DecisionMaker.model_validate(item)
        for item in state.report.get("decision_makers", [])
    ]
    outreach = [
        provider.build_outreach(state.input.company_name, person, facts, evidence_refs)
        for person in decision_makers
    ]
    set_report_section(state, "personalized_outreach", outreach)
    return state
