from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import List

from .state import RunState, RunSummary


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                company_name TEXT NOT NULL,
                category_description TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                output_path TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tracking_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                contact_key TEXT NOT NULL,
                event_type TEXT NOT NULL,
                created_at TEXT NOT NULL,
                payload TEXT NOT NULL
            )
            """
        )
        conn.commit()


def persist_run(db_path: Path, outputs_dir: Path, run: RunState) -> str:
    outputs_dir.mkdir(parents=True, exist_ok=True)
    output_path = outputs_dir / f"{run.run_id}.json"
    output_path.write_text(run.model_dump_json(indent=2), encoding="utf-8")

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO runs (
                run_id, company_name, category_description, status, created_at, updated_at, output_path
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET
                company_name = excluded.company_name,
                category_description = excluded.category_description,
                status = excluded.status,
                updated_at = excluded.updated_at,
                output_path = excluded.output_path
            """,
            (
                run.run_id,
                run.input.company_name,
                run.input.category_description,
                run.status,
                run.started_at,
                run.updated_at,
                str(output_path),
            ),
        )
        conn.commit()
    return str(output_path)


def list_runs(db_path: Path) -> List[RunSummary]:
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT run_id, company_name, category_description, status, created_at, updated_at, output_path
            FROM runs
            ORDER BY updated_at DESC
            """
        ).fetchall()

    return [
        RunSummary(
            run_id=row[0],
            company_name=row[1],
            category_description=row[2],
            status=row[3],
            created_at=row[4],
            updated_at=row[5],
            output_path=row[6],
        )
        for row in rows
    ]


def save_tracking_event(
    db_path: Path,
    *,
    run_id: str,
    contact_key: str,
    event_type: str,
    created_at: str,
    payload: dict,
) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO tracking_events (run_id, contact_key, event_type, created_at, payload)
            VALUES (?, ?, ?, ?, ?)
            """,
            (run_id, contact_key, event_type, created_at, json.dumps(payload)),
        )
        conn.commit()


def get_tracking_events(db_path: Path, run_id: str) -> list[dict]:
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT contact_key, event_type, created_at, payload
            FROM tracking_events
            WHERE run_id = ?
            ORDER BY created_at ASC
            """,
            (run_id,),
        ).fetchall()

    events = []
    for row in rows:
        payload = json.loads(row[3])
        events.append(
            {
                "contact_key": row[0],
                "event_type": row[1],
                "created_at": row[2],
                "payload": payload,
            }
        )
    return events
