from dataclasses import dataclass, field

from app.agent_tools import build_runtime


@dataclass
class WorkflowState:
    status: str = "ready"
    steps: int = 0
    result: dict = field(default_factory=dict)
    trace: list = field(default_factory=list)


class AgentWorkflow:
    def __init__(self, runtime=None, max_steps=3):
        if not 1 <= max_steps <= 10:
            raise ValueError("Invalid step limit")

        self.runtime = runtime or build_runtime()
        self.max_steps = max_steps

    def decide(self, analysis):
        if analysis.get("priority") == "high":
            return {
                "action": "prepare_response",
                "requires_human_review": True,
            }

        return {
            "action": "queue_for_review",
            "requires_human_review": True,
        }

    def run(self, objective, context):
        state = WorkflowState(status="working")

        if objective != "lead:process":
            state.status = "blocked"
            state.result = {"reason": "unsupported_objective"}
            return state

        message = context.get("message") if isinstance(context, dict) else None

        if not isinstance(message, str) or not 1 <= len(message.strip()) <= 2000:
            state.status = "blocked"
            state.result = {"reason": "invalid_message"}
            return state

        plan = [{
            "tool": "lead.analyze",
            "args": {"message": message},
        }]

        while plan:
            if state.steps >= self.max_steps:
                state.status = "blocked"
                state.result = {"reason": "step_limit"}
                return state

            step = plan.pop(0)

            execution = self.runtime.run(
                objective, [step]
            )

            if execution.status != "completed":
                state.status = execution.status
                state.result = execution.result
                return state

            state.steps += 1
            state.trace.append({
                "step": state.steps,
                "tool": step["tool"],
                "result": execution.result,
            })

            if step["tool"] == "lead.analyze":
                decision = self.decide(execution.result)

                state.result = {
                    "analysis": execution.result,
                    "decision": decision,
                }

                state.trace.append({
                    "event": "decision",
                    "decision": decision,
                })

        state.status = "awaiting_approval"
        return state
