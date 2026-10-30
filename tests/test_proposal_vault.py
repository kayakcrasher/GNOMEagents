"""Persistent proposal storage tests."""

from app.tools.proposal_vault import ProposalVault


def test_proposal_survives_restart(tmp_path):
    target = tmp_path / "example.py"
    target.write_text("VALUE = 1\n")

    database = tmp_path / "proposals.db"

    first = ProposalVault(tmp_path, database)

    proposal = first.save(
        "example.py",
        "VALUE = 2\n",
    )

    second = ProposalVault(tmp_path, database)

    recovered = second.get(proposal["id"])

    assert recovered["status"] == "awaiting_approval"
    assert recovered["after_content"] == "VALUE = 2\n"
    assert recovered["path"] == "example.py"
    assert target.read_text() == "VALUE = 1\n"


def test_pending_proposals_are_listed(tmp_path):
    target = tmp_path / "example.py"
    target.write_text("VALUE = 1\n")

    database = tmp_path / "proposals.db"

    vault = ProposalVault(tmp_path, database)

    proposal = vault.save(
        "example.py",
        "VALUE = 3\n",
    )

    restarted = ProposalVault(tmp_path, database)

    pending = restarted.pending()

    assert len(pending) == 1
    assert pending[0]["id"] == proposal["id"]
    assert pending[0]["status"] == "awaiting_approval"
    assert target.read_text() == "VALUE = 1\n"
