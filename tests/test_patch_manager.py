import pytest

from app.tools.patches import PatchManager
from app.tools.registry import ToolError


def test_proposal_does_not_modify_file(tmp_path):
    target = tmp_path / "app.py"
    target.write_text("VALUE = 1\n")

    manager = PatchManager(tmp_path)

    proposal = manager.propose(
        "app.py",
        "VALUE = 2\n",
    )

    assert proposal["status"] == "awaiting_approval"
    assert "-VALUE = 1" in proposal["diff"]
    assert "+VALUE = 2" in proposal["diff"]
    assert target.read_text() == "VALUE = 1\n"


def test_approved_patch_applies(tmp_path):
    target = tmp_path / "app.py"
    target.write_text("VALUE = 1\n")

    manager = PatchManager(tmp_path)
    proposal = manager.propose(
        "app.py", "VALUE = 2\n"
    )

    result = manager.apply(
        proposal["id"],
        approved=True,
    )

    assert result["status"] == "applied"
    assert target.read_text() == "VALUE = 2\n"


def test_unapproved_patch_denied(tmp_path):
    target = tmp_path / "app.py"
    target.write_text("VALUE = 1\n")

    manager = PatchManager(tmp_path)
    proposal = manager.propose(
        "app.py", "VALUE = 2\n"
    )

    with pytest.raises(ToolError):
        manager.apply(proposal["id"])

    assert target.read_text() == "VALUE = 1\n"


def test_changed_file_blocks_patch(tmp_path):
    target = tmp_path / "app.py"
    target.write_text("VALUE = 1\n")

    manager = PatchManager(tmp_path)
    proposal = manager.propose(
        "app.py", "VALUE = 2\n"
    )

    target.write_text("VALUE = 99\n")

    with pytest.raises(ToolError):
        manager.apply(
            proposal["id"],
            approved=True,
        )

    assert target.read_text() == "VALUE = 99\n"


def test_path_escape_denied(tmp_path):
    manager = PatchManager(tmp_path)

    with pytest.raises(ToolError):
        manager.propose(
            "../outside.py",
            "SECRET = True\n",
        )


def test_proposal_cannot_be_reused(tmp_path):
    target = tmp_path / "app.py"
    target.write_text("VALUE = 1\n")

    manager = PatchManager(tmp_path)
    proposal = manager.propose(
        "app.py", "VALUE = 2\n"
    )

    manager.apply(proposal["id"], approved=True)

    with pytest.raises(ToolError):
        manager.apply(
            proposal["id"],
            approved=True,
        )
