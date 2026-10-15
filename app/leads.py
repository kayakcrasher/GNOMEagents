from datetime import datetime, timezone

from pydantic import BaseModel, Field


class LeadCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    contact: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1, max_length=2000)


class Lead(LeadCreate):
    id: int
    status: str
    intent: str
    priority: str
    confidence: float
    recommended_action: str
    created_at: datetime


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AgentDecisionResult(BaseModel):
    action: str
    reason: str
    requires_approval: bool
    follow_up: bool


class LeadkeeperResult(BaseModel):
    lead: Lead
    draft_response: str
    knowledge_answer: str | None
    evidence: list[dict]
    decision: AgentDecisionResult
