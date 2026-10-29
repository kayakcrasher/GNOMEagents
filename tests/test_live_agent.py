from app.tools.live_agent import investigate


class ScriptedModel:
    def __init__(self):
        self.calls = 0

    def decide(self, request):
        self.calls += 1

        if self.calls == 1:
            return {
                "action": "tool",
                "name": "files.list",
                "arguments": {"path": "."},
            }

        if self.calls == 2:
            return {
                "action": "tool",
                "name": "files.read",
                "arguments": {"path": "example.py"},
            }

        return {
            "action": "finish",
            "result": {
                "summary": "Inspected example.py",
            },
        }


def test_live_agent_inspects_workspace(tmp_path):
    (tmp_path / "example.py").write_text(
        "VALUE = 42\n"
    )

    state = investigate(
        tmp_path,
        "Inspect example.py",
        model=ScriptedModel(),
    )

    assert state.status == "completed"
    assert state.steps == 2
    assert len(state.observations) == 2
    assert state.observations[1]["success"]
    assert (
        "VALUE = 42"
        in state.observations[1]["output"]["content"]
    )
