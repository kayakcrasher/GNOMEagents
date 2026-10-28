class WorkflowApprovalError(RuntimeError):
    pass


def submit_workflow_approval(worker, job, workflow):
    """Submit a prepared lead workflow for human review."""

    if job.get("kind") != "lead:process":
        raise WorkflowApprovalError(
            "Unsupported approval workflow"
        )

    if workflow.get("status") != "awaiting_approval":
        raise WorkflowApprovalError(
            "Workflow is not ready for approval"
        )

    result = workflow.get("result")

    if not isinstance(result, dict):
        raise WorkflowApprovalError(
            "Workflow result missing"
        )

    decision = result.get("decision", {})

    if not decision.get("requires_human_review"):
        raise WorkflowApprovalError(
            "Human review was not requested"
        )

    response = worker.request(
        "POST",
        "/api/approvals/proposals",
        json={
            "action": "lead:review",
            "title": "Leadkeeper workflow review",
            "payload": {
                "job_id": job["id"],
                "analysis": result.get("analysis"),
                "decision": decision,
                "requires_human_approval": True,
            },
        },
    )

    if response.get("status") != "pending":
        raise WorkflowApprovalError(
            "Approval proposal not accepted"
        )

    proposal_id = response.get("id")

    if not isinstance(proposal_id, int) or proposal_id < 1:
        raise WorkflowApprovalError(
            "Invalid approval proposal ID"
        )

    return proposal_id
