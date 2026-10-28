from dataclasses import dataclass, field

from app.agent import analyze_lead, draft_response


@dataclass
class PilotResult:
    status: str
    analysis: dict = field(default_factory=dict)
    draft: str = ""
    evaluation: dict = field(default_factory=dict)
    trace: list = field(default_factory=list)


def evaluate_draft(name, message, draft):
    issues = []

    if not draft.strip():
        issues.append("empty_draft")

    if len(draft) > 1000:
        issues.append("draft_too_long")

    if name.strip() not in draft:
        issues.append("missing_customer_name")

    risky_phrases = (
        "guaranteed",
        "your appointment is confirmed",
        "we have charged",
        "payment received",
    )

    if any(phrase in draft.lower() for phrase in risky_phrases):
        issues.append("unverified_commitment")

    return {
        "passed": not issues,
        "issues": issues,
        "requires_human_approval": True,
    }


def process_inquiry(name, message):
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 100:
        raise ValueError("Invalid customer name")

    if not isinstance(message, str) or not 1 <= len(message.strip()) <= 2000:
        raise ValueError("Invalid inquiry")

    from dataclasses import asdict

    trace = []

    analysis = asdict(analyze_lead(message))
    trace.append({
        "step": "analyze",
        "intent": analysis["intent"],
    })

    draft = draft_response(name.strip(), message)
    trace.append({
        "step": "draft",
        "created": True,
    })

    evaluation = evaluate_draft(name.strip(), message, draft)
    trace.append({
        "step": "evaluate",
        "passed": evaluation["passed"],
    })

    status = (
        "awaiting_approval"
        if evaluation["passed"]
        else "needs_revision"
    )

    return PilotResult(
        status=status,
        analysis=analysis,
        draft=draft,
        evaluation=evaluation,
        trace=trace,
    )
