from ..services import get_provider
from ..state import RunState, append_event


async def run(state: RunState) -> RunState:
    provider = get_provider()
    state.research_context = await provider.gather_research(
        state.input.company_name,
        state.input.category_description,
    )
    append_event(
        state,
        "research_complete",
        "Research bundle gathered.",
        mode=state.research_context.get("mode", "unknown"),
    )
    return state
