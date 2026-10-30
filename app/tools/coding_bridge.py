"""Bridge validated code generation to patch review."""

import ast

from app.tools.coding_workbench import CodingWorkbench
from app.tools.patches import PatchManager
from app.tools.registry import ToolError, ToolRegistry


class CodingBridge:
    def __init__(self, workspace, model=None):
        self.registry = ToolRegistry(workspace)
        self.workbench = CodingWorkbench(model=model)
        self.patches = PatchManager(workspace)

    def propose_function(
        self, objective, name, parameters, path
    ):
        if not isinstance(path, str) or not path.endswith(".py"):
            raise ToolError("Python target required")

        original = self.registry.read_file(path)["content"]

        generated = self.workbench.generate_function(
            objective, name, parameters
        )

        source = generated["source"].strip() + "\n"

        existing_tree = ast.parse(original)
        generated_tree = ast.parse(source)

        existing_names = {
            node.name
            for node in existing_tree.body
            if isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef,
                       ast.ClassDef)
            )
        }

        if name in existing_names:
            raise ToolError("Function already exists")

        for node in generated_tree.body:
            if not isinstance(
                node, (ast.FunctionDef, ast.Import,
                       ast.ImportFrom)
            ):
                raise ToolError(
                    "Unexpected top-level generated code"
                )

        # Append only. Never replace existing code.
        updated = original.rstrip() + "\n\n\n" + source

        ast.parse(updated)

        proposal = self.patches.propose(path, updated)

        return {
            "status": "awaiting_approval",
            "proposal": proposal,
            "generation": {
                "syntax_valid": generated["syntax_valid"],
                "signature_valid": generated["signature_valid"],
                "tests_run": False,
            },
        }
