from app.gnomedata import KnowledgeResult
from app.leads import LeadCreate
from app.leadkeeper import process_lead


class FakeGNOMEdataClient:
    def query(
        self,
        question: str,
        collection_id: str = "default",
    ) -> KnowledgeResult:
        return KnowledgeResult(
            question=question,
            collection_id=collection_id,
            answer="We install metal roofing.",
            facts=[],
            evidence=[
                {
                    "board_id": "services:1",
                    "source_name": "services.txt",
                    "text": "We install metal roofing.",
                    "score": 0.95,
                }
            ],
            online_used=False,
        )


def test_process_lead_uses_gnomedata(
    tmp_path,
    monkeypatch,
):
    import app.database as database

    monkeypatch.setattr(
        database,
        "DB_PATH",
        tmp_path / "leadkeeper.db",
    )

    database.initialize_database()

    lead = LeadCreate(
        name="Alice",
        contact="alice@example.com",
        message="Do you install metal roofing?",
    )

    result = process_lead(
        lead,
        collection_id="demo_roofing",
        knowledge_client=FakeGNOMEdataClient(),
    )

    assert result.lead.name == "Alice"
    assert result.knowledge_answer == (
        "We install metal roofing."
    )
    assert "metal roofing" in result.draft_response
    assert result.evidence[0]["source_name"] == (
        "services.txt"
    )
