from app.runtime import AgentRuntime, Tool
from app.agent_tools import build_runtime


def test_agent_completes():
    agent = build_runtime()
    state = agent.run(
        "Analyze lead",
        [{
            "tool": "lead.analyze",
            "args": {"message": "Need a quote"},
        }],
    )
    assert state.status == "completed"
    assert state.steps == 1
    assert state.result["intent"] == "quote_request"


def test_unknown_tool_blocked():
    state = build_runtime().run(
        "Unknown action",
        [{"tool": "system.shell", "args": {}}],
    )
    assert state.status == "blocked"
    assert state.steps == 0


def test_step_limit():
    agent = AgentRuntime(max_steps=2)
    state = agent.run(
        "Too many actions",
        [{"tool": "anything"}] * 3,
    )
    assert state.status == "blocked"
    assert state.result["reason"] == "step_limit"


def test_approval_required():
    agent = AgentRuntime()
    agent.register(Tool(
        "outreach.send",
        lambda args: {"sent": True},
        requires_approval=True,
    ))
    state = agent.run(
        "Send message",
        [{"tool": "outreach.send", "args": {}}],
    )
    assert state.status == "awaiting_approval"
    assert state.steps == 0


def test_tool_failure_contained():
    def broken(args):
        raise RuntimeError("Failed")

    agent = AgentRuntime()
    agent.register(Tool("broken", broken))

    state = agent.run(
        "Try tool",
        [{"tool": "broken", "args": {}}],
    )
    assert state.status == "failed"
    assert state.result["reason"] == "tool_failed"


def test_trace_records_execution():
    state = build_runtime().run(
        "Analyze lead",
        [{
            "tool": "lead.analyze",
            "args": {"message": "Hello"},
        }],
    )
    assert len(state.trace) == 1
    assert state.trace[0]["tool"] == "lead.analyze"
