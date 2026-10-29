"""Bounded test and read-only Git operators."""

import subprocess
import sys

from app.tools.registry import ToolError, ToolRegistry


class DevOpsTools:
    MAX_OUTPUT = 12000

    def __init__(self, workspace):
        self.registry = ToolRegistry(workspace)
        self.root = self.registry.root

    def _run(self, argv, timeout=30):
        try:
            result = subprocess.run(
                argv,
                cwd=self.root,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                errors="replace",
                timeout=timeout,
                check=False,
                env={
                    "PATH": __import__("os").environ.get(
                        "PATH", ""
                    ),
                    "HOME": str(self.root),
                    "GIT_CONFIG_NOSYSTEM": "1",
                    "GIT_CONFIG_GLOBAL": "/dev/null",
                    "GIT_OPTIONAL_LOCKS": "0",
                    "GIT_TERMINAL_PROMPT": "0",
                    "GIT_PAGER": "cat",
                    "PAGER": "cat",
                },
            )
        except subprocess.TimeoutExpired as error:
            raise ToolError(
                "Operation exceeded time limit"
            ) from error
        except OSError as error:
            raise ToolError(
                "Could not start operation"
            ) from error

        return {
            "returncode": result.returncode,
            "passed": result.returncode == 0,
            "stdout": result.stdout[:self.MAX_OUTPUT],
            "stderr": result.stderr[:self.MAX_OUTPUT],
        }

    def git_status(self):
        result = self._run(
            ["git", "status", "--short"],
            timeout=10,
        )
        if not result["passed"]:
            raise ToolError("Git status failed")
        return result

    def git_diff(self):
        result = self._run(
            ["git", "diff", "--no-ext-diff", "--"],
            timeout=10,
        )
        if not result["passed"]:
            raise ToolError("Git diff failed")
        return result

    def run_tests(self):
        result = self._run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "-p",
                "no:cacheprovider",
            ],
            timeout=60,
        )
        result["operation"] = "pytest"
        return result
