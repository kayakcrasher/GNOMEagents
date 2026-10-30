"""Approval gate security tests."""

import pytest

from app.tools.proposal_vault import ProposalVault
from app.tools.registry import ToolError


@pytest.fixture
def setup_vault(tmp_path):
    target = tmp_path / "example.py"
    target.write_text("VALUE = 1\n")

    database = tmp_path / "vault.db"
    vault = ProposalVault(tmp_path, database)

    proposal = vault.save(
        "example.py",
        "VALUE = 2\n",
    )

    return tmp_path, database, target, proposal


def test_approval_required(setup_vault):
    root, database, target, proposal = setup_vault
    vault = ProposalVault(root, database)

    with pytest.raises(ToolError, match="approval"):
        vault.approve(proposal["id"])

    assert target.read_text() == "VALUE = 1\n"


def test_approval_survives_restart(setup_vault):
    root, database, target, proposal = setup_vault
    restarted = ProposalVault(root, database)

    result = restarted.approve(
        proposal["id"],
        approved=True,
    )

    assert result["status"] == "applied"
    assert target.read_text() == "VALUE = 2\n"

    again = ProposalVault(root, database)
    assert again.get(proposal["id"])["status"] == "applied"


def test_stale_file_rejected(setup_vault):
    root, database, target, proposal = setup_vault
    target.write_text("VALUE = 99\n")

    restarted = ProposalVault(root, database)

    with pytest.raises(ToolError, match="changed"):
        restarted.approve(
            proposal["id"],
            approved=True,
        )

    assert target.read_text() == "VALUE = 99\n"
    assert restarted.get(proposal["id"])["status"] == (
        "awaiting_approval"
    )


def test_rejection_preserves_file(setup_vault):
    root, database, target, proposal = setup_vault
    restarted = ProposalVault(root, database)

    result = restarted.reject(proposal["id"])

    assert result["status"] == "rejected"
    assert target.read_text() == "VALUE = 1\n"

    with pytest.raises(ToolError, match="not awaiting"):
        restarted.approve(
            proposal["id"],
            approved=True,
        )


def test_cannot_apply_twice(setup_vault):
    root, database, target, proposal = setup_vault
    restarted = ProposalVault(root, database)

    restarted.approve(proposal["id"], approved=True)

    with pytest.raises(ToolError, match="not awaiting"):
        restarted.approve(proposal["id"], approved=True)
