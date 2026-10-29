"""First real GNOMEagents workspace task."""

from app.tools.registry import ToolRegistry


def inspect_workspace(workspace):
    registry = ToolRegistry(workspace)

    listing = registry.execute(
        "files.list",
        {"path": "."},
    )

    location = registry.execute(
        "shell.run",
        {"command": "pwd"},
    )

    return {
        "status": "completed",
        "objective": "Inspect authorized workspace",
        "capabilities": registry.capabilities(),
        "files": listing["entries"],
        "working_directory": location["stdout"].strip(),
    }
