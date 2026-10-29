import json

import httpx

from app.agent_memory import AgentMemory
from app.workstation_worker import WorkstationWorker


def test_worker_plans_and_remembers(tmp_path, monkeypatch):
    memory_path = tmp_path / "memory.db"
    monkeypatch.setenv(
        "GNOME_AGENT_MEMORY_DB",
        str(memory_path),
    )

    requests = []

    def handler(request):
        if (
            request.method == "POST"
            and request.url.path == "/api/agents/heartbeat"
        ):
            return httpx.Response(200, json={
                "status": "online"
            })

        requests.append(
            (request.method, request.url.path)
        )

        if request.method == "GET":
            return httpx.Response(200, json={
                "jobs": [{
                    "id": 42,
                    "business_id": 7,
                    "status": "queued",
                    "kind": "lead:analyze",
                    "instructions": {
                        "message": "Need a quote ASAP"
                    },
                }]
            })

        if request.url.path.endswith("/claim"):
            return httpx.Response(200, json={
                "status": "working"
            })

        if request.url.path.endswith("/complete"):
            body = json.loads(request.content)
            assert body["result"]["analysis"]["intent"] == (
                "quote_request"
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

    result = worker.run_once()

    assert result["status"] == "completed"

    records = AgentMemory(memory_path).recall(7)

    assert len(records) == 1
    assert records[0]["result"]["job_id"] == 42
    assert records[0]["result"]["analysis"]["intent"] == (
        "quote_request"
    )
    assert len(requests) == 3


def test_no_memory_when_completion_fails(
    tmp_path, monkeypatch
):
    memory_path = tmp_path / "memory.db"
    monkeypatch.setenv(
        "GNOME_AGENT_MEMORY_DB",
        str(memory_path),
    )

    def handler(request):
        if (
            request.method == "POST"
            and request.url.path == "/api/agents/heartbeat"
        ):
            return httpx.Response(200, json={
                "status": "online"
            })

        if request.method == "GET":
            return httpx.Response(200, json={
                "jobs": [{
                    "id": 43,
                    "business_id": 7,
                    "status": "queued",
                    "kind": "lead:analyze",
                    "instructions": {
                        "message": "Need a quote"
                    },
                }]
            })

        if request.url.path.endswith("/claim"):
            return httpx.Response(200, json={})

        return httpx.Response(
            500, json={"detail": "Server error"}
        )

    worker = WorkstationWorker(
        "http://testserver",
        "test-token",
        transport=httpx.MockTransport(handler),
    )

    try:
        worker.run_once()
    except httpx.HTTPStatusError:
        pass
    else:
        raise AssertionError("Expected HTTP failure")

    assert AgentMemory(memory_path).recall(7) == []
