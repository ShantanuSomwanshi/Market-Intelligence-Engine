from ..services import get_provider
from ..state import DecisionMaker, RunState, set_report_section


async def run(state: RunState) -> RunState:
    provider = get_provider()
    decision_makers = [
        DecisionMaker.model_validate(item)
        for item in state.report.get("decision_makers", [])
    ]
    contacts = await provider.enrich_contacts(
        decision_makers,
        state.research_context.get("company_domain", ""),
    )
    set_report_section(state, "contact_intelligence", [item.model_dump() for item in contacts])
    return state
