from app.agent_workflow import AgentWorkflow


SUPPORTED_WORKFLOWS = {
    "lead:process",
}


def dispatch_workflow(kind, instructions):
    if kind not in SUPPORTED_WORKFLOWS:
        raise ValueError("Unsupported workflow")

    if not isinstance(instructions, dict):
        raise ValueError("Instructions must be an object")

    state = AgentWorkflow(max_steps=3).run(
        kind,
        instructions,
    )

    return {
        "status": state.status,
        "steps": state.steps,
        "result": state.result,
        "trace": state.trace,
        "requires_human_review": (
            state.status == "awaiting_approval"
        ),
    }
