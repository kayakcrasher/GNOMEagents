from dataclasses import dataclass

from app.agent import LeadAnalysis


@dataclass(frozen=True)
class AgentDecision:
    action: str
    reason: str
    requires_approval: bool
    follow_up: bool


def decide_next_action(
    analysis: LeadAnalysis,
    knowledge_answer: str | None,
) -> AgentDecision:
    """Choose Leadkeeper's next action."""

    if analysis.intent == "customer_issue":
        return AgentDecision(
            action="escalate",
            reason="Customer issue requires owner review.",
            requires_approval=True,
            follow_up=False,
        )

    if knowledge_answer:
        return AgentDecision(
            action="reply",
            reason="GNOMEdata supplied grounded business knowledge.",
            requires_approval=True,
            follow_up=False,
        )

    if analysis.intent == "quote_request":
        return AgentDecision(
            action="request_details",
            reason="Quote request needs more job information.",
            requires_approval=True,
            follow_up=True,
        )

    return AgentDecision(
        action="reply",
        reason="General inquiry can receive the standard response.",
        requires_approval=True,
        follow_up=False,
    )
