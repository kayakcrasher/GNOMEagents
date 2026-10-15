from app.agent import analyze_lead
from app.decisions import decide_next_action


def test_grounded_question_gets_reply():
    analysis = analyze_lead(
        "Do you install metal roofing?"
    )

    decision = decide_next_action(
        analysis,
        "We install metal roofing.",
    )

    assert decision.action == "reply"
    assert decision.requires_approval is True
    assert decision.follow_up is False


def test_complaint_escalates_even_with_knowledge():
    analysis = analyze_lead(
        "I'm angry and want a refund."
    )

    decision = decide_next_action(
        analysis,
        "Refunds may be available.",
    )

    assert decision.action == "escalate"
    assert decision.requires_approval is True
    assert decision.follow_up is False


def test_quote_without_knowledge_requests_details():
    analysis = analyze_lead(
        "Can I get an estimate?"
    )

    decision = decide_next_action(
        analysis,
        None,
    )

    assert decision.action == "request_details"
    assert decision.requires_approval is True
    assert decision.follow_up is True


def test_general_inquiry_has_safe_fallback():
    analysis = analyze_lead(
        "Hello, I have a question."
    )

    decision = decide_next_action(
        analysis,
        None,
    )

    assert decision.action == "reply"
    assert decision.requires_approval is True
