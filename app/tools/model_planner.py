"""Model-driven decisions with bounded recovery."""

from app.tools.registry import ToolError


class ModelPlanner:
    """Convert model output into controlled agent actions."""

    def __init__(
        self,
        model,
        allowed_tools,
        max_context=12,
        max_retries=2,
    ):
        self.model = model
        self.allowed_tools = frozenset(allowed_tools)
        self.max_context = max_context
        self.max_retries = max_retries

    def next_action(self, state):
        observations = state.observations[-self.max_context:]

        attempted = [
            {
                "name": item.get("tool"),
                "arguments": item.get("arguments"),
                "success": item.get("success"),
            }
            for item in state.observations
        ]

        feedback = None

        for attempt in range(self.max_retries + 1):
            request = {
                "objective": state.objective,
                "observations": observations,
                "available_tools": sorted(self.allowed_tools),
                "attempted_calls": attempted,
                "feedback": feedback,
                "instruction": (
                    "Never repeat an attempted tool call. "
                    "Use files.list for directories and "
                    "files.read for files. "
                    "If enough evidence has been collected, "
                    "finish with a factual summary."
                ),
            }

            decision = self.model.decide(request)

            try:
                return self._validate(decision, attempted)
            except ToolError as error:
                feedback = str(error)

        evidence = [
            item for item in state.observations
            if item.get("success") is True
            and item.get("tool") == "files.read"
        ]

        if evidence:
            summary = self._fallback_summary(
                state.objective,
                evidence,
            )
            return {
                "action": "finish",
                "result": summary,
            }

        raise ToolError(
            "Model could not produce a valid new action "
            f"after {self.max_retries + 1} attempts: "
            f"{feedback}"
        )

    def _validate(self, decision, attempted):
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

        for previous in attempted:
            if (
                previous["name"] == name
                and previous["arguments"] == arguments
            ):
                raise ToolError(
                    f"Repeated tool call: {name} {arguments}. "
                    "Choose a different action or finish."
                )

        return {
            "action": "tool",
            "name": name,
            "arguments": arguments,
        }

    def _fallback_summary(self, objective, evidence):
        request = {
            "objective": objective,
            "available_tools": [],
            "observations": evidence[-2:],
            "instruction": (
                "You must finish now. "
                "Return JSON with action='finish' and "
                "result={'summary': 'your factual answer'}. "
                "Do not request any tools."
            ),
        }

        try:
            decision = self.model.decide(request)
            if (
                isinstance(decision, dict)
                and decision.get("action") == "finish"
                and isinstance(decision.get("result"), dict)
            ):
                return decision["result"]
        except (ToolError, StopIteration):
            pass

        return {
            "summary": (
                "Investigation stopped after reading "
                "the following files: "
                + ", ".join(
                    item["arguments"]["path"]
                    for item in evidence
                )
            ),
            "warning": "Model did not generate a final summary",
        }
