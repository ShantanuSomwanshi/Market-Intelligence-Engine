from ..services import get_provider
from ..state import RunState, set_report_section


async def run(state: RunState) -> RunState:
    provider = get_provider()
    profile = state.research_context.get("profile", {})
    fallback = {
        "business_model": profile.get("business_model", "Unknown"),
        "company_scale": {
            "estimated_employee_band": "unknown",
            "geographic_presence": [],
        },
        "positioning": f"{state.input.company_name} is positioned in {state.input.category_description}.",
        "key_offerings": [state.input.category_description],
        "source_facts": state.research_context.get("evidence", [])[:3],
    }
    payload = await provider.reason_json(
        "Create the company_overview section using business model, scale, positioning, and key_offerings.",
        {
            "company_name": state.input.company_name,
            "category_description": state.input.category_description,
            "research_context": state.research_context,
        },
        fallback,
    )
    set_report_section(state, "company_overview", payload)
    return state
