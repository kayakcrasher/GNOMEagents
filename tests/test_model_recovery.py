"""ModelPlanner recovery tests."""

import pytest

from app.tools.model_planner import ModelPlanner
from app.tools.registry import ToolError


class SequenceModel:
    def __init__(self, decisions):
        self.decisions = iter(decisions)
        self.requests = []

    def decide(self, request):
        self.requests.append(request)
        return next(self.decisions)


class State:
    objective = "Summarize registry.py"
    observations = [{
        "step": 1,
        "tool": "files.read",
        "arguments": {"path": "registry.py"},
        "success": True,
        "output": {"content": "ToolRegistry"},
    }]


def test_recovers_from_duplicate_with_finish():
    model = SequenceModel([
        {
            "action": "tool",
            "name": "files.read",
            "arguments": {"path": "registry.py"},
        },
        {
            "action": "finish",
            "result": {"summary": "ToolRegistry"},
        },
    ])

    planner = ModelPlanner(model, ["files.read"])

    result = planner.next_action(State())

    assert result["action"] == "finish"
    assert len(model.requests) == 2
    assert "Repeated" in model.requests[1]["feedback"]


def test_recovers_from_forbidden_tool():
    model = SequenceModel([
        {
            "action": "tool",
            "name": "shell.unrestricted",
            "arguments": {},
        },
        {
            "action": "finish",
            "result": {"summary": "Done"},
        },
    ])

    planner = ModelPlanner(model, ["files.read"])

    assert planner.next_action(State())["action"] == "finish"


def test_retries_are_bounded():
    duplicate = {
        "action": "tool",
        "name": "files.read",
        "arguments": {"path": "registry.py"},
    }

    model = SequenceModel([duplicate] * 3)
    planner = ModelPlanner(
        model,
        ["files.read"],
        max_retries=2,
    )

    result = planner.next_action(State())

    assert result["action"] == "finish"
    assert result["result"]["warning"] == (
        "Model did not generate a final summary"
    )
    assert len(model.requests) == 4
