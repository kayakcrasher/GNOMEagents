from app.actions import execute_action
from app.decisions import AgentDecision


def test_reply_waits_for_approval():
    decision = AgentDecision(
        action="reply",
        reason="Grounded knowledge available.",
        requires_approval=True,
        follow_up=False,
    )

    result = execute_action(
        decision,
        "Hi Alice, we install metal roofing.",
    )

    assert result.action == "reply"
    assert result.status == "awaiting_approval"


def test_approved_reply_becomes_ready():
    decision = AgentDecision(
        action="reply",
        reason="Grounded knowledge available.",
        requires_approval=True,
        follow_up=False,
    )

    result = execute_action(
        decision,
        "Hi Alice, we install metal roofing.",
        approved=True,
    )

    assert result.status == "ready"
    assert result.message == "Hi Alice, we install metal roofing."


def test_escalation_waits_for_approval():
    decision = AgentDecision(
        action="escalate",
        reason="Customer issue requires owner review.",
        requires_approval=True,
        follow_up=False,
    )

    result = execute_action(
        decision,
        "Customer requested a refund.",
    )

    assert result.status == "awaiting_approval"


def test_unknown_action_is_blocked():
    decision = AgentDecision(
        action="launch_moon_rocket",
        reason="GNOME got ambitious.",
        requires_approval=False,
        follow_up=False,
    )

    result = execute_action(
        decision,
        "TO MARS!",
    )

    assert result.status == "unsupported"
