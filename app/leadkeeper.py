from app.agent import analyze_lead, draft_grounded_response
from app.database import add_lead
from app.decisions import decide_next_action
from app.gnomedata import GNOMEdataClient
from app.leads import LeadCreate, LeadkeeperResult


def process_lead(
    lead: LeadCreate,
    collection_id: str = "default",
    knowledge_client: GNOMEdataClient | None = None,
) -> LeadkeeperResult:
    """Process one lead using GNOMEdata business knowledge."""

    stored_lead = add_lead(lead)

    client = knowledge_client or GNOMEdataClient()

    knowledge = client.query(
        lead.message,
        collection_id=collection_id,
    )

    analysis = analyze_lead(lead.message)

    decision = decide_next_action(
        analysis,
        knowledge.answer,
    )

    draft = draft_grounded_response(
        lead.name,
        lead.message,
        knowledge.answer,
    )

    return LeadkeeperResult(
        lead=stored_lead,
        draft_response=draft,
        knowledge_answer=knowledge.answer,
        evidence=knowledge.evidence,
        decision={
            "action": decision.action,
            "reason": decision.reason,
            "requires_approval": decision.requires_approval,
            "follow_up": decision.follow_up,
        },
    )
