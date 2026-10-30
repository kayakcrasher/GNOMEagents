"""Persistent AI coding proposal integration tests."""

from app.tools.coding_coordinator import CodingCoordinator


class FakeModel:
    def decide(self, request):
        return {
            "action": "finish",
            "result": {
                "new_content": (
                    "def count_python_files(directory):\n"
                    "    return 0\n"
                ),
            },
        }


def test_generated_proposal_is_persistent(tmp_path):
    target = tmp_path / "utilities.py"
    original = "VALUE = 42\n"
    target.write_text(original)

    database = tmp_path / "vault.db"

    first = CodingCoordinator(
        tmp_path, database, model=FakeModel()
    )

    result = first.propose_function(
        "Count Python files",
        "count_python_files",
        ["directory"],
        "utilities.py",
    )

    assert result["status"] == "awaiting_approval"
    assert result["persistent"] is True
    assert target.read_text() == original

    second = CodingCoordinator(
        tmp_path, database, model=FakeModel()
    )

    proposal_id = result["proposal"]["id"]
    recovered = second.get(proposal_id)

    assert recovered["status"] == "awaiting_approval"
    assert "+def count_python_files" in recovered["diff"]
    assert target.read_text() == original


def test_generated_proposal_appears_in_inbox(tmp_path):
    target = tmp_path / "utilities.py"
    target.write_text("VALUE = 42\n")

    database = tmp_path / "vault.db"

    coordinator = CodingCoordinator(
        tmp_path, database, model=FakeModel()
    )

    result = coordinator.propose_function(
        "Count Python files",
        "count_python_files",
        ["directory"],
        "utilities.py",
    )

    restarted = CodingCoordinator(
        tmp_path, database, model=FakeModel()
    )

    inbox = restarted.pending()

    assert len(inbox) == 1
    assert inbox[0]["id"] == result["proposal"]["id"]
    assert inbox[0]["status"] == "awaiting_approval"
    assert target.read_text() == "VALUE = 42\n"
