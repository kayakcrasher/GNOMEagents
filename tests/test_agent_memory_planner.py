import pytest

from app.agent_memory import AgentMemory
from app.agent_planner import AgentPlanner


def test_memory_persists(tmp_path):
    path = tmp_path / "memory.db"

    AgentMemory(path).remember(
        1, "Analyze lead", "completed",
        {"intent": "quote_request"},
    )

    records = AgentMemory(path).recall(1)

    assert len(records) == 1
    assert records[0]["result"]["intent"] == "quote_request"


def test_memory_isolates_businesses(tmp_path):
    memory = AgentMemory(tmp_path / "memory.db")

    memory.remember(1, "Private task", "completed", {})
    memory.remember(2, "Other task", "completed", {})

    assert len(memory.recall(1)) == 1
    assert memory.recall(1)[0]["objective"] == "Private task"


def test_invalid_business_rejected(tmp_path):
    memory = AgentMemory(tmp_path / "memory.db")

    with pytest.raises(ValueError):
        memory.remember(0, "Task", "completed", {})


def test_planner_selects_tool():
    plan = AgentPlanner().plan(
        "Analyze lead",
        {"message": "I need a quote"},
    )

    assert plan[0]["tool"] == "lead.analyze"


def test_planner_executes():
    state = AgentPlanner().execute(
        "Analyze lead",
        {"message": "Need a quote ASAP"},
    )

    assert state.status == "completed"
    assert state.result["intent"] == "quote_request"


def test_unsupported_objective_rejected():
    with pytest.raises(ValueError):
        AgentPlanner().plan(
            "Delete customer database", {}
        )
