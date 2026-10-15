from dataclasses import asdict, dataclass


@dataclass
class LeadAnalysis:
    intent: str
    priority: str
    confidence: float
    recommended_action: str


def analyze_lead(message: str) -> LeadAnalysis:
    text = message.lower()

    quote_words = (
        "quote",
        "estimate",
        "price",
        "cost",
        "how much",
    )

    urgent_words = (
        "urgent",
        "emergency",
        "asap",
        "immediately",
    )

    complaint_words = (
        "complaint",
        "refund",
        "angry",
        "broken",
        "problem",
    )

    if any(word in text for word in complaint_words):
        return LeadAnalysis(
            intent="customer_issue",
            priority="high",
            confidence=0.90,
            recommended_action="escalate_to_owner",
        )

    if any(word in text for word in quote_words):
        priority = (
            "high"
            if any(word in text for word in urgent_words)
            else "sales"
        )

        return LeadAnalysis(
            intent="quote_request",
            priority=priority,
            confidence=0.90,
            recommended_action="prepare_quote_response",
        )

    return LeadAnalysis(
        intent="general_inquiry",
        priority="normal",
        confidence=0.65,
        recommended_action="prepare_response",
    )


def analysis_dict(message: str) -> dict:
    return asdict(analyze_lead(message))
