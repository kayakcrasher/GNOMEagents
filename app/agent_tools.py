from dataclasses import asdict

from app.agent import analyze_lead
from app.runtime import AgentRuntime, Tool


def analyze_lead_tool(args):
    message = args.get("message")

    if not isinstance(message, str):
        raise ValueError("Message must be text")

    if not 1 <= len(message.strip()) <= 2000:
        raise ValueError("Invalid message length")

    return asdict(analyze_lead(message))


def build_runtime():
    runtime = AgentRuntime(max_steps=5)

    runtime.register(Tool(
        name="lead.analyze",
        handler=analyze_lead_tool,
    ))

    return runtime
