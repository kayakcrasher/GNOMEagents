import pytest

from app.workflow_dispatch import dispatch_workflow


def test_dispatch_lead_workflow():
    result = dispatch_workflow(
        "lead:process",
        {"message": "Need an urgent quote"},
    )

    assert result["status"] == "awaiting_approval"
    assert result["requires_human_review"]
    assert result["steps"] == 1


def test_dispatch_rejects_unknown_workflow():
    with pytest.raises(ValueError):
        dispatch_workflow(
            "system:delete",
            {"message": "anything"},
        )


def test_dispatch_rejects_invalid_instructions():
    with pytest.raises(ValueError):
        dispatch_workflow(
            "lead:process",
            "not a dictionary",
        )


def test_dispatch_blocks_empty_message():
    result = dispatch_workflow(
        "lead:process",
        {"message": ""},
    )

    assert result["status"] == "blocked"
    assert not result["requires_human_review"]
