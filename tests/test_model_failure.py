from app.tools.engine import AgentEngine
from app.tools.model_planner import ModelPlanner
from app.tools.registry import ToolError, ToolRegistry


class OfflineModel:
    def decide(self, request):
        raise ToolError("Model server unavailable")


class InvalidModel:
    def decide(self, request):
        return "not a decision"


def test_offline_model_fails_safely(tmp_path):
    registry = ToolRegistry(tmp_path)
    planner = ModelPlanner(
        OfflineModel(),
        registry.capabilities(),
    )

    state = AgentEngine(
        registry, planner
    ).run("Inspect repository")

    assert state.status == "failed"
    assert state.result["stage"] == "planning"
    assert state.steps == 0


def test_invalid_model_fails_safely(tmp_path):
    registry = ToolRegistry(tmp_path)
    planner = ModelPlanner(
        InvalidModel(),
        registry.capabilities(),
    )

    state = AgentEngine(
        registry, planner
    ).run("Inspect repository")

    assert state.status == "failed"
    assert state.steps == 0
