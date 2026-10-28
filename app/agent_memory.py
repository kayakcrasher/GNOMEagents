import json
import os
import sqlite3
from pathlib import Path


class AgentMemory:
    def __init__(self, path=None):
        self.path = Path(
            path or os.getenv(
                "GNOME_AGENT_MEMORY_DB",
                str(Path.home() / ".gnome_agent_memory.db"),
            )
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)

        with self.connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS task_memory (
                    id INTEGER PRIMARY KEY,
                    business_id INTEGER NOT NULL,
                    objective TEXT NOT NULL,
                    status TEXT NOT NULL,
                    result TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def connect(self):
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        return db

    def remember(self, business_id, objective, status, result):
        if not isinstance(business_id, int) or business_id < 1:
            raise ValueError("Invalid business ID")

        if not isinstance(result, dict):
            raise ValueError("Result must be a dictionary")

        with self.connect() as db:
            cursor = db.execute(
                """
                INSERT INTO task_memory
                (business_id, objective, status, result)
                VALUES (?, ?, ?, ?)
                """,
                (
                    business_id,
                    objective,
                    status,
                    json.dumps(result, allow_nan=False),
                ),
            )
            return cursor.lastrowid

    def recall(self, business_id, limit=10):
        if not isinstance(business_id, int) or business_id < 1:
            raise ValueError("Invalid business ID")

        limit = max(1, min(int(limit), 100))

        with self.connect() as db:
            rows = db.execute(
                """
                SELECT id, objective, status, result, created_at
                FROM task_memory
                WHERE business_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (business_id, limit),
            ).fetchall()

        return [
            {
                **dict(row),
                "result": json.loads(row["result"]),
            }
            for row in rows
        ]
