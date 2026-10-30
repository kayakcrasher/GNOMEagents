"""Generate and inspect small Python coding tasks."""

import ast

from app.tools.model_client import ModelClient
from app.tools.registry import ToolError


class CodingWorkbench:
    def __init__(self, model=None):
        self.model = model or ModelClient()

    def generate_function(self, objective, name, parameters):
        if not objective.strip():
            raise ToolError("Objective required")

        if not name.isidentifier():
            raise ToolError("Invalid function name")

        if not isinstance(parameters, list):
            raise ToolError("Parameters must be a list")

        if any(
            not isinstance(item, str)
            or not item.isidentifier()
            for item in parameters
        ):
            raise ToolError("Invalid parameter")

        signature = ", ".join(parameters)

        decision = self.model.decide({
            "task": "generate_code_patch",
            "objective": objective,
            "path": "generated.py",
            "original_content": "",
            "available_tools": [],
            "instruction": (
                f"Generate Python source containing exactly "
                f"one top-level function named {name} "
                f"with parameters ({signature}). "
                "Return action='finish' with "
                "result.new_content containing complete "
                "Python source. Imports are allowed. "
                "Do not include examples or markdown."
            ),
        })

        if not isinstance(decision, dict):
            raise ToolError("Invalid model response")

        if decision.get("action") != "finish":
            raise ToolError("Model did not finish")

        result = decision.get("result")

        if not isinstance(result, dict):
            raise ToolError("Invalid result")

        source = result.get("new_content")

        if not isinstance(source, str) or not source.strip():
            raise ToolError("Missing Python source")

        if len(source.encode("utf-8")) > 12000:
            raise ToolError("Generated source too large")

        try:
            tree = ast.parse(source)
        except SyntaxError as error:
            raise ToolError("Invalid Python syntax") from error

        functions = [
            node for node in tree.body
            if isinstance(node, ast.FunctionDef)
        ]

        if len(functions) != 1:
            raise ToolError("Expected one top-level function")

        function = functions[0]

        if function.name != name:
            raise ToolError("Wrong function name")

        args = function.args

        if (
            args.posonlyargs
            or args.vararg
            or args.kwonlyargs
            or args.kwarg
            or args.defaults
            or args.kw_defaults
        ):
            raise ToolError("Unexpected function signature")

        actual = [arg.arg for arg in args.args]

        if actual != parameters:
            raise ToolError("Wrong function parameters")

        return {
            "status": "generated",
            "name": name,
            "source": source,
            "syntax_valid": True,
            "signature_valid": True,
            "tests_run": False,
        }
