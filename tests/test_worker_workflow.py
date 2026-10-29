import json

import httpx
import pytest

from app.workstation_worker import WorkstationWorker


def make_worker(kind, message):
    calls = []

    def handler(request):
        if (
            request.method == "POST"
            and request.url.path == "/api/agents/heartbeat"
        ):
            return httpx.Response(200, json={
                "status": "online"
            })

        calls.append(request.url.path)

        if request.method == "GET":
            return httpx.Response(200, json={
                "jobs": [{
                    "id": 47,
                    "business_id": 7,
                    "kind": kind,
                    "status": "queued",
                    "instructions": {
                        "message": message,
                    },
                }]
            })

        if request.url.path == "/api/approvals/proposals":
            return httpx.Response(201, json={
                "id": 99,
                "status": "pending",
            })

        if request.url.path.endswith("/claim"):
            return httpx.Response(200, json={})

        if request.url.path.endswith("/complete"):
            result = json.loads(request.content)["result"]
            assert result["requires_human_review"]
            return httpx.Response(200, json={})

        return httpx.Response(404)

    return WorkstationWorker(
        "http://testserver",
        "test-token",
        transport=httpx.MockTransport(handler),
    ), calls


def test_worker_processes_workflow(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "GNOME_AGENT_MEMORY_DB",
        str(tmp_path / "memory.db"),
    )

    worker, calls = make_worker(
        "lead:process",
        "Need an urgent quote",
    )

    result = worker.run_once()

    assert result["status"] == "completed"
    assert result["analysis"]["decision"][
        "requires_human_review"
    ]
    assert any(path.endswith("/complete") for path in calls)


def test_worker_skips_unknown_job():
    worker, calls = make_worker(
        "system:delete",
        "Delete everything",
    )

    assert worker.run_once() == {"status": "idle"}
    assert len(calls) == 1


def test_worker_skips_invalid_message():
    worker, calls = make_worker(
        "lead:process",
        "",
    )

    assert worker.run_once() == {"status": "idle"}
    assert len(calls) == 1
