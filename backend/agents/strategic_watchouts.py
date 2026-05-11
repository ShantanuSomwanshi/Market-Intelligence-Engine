from ..state import RunState, set_report_section


async def run(state: RunState) -> RunState:
    profile = state.research_context.get("profile", {})
    competitors = state.report.get("competitor_mapping", [])
    contacts = state.report.get("contact_intelligence", [])
    verified_contacts = [
        contact
        for contact in contacts
        if contact.get("overall_status") in {"verified_contactable", "verified_partial"}
    ]
    category = state.input.category_description.lower()

    risks = [
        f"Messaging may need stronger proof around {profile.get('message_shift', 'recent narrative shifts')}.",
        f"Competitive pressure is visible from {len(competitors) or 'multiple'} comparable players, so outreach should avoid generic category claims.",
    ]
    if not verified_contacts:
        risks.append("Verified contact coverage is limited; use role-based outreach planning until a public contact route is confirmed.")
    if any(term in category for term in ["crm", "marketing automation", "saas", "software", "platform"]):
        risks.append("Feature parity is likely high, so the strongest pitch angle should connect positioning to measurable revenue or workflow outcomes.")
    elif any(term in category for term in ["event", "exhibition", "activation", "roadshow", "experiential"]):
        risks.append("Proof through case studies, production quality, and measurable event outcomes will matter more than broad creative claims.")
    elif any(term in category for term in ["retail", "consumer", "fashion", "sportswear"]):
        risks.append("Brand differentiation and cultural relevance can shift quickly, so recent campaign evidence should guide the outreach angle.")

    insights = [
        "Lead outreach with visible public facts only.",
        "Use competitor contrast to make the opening message feel specific rather than templated.",
    ]
    if verified_contacts:
        insights.append("Prioritize the verified public contact route first, then expand to role-based stakeholders if no response.")
    else:
        insights.append("Start with role-relevant stakeholders and keep contact fields transparent until a verified source returns data.")

    set_report_section(
        state,
        "strategic_watchouts",
        {
            "risks_tensions_blindspots": risks[:5],
            "pre_engagement_insights": insights[:4],
        },
    )
    return state
