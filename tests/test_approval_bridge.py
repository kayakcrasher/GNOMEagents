import httpx
import pytest

from app.approval_bridge import ApprovalBridge


def test_proposal_submitted():
    captured = {}

    def handler(request):
        captured["path"] = request.url.path
        captured["authorization"] = request.headers.get(
            "authorization"
        )
        captured["payload"] = __import__("json").loads(
            request.content
        )
        return httpx.Response(
            201, json={"id": 12, "status": "pending"}
        )

    bridge = ApprovalBridge(
        "http://testserver",
        "test-token",
        transport=httpx.MockTransport(handler),
    )

    result = bridge.submit(
        "Alice", "Can I get a quote?"
    )

    assert result["status"] == "pending"
    assert result["proposal_id"] == 12
    assert result["executed"] is False
    assert captured["path"] == "/api/approvals/proposals"
    assert captured["authorization"] == "Bearer test-token"
    assert captured["payload"]["action"] == "outreach:draft"
    assert captured["payload"]["payload"]["draft"]
    assert captured["payload"]["payload"][
        "requires_human_approval"
    ]


def test_rejected_credentials():
    def handler(request):
        return httpx.Response(
            403, json={"detail": "Permission denied"}
        )

    bridge = ApprovalBridge(
        "http://testserver",
        "invalid-token",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(httpx.HTTPStatusError):
        bridge.submit("Bob", "Need an estimate")


def test_missing_token():
    with pytest.raises(ValueError):
        ApprovalBridge("http://testserver", "")


def test_invalid_inquiry_never_submitted():
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(201, json={"id": 1})

    bridge = ApprovalBridge(
        "http://testserver",
        "test-token",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(ValueError):
        bridge.submit("Alice", "")

    assert calls == []
