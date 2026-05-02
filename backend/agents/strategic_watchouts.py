from ..state import RunState, set_report_section


async def run(state: RunState) -> RunState:
    profile = state.research_context.get("profile", {})
    set_report_section(
        state,
        "strategic_watchouts",
        {
            "risks_tensions_blindspots": [
                f"Messaging may need stronger proof around {profile.get('message_shift', 'recent narrative shifts')}.",
                f"Competitive pressure may intensify because of {profile.get('competitive_frame', 'category crowding')}.",
                "Contact availability may remain sparse without richer public signals or Apollo matches.",
            ],
            "pre_engagement_insights": [
                "Lead outreach with visible public facts only.",
                "Anchor the pitch in positioning clarity, competitor contrast, and execution speed.",
            ],
        },
    )
    return state
