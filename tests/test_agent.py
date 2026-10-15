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


def test_quote_response():
    from app.agent import draft_response

    response = draft_response(
        "Alice",
        "Can I get an estimate for my driveway?",
    )

    assert "Alice" in response
    assert "estimate" in response.lower()


def test_complaint_response_does_not_promise_refund():
    from app.agent import draft_response

    response = draft_response(
        "Sam",
        "I'm angry and want a refund.",
    )

    assert "owner" in response.lower()
    assert "refund has been issued" not in response.lower()


def test_grounded_response_uses_business_knowledge():
    from app.agent import draft_grounded_response

    response = draft_grounded_response(
        "Alice",
        "What is Oakville known for?",
        "Randy sells pies from his home in Oakville.",
    )

    assert "Alice" in response
    assert "Randy sells pies" in response


def test_grounded_response_falls_back_without_knowledge():
    from app.agent import draft_grounded_response

    response = draft_grounded_response(
        "Bob",
        "I need an estimate for a deck.",
        None,
    )

    assert "Bob" in response
    assert "estimate" in response.lower()


def test_complaint_still_escalates_with_knowledge():
    from app.agent import draft_grounded_response

    response = draft_grounded_response(
        "Sam",
        "I'm angry and want a refund.",
        "Refunds are normally available.",
    )

    assert "owner" in response.lower()
    assert "refunds are normally available" not in response.lower()
