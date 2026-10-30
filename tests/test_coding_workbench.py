"""Tests for GNOME coding workbench."""

import pytest

from app.tools.coding_workbench import CodingWorkbench
from app.tools.registry import ToolError


class FakeModel:
    def __init__(self, source):
        self.source = source

    def decide(self, request):
        return {
            "action": "finish",
            "result": {
                "new_content": self.source,
            },
        }


def test_generates_valid_function():
    model = FakeModel(
        "def add(a, b):\n"
        "    return a + b\n"
    )

    workbench = CodingWorkbench(model)

    result = workbench.generate_function(
        "Add two numbers",
        "add",
        ["a", "b"],
    )

    assert result["syntax_valid"]
    assert result["signature_valid"]
    assert result["tests_run"] is False


def test_rejects_wrong_function():
    model = FakeModel(
        "def subtract(a, b):\n"
        "    return a - b\n"
    )

    workbench = CodingWorkbench(model)

    with pytest.raises(ToolError, match="Wrong function"):
        workbench.generate_function(
            "Add numbers",
            "add",
            ["a", "b"],
        )


def test_rejects_wrong_parameters():
    model = FakeModel(
        "def add(x, y):\n"
        "    return x + y\n"
    )

    workbench = CodingWorkbench(model)

    with pytest.raises(ToolError, match="parameters"):
        workbench.generate_function(
            "Add numbers",
            "add",
            ["a", "b"],
        )


def test_rejects_invalid_syntax():
    model = FakeModel("def add(:\n")

    workbench = CodingWorkbench(model)

    with pytest.raises(ToolError, match="syntax"):
        workbench.generate_function(
            "Add numbers",
            "add",
            ["a", "b"],
        )


def test_rejects_extra_functions():
    model = FakeModel(
        "def add(a, b):\n"
        "    return a + b\n\n"
        "def surprise():\n"
        "    return 42\n"
    )

    workbench = CodingWorkbench(model)

    with pytest.raises(ToolError, match="one top-level"):
        workbench.generate_function(
            "Add numbers",
            "add",
            ["a", "b"],
        )
