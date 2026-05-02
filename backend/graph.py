from __future__ import annotations

from typing import Callable, Dict, List

from .agents import (
    brand_activity,
    company_overview,
    competitor_mapping,
    contact_intelligence,
    decision_makers,
    events_footprint,
    input_node,
    market_position,
    outreach_generation,
    strategic_watchouts,
    tracking_logic,
    validator,
    web_research,
)
from .state import NodeSnapshot, RunState


PIPELINE_ORDER = [
    ("input_node", "Input"),
    ("web_research", "Web Research"),
    ("company_overview", "Company Overview"),
    ("market_position", "Market Position"),
    ("competitor_mapping", "Competitor Mapping"),
    ("brand_activity", "Brand Activity"),
    ("events_footprint", "Events Footprint"),
    ("strategic_watchouts", "Strategic Watchouts"),
    ("decision_makers", "Decision Makers"),
    ("contact_intelligence", "Contact Intelligence"),
    ("outreach_generation", "Outreach Generation"),
    ("tracking_logic", "Tracking Logic"),
    ("validator", "Validator"),
    ("output", "Output"),
]

PIPELINE_EDGES = [
    ("input_node", "web_research"),
    ("web_research", "company_overview"),
    ("company_overview", "market_position"),
    ("market_position", "competitor_mapping"),
    ("competitor_mapping", "brand_activity"),
    ("brand_activity", "events_footprint"),
    ("events_footprint", "strategic_watchouts"),
    ("strategic_watchouts", "decision_makers"),
    ("decision_makers", "contact_intelligence"),
    ("contact_intelligence", "outreach_generation"),
    ("outreach_generation", "tracking_logic"),
    ("tracking_logic", "validator"),
    ("validator", "output"),
]

RETRY_EDGES = [
    ("validator", "contact_intelligence", "orange"),
    ("validator", "outreach_generation", "orange"),
]

NODE_RUNNERS: Dict[str, Callable] = {
    "input_node": input_node.run,
    "web_research": web_research.run,
    "company_overview": company_overview.run,
    "market_position": market_position.run,
    "competitor_mapping": competitor_mapping.run,
    "brand_activity": brand_activity.run,
    "events_footprint": events_footprint.run,
    "strategic_watchouts": strategic_watchouts.run,
    "decision_makers": decision_makers.run,
    "contact_intelligence": contact_intelligence.run,
    "outreach_generation": outreach_generation.run,
    "tracking_logic": tracking_logic.run,
    "validator": validator.run,
}


def default_nodes() -> List[NodeSnapshot]:
    return [NodeSnapshot(id=node_id, label=label) for node_id, label in PIPELINE_ORDER]


def get_node_runner(node_id: str):
    return NODE_RUNNERS.get(node_id)


def _graph_adapter(runner: Callable):
    async def _wrapped(state: dict) -> dict:
        run_state = RunState.model_validate(state)
        updated = await runner(run_state)
        return updated.model_dump()

    return _wrapped


def build_langgraph():
    try:
        from langgraph.graph import END, StateGraph
    except ImportError:
        return None

    workflow = StateGraph(dict)
    for node_id, _label in PIPELINE_ORDER:
        if node_id == "output":
            workflow.add_node(node_id, lambda state: state)
            continue
        runner = get_node_runner(node_id)
        workflow.add_node(node_id, _graph_adapter(runner) if runner is not None else (lambda state: state))

    workflow.set_entry_point("input_node")
    for source, target in PIPELINE_EDGES:
        workflow.add_edge(source, target)
    workflow.add_edge("output", END)
    return workflow.compile()


def compile_graph() -> dict:
    return {
        "name": "market_intelligence_agent",
        "description": "Full workflow graph for research, enrichment, validation, tracking, and output.",
        "langgraph_ready": build_langgraph() is not None,
        "nodes": [node.model_dump() for node in default_nodes()],
        "edges": [
            {"source": source, "target": target, "kind": "default"}
            for source, target in PIPELINE_EDGES
        ]
        + [
            {"source": source, "target": target, "kind": "retry", "color": color}
            for source, target, color in RETRY_EDGES
        ],
    }
