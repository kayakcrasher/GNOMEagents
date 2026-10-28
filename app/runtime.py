from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True)
class Tool:
    name: str
    handler: Callable[[dict], dict]
    requires_approval: bool = False


@dataclass
class AgentState:
    objective: str
    status: str = "ready"
    steps: int = 0
    result: dict = field(default_factory=dict)
    trace: list = field(default_factory=list)


class AgentRuntime:
    def __init__(self, max_steps=5):
        if not 1 <= max_steps <= 20:
            raise ValueError("max_steps must be 1-20")

        self.max_steps = max_steps
        self.tools = {}

    def register(self, tool: Tool):
        if tool.name in self.tools:
            raise ValueError("Duplicate tool")
        self.tools[tool.name] = tool

    def run(self, objective, plan):
        state = AgentState(objective=objective)

        if not isinstance(plan, list):
            raise ValueError("Plan must be a list")

        if len(plan) > self.max_steps:
            state.status = "blocked"
            state.result = {"reason": "step_limit"}
            return state

        state.status = "working"

        for step in plan:
            if not isinstance(step, dict):
                state.status = "blocked"
                state.result = {"reason": "invalid_step"}
                break

            name = step.get("tool")
            args = step.get("args", {})

            if not isinstance(args, dict):
                state.status = "blocked"
                state.result = {"reason": "invalid_args"}
                break

            tool = self.tools.get(name)

            if tool is None:
                state.status = "blocked"
                state.result = {
                    "reason": "unknown_tool",
                    "tool": name,
                }
                break

            if tool.requires_approval:
                state.status = "awaiting_approval"
                state.result = {
                    "reason": "approval_required",
                    "tool": name,
                }
                break

            try:
                output = tool.handler(dict(args))
                if not isinstance(output, dict):
                    raise TypeError("Tool must return dict")
            except Exception as error:
                state.status = "failed"
                state.result = {
                    "reason": "tool_failed",
                    "tool": name,
                    "error_type": type(error).__name__,
                }
                break

            state.steps += 1
            state.trace.append({
                "step": state.steps,
                "tool": name,
                "result": output,
            })
            state.result = output
        else:
            state.status = "completed"

        return state
