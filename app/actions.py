from dataclasses import dataclass

from app.decisions import AgentDecision


@dataclass(frozen=True)
class ActionResult:
    action: str
    status: str
    message: str


def execute_action(
    decision: AgentDecision,
    draft_response: str,
    *,
    approved: bool = False,
) -> ActionResult:
    """Execute a Leadkeeper decision within its permissions."""

    if decision.requires_approval and not approved:
        return ActionResult(
            action=decision.action,
            status="awaiting_approval",
            message="Action prepared but requires human approval.",
        )

    if decision.action == "reply":
        return ActionResult(
            action="reply",
            status="ready",
            message=draft_response,
        )

    if decision.action == "request_details":
        return ActionResult(
            action="request_details",
            status="ready",
            message=draft_response,
        )

    if decision.action == "escalate":
        return ActionResult(
            action="escalate",
            status="ready",
            message="Lead requires owner review.",
        )

    return ActionResult(
        action=decision.action,
        status="unsupported",
        message="No executor exists for this action.",
    )
