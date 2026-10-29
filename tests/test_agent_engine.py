from app.tools.engine import AgentEngine
from app.tools.planner import WorkspacePlanner
from app.tools.registry import ToolRegistry


def test_agent_inspects_real_project(tmp_path):
    (tmp_path / "hello.py").write_text(
        "ANSWER = 42\n"
    )

    engine = AgentEngine(
        ToolRegistry(tmp_path),
        WorkspacePlanner(),
    )

    state = engine.run(
        "Inspect this Python project"
    )

    assert state.status == "completed"
    assert state.steps == 3

    assert [
        item["tool"]
        for item in state.observations
    ] == [
        "files.list",
        "files.read",
        "shell.run",
    ]

    assert state.result["outcome"] == (
        "inspection_complete"
    )


def test_agent_enforces_step_budget(tmp_path):
    engine = AgentEngine(
        ToolRegistry(tmp_path),
        WorkspacePlanner(),
        max_steps=1,
    )

    state = engine.run("Inspect project")

    assert state.status == "budget_exhausted"
    assert state.steps == 1


def test_agent_rejects_empty_objective(tmp_path):
    engine = AgentEngine(
        ToolRegistry(tmp_path),
        WorkspacePlanner(),
    )

    try:
        engine.run(" ")
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty objective was accepted"
        )


def test_agent_reports_tool_failure(tmp_path):
    class BadPlanner:
        def next_action(self, state):
            if not state.observations:
                return {
                    "action": "tool",
                    "name": "shell.run",
                    "arguments": {
                        "command": "unapproved-command"
                    },
                }

            return {
                "action": "finish",
                "result": {"handled": True},
            }

    engine = AgentEngine(
        ToolRegistry(tmp_path),
        BadPlanner(),
    )

    state = engine.run("Try an unauthorized tool")

    assert state.steps == 1
    assert state.observations[0]["success"] is False
