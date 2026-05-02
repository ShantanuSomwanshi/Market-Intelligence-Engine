from ..state import RunState, set_report_section


def _competitors(category: str) -> list[dict]:
    text = category.lower()
    if any(term in text for term in ["saas", "software", "platform", "productivity"]):
        names = ["Asana", "Monday.com", "ClickUp", "Airtable"]
    elif any(term in text for term in ["retail", "consumer", "fashion", "ecommerce"]):
        names = ["Nike", "Adidas", "Puma", "Lululemon"]
    elif any(term in text for term in ["health", "biotech", "medical", "pharma"]):
        names = ["Moderna", "Pfizer", "BioNTech", "Novavax"]
    else:
        names = ["Incumbent Leader", "Category Challenger", "Performance-First Rival", "Brand-Led Rival"]

    return [
        {
            "competitor_name": name,
            "brand_activity": ["Visible campaign and launch activity in category"],
            "strengths": ["Category recognition", "Clear messaging"],
            "gaps_vs_target": ["Potential room for sharper differentiation"],
            "relative_position": "Benchmark competitor derived from category archetype",
        }
        for name in names[:4]
    ]


async def run(state: RunState) -> RunState:
    set_report_section(state, "competitor_mapping", _competitors(state.input.category_description))
    return state
