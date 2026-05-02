from ..state import RunState, append_event, clear_retry


async def run(state: RunState) -> RunState:
    state.input.company_name = state.input.company_name.strip()
    state.input.category_description = state.input.category_description.strip()
    clear_retry(state)
    append_event(state, "input_ready", "Input normalized and ready for research.")
    return state
