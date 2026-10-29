"""Bounded tool execution for GNOMEagents."""

from dataclasses import dataclass, field
from typing import Any

from app.tools.registry import ToolError


@dataclass
class AgentState:
    objective: str
    status: str = "running"
    steps: int = 0
    observations: list[dict] = field(
        default_factory=list
    )
    result: dict[str, Any] = field(
        default_factory=dict
    )


class AgentEngine:
    def __init__(self, registry, planner, max_steps=8):
        if not 1 <= max_steps <= 50:
            raise ValueError("Invalid step budget")

        self.registry = registry
        self.planner = planner
        self.max_steps = max_steps

    def run(self, objective):
        if not isinstance(objective, str):
            raise ValueError("Objective must be text")

        objective = objective.strip()

        if not objective:
            raise ValueError("Objective required")

        state = AgentState(objective=objective)

        for _ in range(self.max_steps):
            decision = self.planner.next_action(state)

            if not isinstance(decision, dict):
                state.status = "failed"
                state.result = {
                    "error": "Invalid planner decision"
                }
                break

            if decision.get("action") == "finish":
                state.status = "completed"
                state.result = decision.get("result", {})
                break

            if decision.get("action") != "tool":
                state.status = "failed"
                state.result = {
                    "error": "Unsupported planner action"
                }
                break

            name = decision.get("name")
            arguments = decision.get("arguments", {})

            try:
                observation = self.registry.execute(
                    name, arguments
                )
                success = True
            except (ToolError, OSError, ValueError) as error:
                observation = {
                    "error": str(error)
                }
                success = False

            state.observations.append({
                "step": state.steps + 1,
                "tool": name,
                "arguments": arguments,
                "success": success,
                "output": observation,
            })

            state.steps += 1

        else:
            state.status = "budget_exhausted"
            state.result = {
                "error": "Maximum steps reached"
            }

        return state
