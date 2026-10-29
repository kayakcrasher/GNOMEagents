"""Model-driven decisions for the existing AgentEngine."""

from app.tools.registry import ToolError


class ModelPlanner:
    """Convert model decisions into controlled agent actions."""

    def __init__(self, model, allowed_tools, max_context=12):
        self.model = model
        self.allowed_tools = frozenset(allowed_tools)
        self.max_context = max_context

    def next_action(self, state):
        request = {
            "objective": state.objective,
            "observations": state.observations[
                -self.max_context:
            ],
            "available_tools": sorted(self.allowed_tools),
            "remaining_context": self.max_context,
        }

        decision = self.model.decide(request)

        if not isinstance(decision, dict):
            raise ToolError("Invalid model response")

        action = decision.get("action")

        if action == "finish":
            result = decision.get("result", {})

            if not isinstance(result, dict):
                raise ToolError("Invalid finish result")

            return {
                "action": "finish",
                "result": result,
            }

        if action != "tool":
            raise ToolError("Unsupported model action")

        name = decision.get("name")
        arguments = decision.get("arguments")

        if name not in self.allowed_tools:
            raise ToolError("Model requested forbidden tool")

        if not isinstance(arguments, dict):
            raise ToolError("Invalid tool arguments")

        return {
            "action": "tool",
            "name": name,
            "arguments": arguments,
        }
