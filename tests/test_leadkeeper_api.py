from fastapi.testclient import TestClient

import app.main as main


def test_leadkeeper_process_endpoint(
    tmp_path,
    monkeypatch,
):
    import app.database as database

    monkeypatch.setattr(
        database,
        "DB_PATH",
        tmp_path / "leadkeeper_api.db",
    )

    def fake_process_lead(
        lead,
        collection_id="default",
    ):
        from app.leads import Lead, LeadkeeperResult
        from app.leads import utc_now

        return LeadkeeperResult(
            lead=Lead(
                id=1,
                name=lead.name,
                contact=lead.contact,
                message=lead.message,
                status="new",
                intent="general_inquiry",
                priority="normal",
                confidence=0.65,
                recommended_action="prepare_response",
                created_at=utc_now(),
            ),
            draft_response=(
                f"Hi {lead.name}, we install metal roofing."
            ),
            knowledge_answer=(
                "We install metal roofing."
            ),
            evidence=[
                {
                    "source_name": "services.txt",
                    "text": "We install metal roofing.",
                    "score": 0.95,
                }
            ],
            decision={
                "action": "reply",
                "reason": "GNOMEdata supplied grounded business knowledge.",
                "requires_approval": True,
                "follow_up": False,
            },
        )

    monkeypatch.setattr(
        main,
        "process_lead",
        fake_process_lead,
    )

    with TestClient(main.app) as client:
        response = client.post(
            "/leadkeeper/process",
            params={
                "collection_id": "demo_roofing",
            },
            json={
                "name": "Alice",
                "contact": "alice@example.com",
                "message": "Do you install metal roofing?",
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["lead"]["name"] == "Alice"
    assert data["knowledge_answer"] == (
        "We install metal roofing."
    )
    assert "metal roofing" in data["draft_response"]


def test_leadkeeper_result_exposes_decision():
    from app.leads import AgentDecisionResult

    decision = AgentDecisionResult(
        action="reply",
        reason="Grounded knowledge available.",
        requires_approval=True,
        follow_up=False,
    )

    assert decision.action == "reply"
    assert decision.requires_approval is True
    assert decision.follow_up is False
