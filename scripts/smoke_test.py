from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.graph import PIPELINE_ORDER, default_nodes, get_node_runner
from backend.state import RunInput, RunState


CASES = [
    ("Notion", "Collaborative productivity software for teams"),
    ("Nike", "Global consumer retail and sportswear brand"),
    ("Moderna", "Biotechnology company focused on mRNA therapeutics"),
]


async def execute_case(company_name: str, category_description: str) -> dict:
    run = RunState(
        run_id=str(uuid4()),
        input=RunInput(company_name=company_name, category_description=category_description),
        nodes=default_nodes(),
        status="running",
    )

    for node_id, _label in PIPELINE_ORDER:
        if node_id == "output":
            break
        runner = get_node_runner(node_id)
        if runner is not None:
            run = await runner(run)

    return {
        "company_name": company_name,
        "sections_present": sorted(run.report.keys()),
        "contact_count": len(run.report.get("contact_intelligence", [])),
        "outreach_count": len(run.report.get("personalized_outreach", [])),
        "mode": run.research_context.get("mode", "unknown"),
    }


async def main() -> None:
    results = []
    for company_name, category_description in CASES:
        results.append(await execute_case(company_name, category_description))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
