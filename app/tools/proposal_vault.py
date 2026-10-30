"""Durable storage for reviewable code proposals."""

import sqlite3
from pathlib import Path

from app.tools.patches import PatchManager
from app.tools.registry import ToolError


class ProposalVault:
    def __init__(self, workspace, database):
        self.patches = PatchManager(workspace)
        self.database = Path(database)
        self.database.parent.mkdir(
            parents=True, exist_ok=True
        )

        with self.connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS proposals (
                    id TEXT PRIMARY KEY,
                    path TEXT NOT NULL,
                    before_hash TEXT NOT NULL,
                    after_content TEXT NOT NULL,
                    diff TEXT NOT NULL,
                    status TEXT NOT NULL
                )
            """)

    def connect(self):
        return sqlite3.connect(
            self.database, timeout=10
        )

    def save(self, path, new_content):
        proposal = self.patches.propose(
            path, new_content
        )

        record = self.patches.pending[
            proposal["id"]
        ]

        with self.connect() as db:
            db.execute(
                """
                INSERT INTO proposals
                (id, path, before_hash,
                 after_content, diff, status)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    record.id,
                    record.path,
                    record.before_hash,
                    record.after,
                    record.diff,
                    "awaiting_approval",
                ),
            )

        return proposal

    def get(self, proposal_id):
        with self.connect() as db:
            db.row_factory = sqlite3.Row
            row = db.execute(
                """
                SELECT * FROM proposals
                WHERE id = ?
                """,
                (proposal_id,),
            ).fetchone()

        if row is None:
            raise ToolError("Proposal not found")

        return dict(row)

    def pending(self):
        with self.connect() as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(
                """
                SELECT id, path, diff, status
                FROM proposals
                WHERE status = 'awaiting_approval'
                ORDER BY rowid
                """
            ).fetchall()

        return [dict(row) for row in rows]

    def reject(self, proposal_id):
        """Reject a pending proposal without touching files."""
        with self.connect() as db:
            cursor = db.execute(
                """
                UPDATE proposals
                SET status = 'rejected'
                WHERE id = ?
                AND status = 'awaiting_approval'
                """,
                (proposal_id,),
            )

            if cursor.rowcount != 1:
                raise ToolError(
                    "Proposal not awaiting approval"
                )

        return {
            "id": proposal_id,
            "status": "rejected",
        }

    def approve(self, proposal_id, approved=False):
        """Apply a stored proposal only with explicit approval."""
        if approved is not True:
            raise ToolError("Explicit approval required")

        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")

            db.row_factory = sqlite3.Row
            row = db.execute(
                """
                SELECT * FROM proposals
                WHERE id = ?
                """,
                (proposal_id,),
            ).fetchone()

            if row is None:
                raise ToolError("Proposal not found")

            if row["status"] != "awaiting_approval":
                raise ToolError(
                    "Proposal not awaiting approval"
                )

            target = self.patches._target(row["path"])
            current = target.read_text(encoding="utf-8")

            if self.patches.digest(current) != row["before_hash"]:
                raise ToolError(
                    "File changed since proposal"
                )

            target.write_text(
                row["after_content"],
                encoding="utf-8",
            )

            db.execute(
                """
                UPDATE proposals
                SET status = 'applied'
                WHERE id = ?
                """,
                (proposal_id,),
            )

        return {
            "id": proposal_id,
            "path": row["path"],
            "status": "applied",
        }
