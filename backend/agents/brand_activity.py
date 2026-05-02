from ..state import RunState, set_report_section


async def run(state: RunState) -> RunState:
    evidence = state.research_context.get("evidence", [])
    activities = []
    for item in evidence[:4]:
        activities.append(
            {
                "title": item.get("title", "Public company signal"),
                "type": "campaign_or_launch_signal",
                "date": item.get("published_at", ""),
                "summary": item.get("snippet", ""),
                "source_url": item.get("source_url", ""),
            }
        )
    set_report_section(
        state,
        "brand_activity",
        {
            "time_window_months": 24,
            "campaigns_launches": activities,
            "communications_patterns": [
                "Messaging reflects visible public signals and recent coverage.",
                "Narrative emphasizes value communication and market differentiation.",
            ],
        },
    )
    return state
