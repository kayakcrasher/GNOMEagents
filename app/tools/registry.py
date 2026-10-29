"""Controlled Linux tools for GNOMEagents."""

import subprocess
from pathlib import Path


class ToolError(Exception):
    """Tool operation denied or failed."""


class ToolRegistry:
    MAX_READ_BYTES = 65536

    COMMANDS = {
        "pwd": ["pwd"],
        "git.status": ["git", "status", "--short"],
    }

    def __init__(self, workspace):
        root = Path(workspace).resolve(strict=True)

        if not root.is_dir():
            raise ToolError("Workspace must be a directory")

        self.root = root

        self.tools = {
            "files.list": self.list_files,
            "files.read": self.read_file,
            "shell.run": self.run_command,
        }

    def resolve(self, relative_path="."):
        path = Path(relative_path)

        if path.is_absolute():
            raise ToolError("Absolute paths denied")

        target = (self.root / path).resolve()

        if not target.is_relative_to(self.root):
            raise ToolError("Workspace escape denied")

        return target

    def list_files(self, path="."):
        target = self.resolve(path)

        if not target.is_dir():
            raise ToolError("Directory not found")

        return {
            "path": str(target.relative_to(self.root)),
            "entries": [
                {
                    "name": item.name,
                    "directory": item.is_dir(),
                }
                for item in sorted(target.iterdir())
                if not item.is_symlink()
            ][:100],
        }

    def read_file(self, path):
        target = self.resolve(path)

        if not target.is_file():
            raise ToolError("File not found")

        if target.stat().st_size > self.MAX_READ_BYTES:
            raise ToolError("File exceeds read limit")

        try:
            content = target.read_text(encoding="utf-8")
        except UnicodeError as error:
            raise ToolError("Text files only") from error

        return {
            "path": str(target.relative_to(self.root)),
            "content": content,
        }

    def run_command(self, command):
        if command not in self.COMMANDS:
            raise ToolError("Command not permitted")

        try:
            result = subprocess.run(
                self.COMMANDS[command],
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
                stdin=subprocess.DEVNULL,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise ToolError("Command execution failed") from error

        return {
            "command": command,
            "returncode": result.returncode,
            "stdout": result.stdout[:8192],
            "stderr": result.stderr[:8192],
        }

    def execute(self, name, arguments=None):
        if name not in self.tools:
            raise ToolError("Unknown tool")

        arguments = arguments or {}

        if not isinstance(arguments, dict):
            raise ToolError("Arguments must be an object")

        try:
            return self.tools[name](**arguments)
        except TypeError as error:
            raise ToolError("Invalid tool arguments") from error

    def capabilities(self):
        return sorted(self.tools)
