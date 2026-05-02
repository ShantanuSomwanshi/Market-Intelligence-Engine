from ..services import get_provider
from ..state import DecisionMaker, RunState, set_report_section


async def run(state: RunState) -> RunState:
    provider = get_provider()
    people = state.research_context.get("public_people", [])
    decision_makers: list[DecisionMaker] = []

    for item in people[:5]:
        decision_makers.append(
            DecisionMaker(
                name=item.get("name", ""),
                role_title=item.get("role_title", "Marketing Lead"),
                role_relevance=item.get("role_relevance", "Relevant go-to-market stakeholder."),
                source_url=item.get("source_url", ""),
                confidence=item.get("confidence", 0.0),
            )
        )

    if not decision_makers:
        decision_makers = provider.derive_decision_roles(state.input.category_description)

    set_report_section(state, "decision_makers", [item.model_dump() for item in decision_makers])
    return state
