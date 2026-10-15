from app.agent import analyze_lead


def test_quote_request():
    result = analyze_lead(
        "I need an estimate for a new deck."
    )

    assert result.intent == "quote_request"
    assert result.priority == "sales"
    assert result.recommended_action == "prepare_quote_response"


def test_urgent_quote():
    result = analyze_lead(
        "I need a quote ASAP for my roof."
    )

    assert result.intent == "quote_request"
    assert result.priority == "high"


def test_customer_issue_escalates():
    result = analyze_lead(
        "I have a problem and want a refund."
    )

    assert result.intent == "customer_issue"
    assert result.priority == "high"
    assert result.recommended_action == "escalate_to_owner"
