"""Deterministic workspace exploration planner."""

from pathlib import Path


class WorkspacePlanner:
    def next_action(self, state):
        observations = state.observations

        if not observations:
            return {
                "action": "tool",
                "name": "files.list",
                "arguments": {"path": "."},
            }

        if any(not item["success"] for item in observations):
            return {
                "action": "finish",
                "result": {
                    "outcome": "inspection_incomplete",
                    "reason": "A tool operation failed",
                },
            }

        listing = observations[0]["output"]

        if len(observations) == 1:
            candidates = [
                entry["name"]
                for entry in listing["entries"]
                if not entry["directory"]
                and Path(entry["name"]).suffix == ".py"
            ]

            if candidates:
                return {
                    "action": "tool",
                    "name": "files.read",
                    "arguments": {
                        "path": candidates[0]
                    },
                }

        if observations[-1]["tool"] != "shell.run":
            return {
                "action": "tool",
                "name": "shell.run",
                "arguments": {
                    "command": "pwd"
                },
            }

        return {
            "action": "finish",
            "result": {
                "outcome": "inspection_complete",
                "workspace": observations[-1][
                    "output"
                ]["stdout"].strip(),
                "observed_steps": len(observations),
            },
        }
