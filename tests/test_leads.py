from fastapi.testclient import TestClient

from app.main import app


def test_create_and_list_lead(tmp_path, monkeypatch):
    import app.database as database

    monkeypatch.setattr(
        database,
        "DB_PATH",
        tmp_path / "test.db",
    )

    with TestClient(app) as client:
        response = client.post(
            "/leads",
            json={
                "name": "Bob Builder",
                "contact": "bob@example.com",
                "message": "I need an estimate for a new deck.",
            },
        )

        assert response.status_code == 201

        lead = response.json()

        assert lead["name"] == "Bob Builder"
        assert lead["status"] == "new"
        assert lead["id"] == 1

        response = client.get("/leads")

        assert response.status_code == 200

        leads = response.json()

        assert len(leads) == 1
        assert leads[0]["message"] == (
            "I need an estimate for a new deck."
        )
