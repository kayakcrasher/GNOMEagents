from datetime import datetime, timezone
from pydantic import BaseModel, Field


class LeadCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    contact: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1, max_length=2000)


class Lead(LeadCreate):
    id: int
    status: str
    created_at: datetime


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
