from app.workflow_approvals import submit_workflow_approval


class FakeWorker:
    def __init__(self):
        self.requests = []
        self.proposals = {}
        self.next_id = 100

    def request(self, method, path, **kwargs):
        assert method == "POST"
        assert path == "/api/approvals/proposals"

        data = kwargs["json"]
        self.requests.append(data)

        key = data["idempotency_key"]

        if key not in self.proposals:
            self.proposals[key] = self.next_id
            self.next_id += 1

        return {
            "id": self.proposals[key],
            "status": "pending",
        }


def workflow():
    return {
        "status": "awaiting_approval",
        "result": {
            "analysis": {
                "priority": "high",
            },
            "decision": {
                "action": "prepare_response",
                "requires_human_review": True,
            },
        },
    }


def test_same_job_reuses_proposal():
    worker = FakeWorker()
    job = {
        "id": 47,
        "kind": "lead:process",
    }

    first = submit_workflow_approval(
        worker, job, workflow()
    )
    second = submit_workflow_approval(
        worker, job, workflow()
    )

    assert first == second == 100
    assert len(worker.proposals) == 1

    assert (
        worker.requests[0]["idempotency_key"]
        == "lead:process:job:47"
    )


def test_different_jobs_get_different_keys():
    worker = FakeWorker()

    first = submit_workflow_approval(
        worker,
        {"id": 47, "kind": "lead:process"},
        workflow(),
    )

    second = submit_workflow_approval(
        worker,
        {"id": 48, "kind": "lead:process"},
        workflow(),
    )

    assert first != second
    assert len(worker.proposals) == 2
