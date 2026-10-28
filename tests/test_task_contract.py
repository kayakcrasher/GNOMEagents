import pytest
from pydantic import ValidationError

from app.task_contract import AgentTask, TaskResult


def make_task():
    return AgentTask(
        business_id=1,
        agent="Leadkeeper",
        kind="lead:analyze",
        instructions={"lead_id": 42},
    )


def test_task_defaults_to_queued():
    task = make_task()

    assert task.status == "queued"
    assert task.task_id


def test_task_ids_are_unique():
    assert make_task().task_id != make_task().task_id


def test_task_requires_valid_business():
    with pytest.raises(ValidationError):
        AgentTask(
            business_id=0,
            agent="Leadkeeper",
            kind="lead:analyze",
            instructions={},
        )


def test_result_supports_approval():
    task = make_task()

    result = TaskResult(
        task_id=task.task_id,
        status="awaiting_approval",
        output={"draft": "Hello customer"},
        requires_approval=True,
    )

    assert result.requires_approval
    assert result.status == "awaiting_approval"


def test_invalid_status_rejected():
    with pytest.raises(ValidationError):
        TaskResult(
            task_id="123",
            status="unlimited_power",
        )
