"""Tests for the review-only coding bridge."""

from app.tools.coding_bridge import CodingBridge
from app.tools.registry import ToolError


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


def test_bridge_creates_patch_without_editing(tmp_path):
    target = tmp_path / "utilities.py"
    original = "VALUE = 42\n"
    target.write_text(original)

    bridge = CodingBridge(tmp_path, FakeModel())

    result = bridge.propose_function(
        "Count Python files",
        "count_python_files",
        ["directory"],
        "utilities.py",
    )

    assert result["status"] == "awaiting_approval"
    assert "+def count_python_files" in (
        result["proposal"]["diff"]
    )
    assert target.read_text() == original
    assert result["generation"]["tests_run"] is False


def test_bridge_rejects_non_python_target(tmp_path):
    bridge = CodingBridge(tmp_path, FakeModel())

    try:
        bridge.propose_function(
            "Count files", "count_python_files",
            ["directory"], "notes.txt"
        )
    except ToolError:
        pass
    else:
        raise AssertionError("Expected ToolError")


def test_bridge_rejects_duplicate_function(tmp_path):
    target = tmp_path / "utilities.py"
    target.write_text(
        "def count_python_files(directory):\n"
        "    return 1\n"
    )

    bridge = CodingBridge(tmp_path, FakeModel())

    try:
        bridge.propose_function(
            "Count files",
            "count_python_files",
            ["directory"],
            "utilities.py",
        )
    except ToolError as error:
        assert "already exists" in str(error)
    else:
        raise AssertionError("Duplicate function accepted")


class UnsafeModel:
    def decide(self, request):
        return {
            "action": "finish",
            "result": {
                "new_content": (
                    "print('unexpected execution')\n"
                    "def count_python_files(directory):\n"
                    "    return 0\n"
                ),
            },
        }


def test_bridge_rejects_top_level_execution(tmp_path):
    target = tmp_path / "utilities.py"
    target.write_text("VALUE = 42\n")

    bridge = CodingBridge(tmp_path, UnsafeModel())

    try:
        bridge.propose_function(
            "Count files",
            "count_python_files",
            ["directory"],
            "utilities.py",
        )
    except ToolError:
        pass
    else:
        raise AssertionError("Unsafe code accepted")


def test_bridge_rejects_duplicate_function(tmp_path):
    target = tmp_path / "utilities.py"
    target.write_text(
        "def count_python_files(directory):\n"
        "    return 1\n"
    )

    bridge = CodingBridge(tmp_path, FakeModel())

    try:
        bridge.propose_function(
            "Count files",
            "count_python_files",
            ["directory"],
            "utilities.py",
        )
    except ToolError as error:
        assert "already exists" in str(error)
    else:
        raise AssertionError("Duplicate function accepted")


class UnsafeModel:
    def decide(self, request):
        return {
            "action": "finish",
            "result": {
                "new_content": (
                    "print('unexpected execution')\n"
                    "def count_python_files(directory):\n"
                    "    return 0\n"
                ),
            },
        }


def test_bridge_rejects_top_level_execution(tmp_path):
    target = tmp_path / "utilities.py"
    target.write_text("VALUE = 42\n")

    bridge = CodingBridge(tmp_path, UnsafeModel())

    try:
        bridge.propose_function(
            "Count files",
            "count_python_files",
            ["directory"],
            "utilities.py",
        )
    except ToolError:
        pass
    else:
        raise AssertionError("Unsafe code accepted")
