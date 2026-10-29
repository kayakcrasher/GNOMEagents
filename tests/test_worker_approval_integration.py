import json

import httpx
import pytest

from app.workstation_worker import WorkstationWorker


def make_worker(approval_status=201):
    calls = []
    completed = []

    def handler(request):
        if (
            request.method == "POST"
            and request.url.path == "/api/agents/heartbeat"
        ):
            return httpx.Response(200, json={
                "status": "online"
            })

        path = request.url.path
        calls.append(path)

        if path == "/api/workstation/jobs":
            return httpx.Response(200, json={
                "jobs": [{
                    "id": 47,
                    "business_id": 7,
                    "status": "queued",
                    "kind": "lead:process",
                    "instructions": {
                        "message": "Need an urgent quote"
                    },
                }]
            })

        if path.endswith("/claim"):
            return httpx.Response(200, json={
                "status": "working"
            })

        if path == "/api/approvals/proposals":
            if approval_status != 201:
                return httpx.Response(
                    approval_status,
                    json={"detail": "Approval unavailable"},
                )

            return httpx.Response(201, json={
                "id": 99,
                "status": "pending",
            })

        if path.endswith("/complete"):
            completed.append(
                json.loads(request.content)["result"]
            )
            return httpx.Response(200, json={
                "status": "completed"
            })

        return httpx.Response(404)

    worker = WorkstationWorker(
        "http://testserver",
        "test-token",
        transport=httpx.MockTransport(handler),
    )

    return worker, calls, completed


def test_workflow_creates_approval_before_completion(
    tmp_path, monkeypatch
):
    monkeypatch.setenv(
        "GNOME_AGENT_MEMORY_DB",
        str(tmp_path / "memory.db"),
    )

    worker, calls, completed = make_worker()

    result = worker.run_once()

    assert result["status"] == "completed"
    assert completed[0]["proposal_id"] == 99

    assert calls.index(
        "/api/approvals/proposals"
    ) < next(
        i for i, path in enumerate(calls)
        if path.endswith("/complete")
    )


def test_approval_failure_prevents_completion():
    worker, calls, completed = make_worker(
        approval_status=403
    )

    with pytest.raises(httpx.HTTPStatusError):
        worker.run_once()

    assert completed == []
    assert not any(
        path.endswith("/complete")
        for path in calls
    )
