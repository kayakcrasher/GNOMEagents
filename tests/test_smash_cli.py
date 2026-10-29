from app import smash


def test_doctor_without_token(monkeypatch, capsys):
    monkeypatch.delenv(
        "GNOME_AGENT_TOKEN",
        raising=False,
    )

    result = smash.main(["doctor"])

    assert result == 1
    assert "false" in capsys.readouterr().out.lower()


def test_doctor_with_token(monkeypatch):
    monkeypatch.setenv(
        "GNOME_AGENT_TOKEN",
        "test-token",
    )

    assert smash.main(["doctor"]) == 0


def test_status_command(monkeypatch, capsys):
    class FakeWorker:
        def request(self, method, path):
            assert method == "GET"
            assert path == "/api/health"
            return {"status": "operational"}

    monkeypatch.setattr(
        smash,
        "worker",
        lambda: FakeWorker(),
    )

    assert smash.main(["status"]) == 0
    assert "operational" in capsys.readouterr().out


def test_run_command(monkeypatch, capsys):
    class FakeWorker:
        def run_once(self):
            return {
                "job_id": 42,
                "status": "completed",
            }

    monkeypatch.setattr(
        smash,
        "worker",
        lambda: FakeWorker(),
    )

    assert smash.main(["run"]) == 0
    assert "completed" in capsys.readouterr().out
