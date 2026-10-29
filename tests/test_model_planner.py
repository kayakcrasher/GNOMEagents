import pytest

from app.tools.model_planner import ModelPlanner
from app.tools.registry import ToolError


class FakeModel:
    def __init__(self, response):
        self.response = response
        self.request = None

    def decide(self, request):
        self.request = request
        return self.response


class FakeState:
    objective = "Inspect the Python project"
    observations = []


def test_model_selects_allowed_tool():
    model = FakeModel({
        "action": "tool",
        "name": "files.list",
        "arguments": {"path": "."},
    })

    planner = ModelPlanner(
        model,
        ["files.list", "files.read"],
    )

    decision = planner.next_action(FakeState())

    assert decision["name"] == "files.list"
    assert model.request["objective"] == (
        "Inspect the Python project"
    )


def test_model_cannot_use_forbidden_tool():
    model = FakeModel({
        "action": "tool",
        "name": "shell.unrestricted",
        "arguments": {"command": "whoami"},
    })

    planner = ModelPlanner(model, ["files.list"])

    with pytest.raises(ToolError):
        planner.next_action(FakeState())


def test_model_can_finish():
    model = FakeModel({
        "action": "finish",
        "result": {"summary": "Inspection complete"},
    })

    planner = ModelPlanner(model, ["files.list"])

    decision = planner.next_action(FakeState())

    assert decision["action"] == "finish"
    assert decision["result"]["summary"] == (
        "Inspection complete"
    )


def test_model_rejects_malformed_response():
    model = FakeModel("invalid response")
    planner = ModelPlanner(model, ["files.list"])

    with pytest.raises(ToolError):
        planner.next_action(FakeState())


def test_model_rejects_invalid_arguments():
    model = FakeModel({
        "action": "tool",
        "name": "files.read",
        "arguments": "app.py",
    })

    planner = ModelPlanner(model, ["files.read"])

    with pytest.raises(ToolError):
        planner.next_action(FakeState())
