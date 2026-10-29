"""SMASH CLI — GNOMEagents command center."""

import argparse
import json
import os
import subprocess
import sys

import httpx

from app.workstation_worker import WorkstationWorker


BANNER = """
╔══════════════════════════════════╗
║       GNOMEAGENTS // SMASH        ║
║       Agent Command Center       ║
╚══════════════════════════════════╝
"""


def worker():
    return WorkstationWorker(
        base_url=os.getenv(
            "GNOMEBUSINESS_URL",
            "http://127.0.0.1:8000",
        ),
        token=os.environ.get("GNOME_AGENT_TOKEN"),
    )


def output(data):
    print(json.dumps(data, indent=2))


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="smash",
        description="GNOMEagents command center",
    )

    commands = parser.add_subparsers(
        dest="command",
        required=True,
    )

    for name in (
        "status",
        "agents",
        "jobs",
        "run",
        "heartbeat",
        "doctor",
        "test",
    ):
        commands.add_parser(name)

    args = parser.parse_args(argv)

    print(BANNER)

    if args.command == "doctor":
        url = os.getenv(
            "GNOMEBUSINESS_URL",
            "http://127.0.0.1:8000",
        )
        token = os.getenv("GNOME_AGENT_TOKEN")

        output({
            "server": url,
            "token_configured": bool(token),
            "python": sys.version.split()[0],
        })
        return 0 if token else 1

    if args.command == "test":
        return subprocess.call([
            sys.executable,
            "-m",
            "pytest",
            "-q",
        ])

    try:
        agent = worker()

        if args.command == "status":
            output(agent.request(
                "GET", "/api/health"
            ))

        elif args.command == "agents":
            output(agent.request(
                "GET", "/api/agents/me"
            ))

        elif args.command == "jobs":
            output(agent.request(
                "GET", "/api/workstation/jobs"
            ))

        elif args.command == "heartbeat":
            output(agent.request(
                "POST", "/api/agents/heartbeat"
            ))

        elif args.command == "run":
            output(agent.run_once())

        return 0

    except (
        httpx.HTTPError,
        ValueError,
    ) as error:
        print(
            f"SMASH ERROR: {error}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
