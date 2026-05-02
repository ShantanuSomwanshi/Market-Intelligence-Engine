from ..services import get_provider
from ..state import RunState, set_report_section


async def run(state: RunState) -> RunState:
    provider = get_provider()
    evidence = state.research_context.get("evidence", [])
    sentiment = state.research_context.get("sentiment", {"label": "neutral", "compound_score": 0.0})
    fallback = {
        "brand_perception": f"{state.input.company_name} appears {state.research_context.get('profile', {}).get('positioning', 'category-relevant')}.",
        "recent_shifts": [item.get("snippet", "") for item in evidence[:2] if item.get("snippet")],
        "sentiment_summary": sentiment,
        "evidence": evidence[:5],
    }
    payload = await provider.reason_json(
        "Create the market_position section. Focus on brand perception, recent shifts, and sentiment.",
        {
            "company_name": state.input.company_name,
            "evidence": evidence,
            "sentiment": sentiment,
        },
        fallback,
    )
    set_report_section(state, "market_position", payload)
    return state
