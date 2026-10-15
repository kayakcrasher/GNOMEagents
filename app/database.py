import sqlite3
from pathlib import Path

from app.agent import analyze_lead
from app.leads import Lead, LeadCreate, utc_now


DB_PATH = Path("data/gnome_agents.db")


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    with connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact TEXT NOT NULL,
                message TEXT NOT NULL,
                status TEXT NOT NULL,
                intent TEXT NOT NULL,
                priority TEXT NOT NULL,
                confidence REAL NOT NULL,
                recommended_action TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


def add_lead(lead: LeadCreate) -> Lead:
    analysis = analyze_lead(lead.message)
    created_at = utc_now()

    with connect() as connection:
        cursor = connection.execute(
            """
            INSERT INTO leads (
                name,
                contact,
                message,
                status,
                intent,
                priority,
                confidence,
                recommended_action,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                lead.name,
                lead.contact,
                lead.message,
                "new",
                analysis.intent,
                analysis.priority,
                analysis.confidence,
                analysis.recommended_action,
                created_at.isoformat(),
            ),
        )

        lead_id = cursor.lastrowid

    return Lead(
        id=lead_id,
        name=lead.name,
        contact=lead.contact,
        message=lead.message,
        status="new",
        intent=analysis.intent,
        priority=analysis.priority,
        confidence=analysis.confidence,
        recommended_action=analysis.recommended_action,
        created_at=created_at,
    )


def get_leads() -> list[Lead]:
    with connect() as connection:
        rows = connection.execute(
            "SELECT * FROM leads ORDER BY id DESC"
        ).fetchall()

    return [
        Lead(
            id=row["id"],
            name=row["name"],
            contact=row["contact"],
            message=row["message"],
            status=row["status"],
            intent=row["intent"],
            priority=row["priority"],
            confidence=row["confidence"],
            recommended_action=row["recommended_action"],
            created_at=row["created_at"],
        )
        for row in rows
    ]
