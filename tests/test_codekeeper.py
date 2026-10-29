import pytest

from app.tools.codekeeper import Codekeeper
from app.tools.registry import ToolError


def test_codekeeper_prepares_patch(tmp_path):
    target = tmp_path / "app.py"
    target.write_text("VALUE = 1\n")

    agent = Codekeeper(
        tmp_path,
        tmp_path / "journal.db",
    )

    result = agent.prepare(
        "Improve application",
        "app.py",
        "VALUE = 2\n",
    )

    assert result["status"] == "awaiting_approval"
    assert target.read_text() == "VALUE = 1\n"

    events = agent.journal.history(
        result["task_id"]
    )

    assert any(
        event["kind"] == "patch.proposed"
        for event in events
    )


def test_codekeeper_approval(tmp_path):
    target = tmp_path / "app.py"
    target.write_text("VALUE = 1\n")

    (tmp_path / "test_app.py").write_text(
        "from app import VALUE\n"
        "def test_value():\n"
        "    assert VALUE == 42\n"
    )

    agent = Codekeeper(
        tmp_path,
        tmp_path / "journal.db",
    )

    prepared = agent.prepare(
        "Update value",
        "app.py",
        "VALUE = 42\n",
    )

    completed = agent.approve(
        prepared["task_id"],
        prepared["proposal"]["id"],
    )

    assert completed["status"] == "completed"
    assert completed["tests"]["passed"]
    assert target.read_text() == "VALUE = 42\n"


def test_wrong_proposal_denied(tmp_path):
    target = tmp_path / "app.py"
    target.write_text("VALUE = 1\n")

    agent = Codekeeper(
        tmp_path,
        tmp_path / "journal.db",
    )

    prepared = agent.prepare(
        "Update value",
        "app.py",
        "VALUE = 42\n",
    )

    with pytest.raises(ToolError):
        agent.approve(
            prepared["task_id"],
            "invalid-proposal",
        )

    assert target.read_text() == "VALUE = 1\n"


def test_failed_inspection_records_failure(tmp_path):
    target = tmp_path / "app.py"
    target.write_text("VALUE = 1\n")

    agent = Codekeeper(
        tmp_path,
        tmp_path / "journal.db",
    )

    with pytest.raises(ToolError):
        agent.prepare(
            "Update missing file",
            "missing.py",
            "VALUE = 2\n",
        )

    with agent.journal.connect() as db:
        row = db.execute(
            "SELECT status FROM tasks"
        ).fetchone()

    assert row["status"] == "failed"
