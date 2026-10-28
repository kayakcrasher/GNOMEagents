import pytest

from app.workflow_approvals import (
    WorkflowApprovalError,
    submit_workflow_approval,
)


class FakeWorker:
    def __init__(self):
        self.calls = []

    def request(self, method, path, **kwargs):
        self.calls.append((method, path, kwargs))
        return {"id": 77, "status": "pending"}


def ready():
    return {
        "status": "awaiting_approval",
        "result": {
            "analysis": {"intent": "quote_request"},
            "decision": {
                "action": "prepare_response",
                "requires_human_review": True,
            },
        },
    }


def test_submits_pending_proposal():
    worker = FakeWorker()

    proposal_id = submit_workflow_approval(
        worker,
        {"id": 42, "kind": "lead:process"},
        ready(),
    )

    assert proposal_id == 77
    assert worker.calls[0][1] == (
        "/api/approvals/proposals"
    )
    assert worker.calls[0][2]["json"]["action"] == (
        "lead:review"
    )


def test_blocked_workflow_cannot_propose():
    worker = FakeWorker()
    workflow = ready()
    workflow["status"] = "blocked"

    with pytest.raises(WorkflowApprovalError):
        submit_workflow_approval(
            worker,
            {"id": 42, "kind": "lead:process"},
            workflow,
        )

    assert worker.calls == []


def test_unapproved_decision_cannot_propose():
    worker = FakeWorker()
    workflow = ready()
    workflow["result"]["decision"][
        "requires_human_review"
    ] = False

    with pytest.raises(WorkflowApprovalError):
        submit_workflow_approval(
            worker,
            {"id": 42, "kind": "lead:process"},
            workflow,
        )

    assert worker.calls == []


def test_rejects_invalid_proposal_id():
    class BadWorker(FakeWorker):
        def request(self, *args, **kwargs):
            return {"id": None, "status": "pending"}

    with pytest.raises(WorkflowApprovalError):
        submit_workflow_approval(
            BadWorker(),
            {"id": 42, "kind": "lead:process"},
            ready(),
        )
