"""Durable agent task and event journal."""

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.tools.registry import ToolError


def now():
    return datetime.now(timezone.utc).isoformat()


class AgentJournal:
    STATES = {
        "queued": {"running"},
        "running": {
            "completed",
            "failed",
            "awaiting_approval",
        },
        "awaiting_approval": {
            "running",
            "failed",
        },
        "completed": set(),
        "failed": set(),
    }

    def __init__(self, database):
        self.database = Path(database)
        self.database.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        self.migrate()

    def connect(self):
        connection = sqlite3.connect(
            self.database,
            timeout=10,
        )
        connection.row_factory = sqlite3.Row
        connection.execute(
            "PRAGMA foreign_keys = ON"
        )
        return connection

    def migrate(self):
        with self.connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    objective TEXT NOT NULL,
                    workspace TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(task_id) REFERENCES tasks(id)
                )
            """)

    def create_task(self, objective, workspace):
        if not isinstance(objective, str):
            raise ToolError("Objective must be text")

        objective = objective.strip()

        if not objective:
            raise ToolError("Objective required")

        root = Path(workspace).resolve(strict=True)

        if not root.is_dir():
            raise ToolError("Workspace must be a directory")

        task_id = uuid.uuid4().hex
        timestamp = now()

        with self.connect() as db:
            db.execute(
                """
                INSERT INTO tasks
                (id, objective, workspace, status,
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    task_id,
                    objective,
                    str(root),
                    "queued",
                    timestamp,
                    timestamp,
                ),
            )

        return self.get_task(task_id)

    def get_task(self, task_id):
        with self.connect() as db:
            row = db.execute(
                "SELECT * FROM tasks WHERE id = ?",
                (task_id,),
            ).fetchone()

        if row is None:
            raise ToolError("Task not found")

        return dict(row)

    def transition(self, task_id, new_status):
        with self.connect() as db:
            row = db.execute(
                "SELECT status FROM tasks WHERE id = ?",
                (task_id,),
            ).fetchone()

            if row is None:
                raise ToolError("Task not found")

            current = row["status"]

            if new_status not in self.STATES[current]:
                raise ToolError(
                    f"Invalid transition: {current} "
                    f"to {new_status}"
                )

            db.execute(
                """
                UPDATE tasks
                SET status = ?, updated_at = ?
                WHERE id = ?
                """,
                (new_status, now(), task_id),
            )

        return self.get_task(task_id)

    def record(self, task_id, kind, payload):
        if not isinstance(kind, str) or not kind:
            raise ToolError("Event kind required")

        if not isinstance(payload, dict):
            raise ToolError("Event payload must be object")

        encoded = json.dumps(payload)

        with self.connect() as db:
            db.execute(
                """
                INSERT INTO events
                (task_id, kind, payload, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (task_id, kind, encoded, now()),
            )

    def history(self, task_id):
        self.get_task(task_id)

        with self.connect() as db:
            rows = db.execute(
                """
                SELECT id, kind, payload, created_at
                FROM events
                WHERE task_id = ?
                ORDER BY id
                """,
                (task_id,),
            ).fetchall()

        return [
            {
                **dict(row),
                "payload": json.loads(row["payload"]),
            }
            for row in rows
        ]
