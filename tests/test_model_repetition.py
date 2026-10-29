from app.tools.model_planner import ModelPlanner
from app.tools.registry import ToolError
import pytest


class RepeatingModel:
    def decide(self, request):
        return {
            "action": "tool",
            "name": "files.read",
            "arguments": {"path": "README.md"},
        }


class State:
    objective = "Summarize README.md"
    observations = [{
        "step": 1,
        "tool": "files.read",
        "arguments": {"path": "README.md"},
        "success": True,
        "output": {
            "path": "README.md",
            "content": "# GNOMEagents",
        },
    }]


def test_repeated_successful_read_is_rejected():
    planner = ModelPlanner(
        RepeatingModel(),
        ["files.read"],
    )

    result = planner.next_action(State())

    assert result["action"] == "finish"
    assert result["result"]["warning"] == (
        "Model did not generate a final summary"
    )
