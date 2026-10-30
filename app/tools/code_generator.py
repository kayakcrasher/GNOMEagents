"""Generate reviewable single-file code proposals."""

import ast

from app.tools.model_client import ModelClient
from app.tools.patches import PatchManager
from app.tools.registry import ToolError, ToolRegistry


class CodeGenerator:
    def __init__(self, workspace, model=None):
        self.registry = ToolRegistry(workspace)
        self.model = model or ModelClient()
        self.patches = PatchManager(workspace)

    def propose(self, objective, path):
        if not isinstance(objective, str) or not objective.strip():
            raise ToolError("Coding objective required")

        original = self.registry.read_file(path)
        source = original["content"]

        if len(source.encode("utf-8")) > 12000:
            raise ToolError(
                "File too large for initial local model workflow"
            )

        request = {
            "task": "generate_code_patch",
            "objective": objective,
            "path": original["path"],
            "original_content": source,
            "available_tools": [],
            "instruction": (
                "Return JSON only. Use action='finish'. "
                "Set result.new_content to the COMPLETE "
                "updated file, not a diff. Preserve existing "
                "functionality unless the objective requires "
                "changing it. Do not invent test results."
            ),
        }

        decision = self.model.decide(request)

        if not isinstance(decision, dict):
            raise ToolError("Invalid code generation response")

        if decision.get("action") != "finish":
            raise ToolError(
                "Model did not return a code proposal"
            )

        result = decision.get("result")

        if not isinstance(result, dict):
            raise ToolError("Invalid code proposal result")

        new_content = result.get("new_content")

        if not isinstance(new_content, str):
            raise ToolError("Missing generated file content")

        if not new_content.strip():
            raise ToolError("Generated file is empty")

        if original["path"].endswith(".py"):
            try:
                ast.parse(
                    new_content,
                    filename=original["path"],
                )
            except SyntaxError as error:
                raise ToolError(
                    f"Generated Python has invalid syntax: {error}"
                ) from error

        return self.patches.propose(
            original["path"],
            new_content,
        )
