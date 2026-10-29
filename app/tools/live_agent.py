"""Live GNOME investigation runner."""

import argparse
import json
from pathlib import Path

from app.tools.engine import AgentEngine
from app.tools.model_client import ModelClient
from app.tools.model_planner import ModelPlanner
from app.tools.registry import ToolRegistry


def investigate(
    workspace,
    objective,
    model=None,
    max_steps=12,
):
    registry = ToolRegistry(workspace)

    client = model or ModelClient()

    planner = ModelPlanner(
        client,
        registry.capabilities(),
    )

    engine = AgentEngine(
        registry,
        planner,
        max_steps=max_steps,
    )

    return engine.run(objective)


def main():
    parser = argparse.ArgumentParser(
        description="GNOME live coding investigator"
    )

    parser.add_argument("objective")
    parser.add_argument(
        "--workspace",
        default=".",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=12,
    )

    args = parser.parse_args()

    state = investigate(
        Path(args.workspace),
        args.objective,
        max_steps=args.steps,
    )

    print(json.dumps({
        "status": state.status,
        "steps": state.steps,
        "result": state.result,
        "observations": state.observations,
    }, indent=2))


if __name__ == "__main__":
    main()
