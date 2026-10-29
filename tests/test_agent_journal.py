import pytest

from app.tools.journal import AgentJournal
from app.tools.registry import ToolError


def test_task_survives_reopening(tmp_path):
    database = tmp_path / "tasks.db"

    first = AgentJournal(database)

    task = first.create_task(
        "Inspect Python project",
        tmp_path,
    )

    first.transition(task["id"], "running")

    first.record(
        task["id"],
        "tool.completed",
        {"tool": "files.list", "count": 3},
    )

    second = AgentJournal(database)

    recovered = second.get_task(task["id"])
    events = second.history(task["id"])

    assert recovered["status"] == "running"
    assert len(events) == 1
    assert events[0]["payload"]["count"] == 3


def test_invalid_transition_denied(tmp_path):
    journal = AgentJournal(
        tmp_path / "tasks.db"
    )

    task = journal.create_task(
        "Test workflow",
        tmp_path,
    )

    with pytest.raises(ToolError):
        journal.transition(
            task["id"], "completed"
        )


def test_approval_lifecycle(tmp_path):
    journal = AgentJournal(
        tmp_path / "tasks.db"
    )

    task = journal.create_task(
        "Prepare patch",
        tmp_path,
    )

    journal.transition(task["id"], "running")
    journal.transition(
        task["id"], "awaiting_approval"
    )
    journal.transition(task["id"], "running")
    result = journal.transition(
        task["id"], "completed"
    )

    assert result["status"] == "completed"


def test_missing_task_denied(tmp_path):
    journal = AgentJournal(
        tmp_path / "tasks.db"
    )

    with pytest.raises(ToolError):
        journal.get_task("missing")
