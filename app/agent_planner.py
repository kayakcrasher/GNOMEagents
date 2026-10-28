from app.agent_tools import build_runtime


class AgentPlanner:
    def __init__(self, runtime=None):
        self.runtime = runtime or build_runtime()

    def plan(self, objective, context):
        if not isinstance(objective, str):
            raise ValueError("Objective must be text")

        if not isinstance(context, dict):
            raise ValueError("Context must be a dictionary")

        objective = objective.strip().lower()

        if objective in {
            "analyze lead",
            "analyze assigned lead",
            "lead:analyze",
        }:
            message = context.get("message")

            if not isinstance(message, str) or not message.strip():
                raise ValueError("Lead message required")

            if "lead.analyze" not in self.runtime.tools:
                raise ValueError("Required tool unavailable")

            return [{
                "tool": "lead.analyze",
                "args": {"message": message},
            }]

        raise ValueError("Unsupported objective")

    def execute(self, objective, context):
        plan = self.plan(objective, context)
        return self.runtime.run(objective, plan)
