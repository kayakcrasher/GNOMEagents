import httpx

from app.gnomedata import GNOMEdataClient


def test_query_gnomedata(monkeypatch):
    def fake_post(url, json, timeout):
        assert url == "http://127.0.0.1:8001/api/query"
        assert json["question"] == "Do you install metal roofs?"
        assert json["collection_id"] == "demo_roofing"
        assert json["allow_online"] is False

        return httpx.Response(
            200,
            json={
                "question": json["question"],
                "collection_id": json["collection_id"],
                "online_used": False,
                "answer": "Yes, metal roofing is offered.",
                "facts": [],
                "evidence": [
                    {
                        "board_id": "board-1",
                        "source_name": "services.txt",
                        "text": "We install metal roofing.",
                        "score": 0.97,
                    }
                ],
            },
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(
        "app.gnomedata.httpx.post",
        fake_post,
    )

    client = GNOMEdataClient()

    result = client.query(
        "Do you install metal roofs?",
        collection_id="demo_roofing",
    )

    assert result.collection_id == "demo_roofing"
    assert result.online_used is False
    assert result.answer == "Yes, metal roofing is offered."
    assert result.evidence[0]["source_name"] == "services.txt"
