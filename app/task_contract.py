from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


TaskStatus = Literal[
    "queued",
    "running",
    "awaiting_approval",
    "completed",
    "failed",
]


class AgentTask(BaseModel):
    task_id: str = Field(
        default_factory=lambda: str(uuid4())
    )
    business_id: int = Field(gt=0)
    agent: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    instructions: dict[str, Any]
    status: TaskStatus = "queued"
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )


class TaskResult(BaseModel):
    task_id: str
    status: TaskStatus
    output: dict[str, Any] = Field(
        default_factory=dict
    )
    requires_approval: bool = False
    error: str | None = None
