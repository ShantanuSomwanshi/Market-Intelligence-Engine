from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Dict, List
from uuid import uuid4

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, ValidationError

from .config import get_settings
from .db import get_tracking_events, init_db, list_runs as db_list_runs, persist_run, save_tracking_event
from .graph import PIPELINE_ORDER, compile_graph, default_nodes, get_node_runner
from .services import (
    build_evidence_trace,
    build_executive_brief,
    build_recommendation_engine,
    build_scorecard,
    build_tracking_metrics,
    build_trust_summary,
    get_provider,
)
from .state import (
    RunInput,
    RunState,
    RunSummary,
    append_event,
    clear_retry,
    ensure_report_shape,
    get_node,
    update_node_status,
    utc_now,
)


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = BASE_DIR / "outputs"
DB_PATH = OUTPUTS_DIR / "runs.db"
SETTINGS = get_settings()
TRANSPARENT_PIXEL = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc`\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)

app = FastAPI(
    title="Market Intelligence Agent API",
    version="1.0.0",
    description="End-to-end research and outreach automation agent for the StepOne AI Buildathon.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

active_runs: Dict[str, RunState] = {}
connections: List[WebSocket] = []


class ReplyEvent(BaseModel):
    run_id: str
    contact_key: str
    message: str = ""


async def broadcast(payload: dict) -> None:
    stale: List[WebSocket] = []
    for websocket in connections:
        try:
            await websocket.send_json(payload)
        except RuntimeError:
            stale.append(websocket)
    for websocket in stale:
        if websocket in connections:
            connections.remove(websocket)


def save_run(run: RunState) -> str:
    return persist_run(DB_PATH, OUTPUTS_DIR, run)


async def emit_run_state(run: RunState, event_type: str) -> None:
    save_run(run)
    await broadcast({"type": event_type, "run": run.model_dump()})


def load_run_from_disk(run_id: str) -> RunState | None:
    output_path = OUTPUTS_DIR / f"{run_id}.json"
    if not output_path.exists():
        return None
    try:
        return RunState.model_validate_json(output_path.read_text(encoding="utf-8"))
    except ValidationError:
        return None


def record_tracking_event(run_id: str, contact_key: str, event_type: str, payload: dict) -> None:
    save_tracking_event(
        DB_PATH,
        run_id=run_id,
        contact_key=contact_key,
        event_type=event_type,
        created_at=utc_now(),
        payload=payload,
    )


async def execute_node(run: RunState, node_id: str, label: str) -> RunState:
    update_node_status(run, node_id, "running", f"{label} is executing.")
    await emit_run_state(run, "node_updated")
    runner = get_node_runner(node_id)
    if runner is not None:
        run = await runner(run)
    update_node_status(run, node_id, "completed", f"{label} completed.")
    await emit_run_state(run, "node_updated")
    return run


async def execute_run(run_id: str) -> None:
    run = active_runs.get(run_id)
    if run is None:
        return

    run.status = "running"
    append_event(run, "run_started", "Workflow execution started.", mode=get_provider().mode)
    await emit_run_state(run, "run_updated")

    index = 0
    order_lookup = {node_id: idx for idx, (node_id, _label) in enumerate(PIPELINE_ORDER)}
    try:
        while index < len(PIPELINE_ORDER):
            node_id, label = PIPELINE_ORDER[index]

            if node_id == "output":
                update_node_status(run, "output", "running", "Packaging final output.")
                run.report = ensure_report_shape(run)
                run.tracking["metrics"] = build_tracking_metrics(get_tracking_events(DB_PATH, run.run_id))
                run.tracking["provider_mode"] = get_provider().mode
                run.tracking["report_ready_at"] = utc_now()
                run.derived_insights = {
                    "executive_brief": build_executive_brief(run),
                    "scorecard": build_scorecard(run),
                    "trust_summary": build_trust_summary(run),
                    "evidence_trace": build_evidence_trace(run),
                    "recommendation_engine": build_recommendation_engine(run),
                }
                update_node_status(run, "output", "completed", "Final output ready.")
                run.status = "completed"
                append_event(run, "run_completed", "Workflow finished successfully.")
                await emit_run_state(run, "run_completed")
                break

            run = await execute_node(run, node_id, label)

            if node_id == "outreach_generation":
                for item in run.report.get("personalized_outreach", []):
                    record_tracking_event(
                        run.run_id,
                        item.get("person_name") or item.get("role_title", "contact"),
                        "delivered",
                        {"subject": item.get("email_subject", ""), "role_title": item.get("role_title", "")},
                    )

            if node_id == "validator" and run.retry_target:
                target = run.retry_target
                retry_reason = run.retry_reason
                target_node = get_node(run, target)
                if target_node is not None:
                    target_node.status = "retrying"
                    target_node.detail = retry_reason
                await emit_run_state(run, "validator_retry")
                index = order_lookup.get(target, index)
                clear_retry(run)
                continue

            index += 1
            await asyncio.sleep(0.08)
    except Exception as exc:
        run.status = "failed"
        run.errors.append(str(exc))
        append_event(run, "run_failed", "Workflow execution failed.", error=str(exc))
        if run.current_node_id:
            update_node_status(run, run.current_node_id, "failed", str(exc))
        await emit_run_state(run, "run_failed")


@app.on_event("startup")
async def startup_event() -> None:
    init_db(DB_PATH)


@app.get("/api/health")
async def health() -> dict:
    return {
        "status": "ok",
        "db_path": str(DB_PATH),
        "provider_mode": get_provider().mode,
        "mock_mode": SETTINGS.use_mock_data,
    }


@app.get("/api/graph")
async def graph() -> dict:
    return compile_graph()


@app.get("/api/runs")
async def list_runs() -> list[RunSummary]:
    return db_list_runs(DB_PATH)


@app.post("/api/runs")
async def create_run(payload: RunInput) -> RunState:
    run = RunState(
        run_id=str(uuid4()),
        input=payload,
        nodes=default_nodes(),
        status="queued",
    )
    active_runs[run.run_id] = run
    save_run(run)
    await broadcast({"type": "run_created", "run": run.model_dump()})
    asyncio.create_task(execute_run(run.run_id))
    return run


@app.get("/api/runs/{run_id}")
async def get_run(run_id: str) -> RunState:
    if run_id in active_runs:
        return active_runs[run_id]
    run = load_run_from_disk(run_id)
    if run is not None:
        return run
    raise HTTPException(status_code=404, detail="Run not found")


@app.get("/api/runs/{run_id}/metrics")
async def get_metrics(run_id: str) -> dict:
    events = get_tracking_events(DB_PATH, run_id)
    return build_tracking_metrics(events)


@app.post("/api/tracking/reply")
async def capture_reply(payload: ReplyEvent) -> dict:
    record_tracking_event(
        payload.run_id,
        payload.contact_key,
        "replied",
        {"message": payload.message},
    )
    return {"status": "recorded"}


@app.get("/track/open/{run_id}/{contact_key}/pixel.png")
async def track_open(run_id: str, contact_key: str) -> Response:
    record_tracking_event(run_id, contact_key, "opened", {"pixel": True})
    return Response(content=TRANSPARENT_PIXEL, media_type="image/png")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    connections.append(websocket)
    await websocket.send_json(
        {
            "type": "bootstrap",
            "graph": compile_graph(),
            "server_time": utc_now(),
            "provider_mode": get_provider().mode,
        }
    )
    try:
        while True:
            message = await websocket.receive_text()
            await websocket.send_json({"type": "echo", "message": message})
    except WebSocketDisconnect:
        if websocket in connections:
            connections.remove(websocket)
