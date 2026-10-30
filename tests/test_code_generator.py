"""Code generation proposal tests."""

import pytest

from app.tools.code_generator import CodeGenerator
from app.tools.registry import ToolError


class FakeModel:
    def __init__(self, decision):
        self.decision = decision
        self.request = None

    def decide(self, request):
        self.request = request
        return self.decision


def test_generates_reviewable_patch(tmp_path):
    target = tmp_path / "example.py"
    target.write_text("VALUE = 1\n")

    model = FakeModel({
        "action": "finish",
        "result": {
            "new_content": "VALUE = 2\n",
        },
    })

    generator = CodeGenerator(tmp_path, model=model)

    proposal = generator.propose(
        "Change VALUE to 2",
        "example.py",
    )

    assert proposal["status"] == "awaiting_approval"
    assert "-VALUE = 1" in proposal["diff"]
    assert "+VALUE = 2" in proposal["diff"]
    assert target.read_text() == "VALUE = 1\n"
    assert model.request["original_content"] == (
        "VALUE = 1\n"
    )


def test_rejects_missing_generated_code(tmp_path):
    target = tmp_path / "example.py"
    target.write_text("VALUE = 1\n")

    model = FakeModel({
        "action": "finish",
        "result": {"summary": "Done"},
    })

    generator = CodeGenerator(tmp_path, model=model)

    with pytest.raises(ToolError, match="Missing generated"):
        generator.propose(
            "Change VALUE",
            "example.py",
        )

    assert target.read_text() == "VALUE = 1\n"


def test_rejects_missing_target(tmp_path):
    model = FakeModel({
        "action": "finish",
        "result": {"new_content": "VALUE = 2\n"},
    })

    generator = CodeGenerator(tmp_path, model=model)

    with pytest.raises(ToolError, match="File not found"):
        generator.propose(
            "Change VALUE",
            "missing.py",
        )


def test_rejects_empty_objective(tmp_path):
    target = tmp_path / "example.py"
    target.write_text("VALUE = 1\n")

    generator = CodeGenerator(
        tmp_path,
        model=FakeModel({}),
    )

    with pytest.raises(ToolError, match="objective"):
        generator.propose("", "example.py")


def test_rejects_invalid_python(tmp_path):
    target = tmp_path / "example.py"
    target.write_text("VALUE = 1\n")

    model = FakeModel({
        "action": "finish",
        "result": {
            "new_content": "def broken(:\n",
        },
    })

    generator = CodeGenerator(tmp_path, model=model)

    with pytest.raises(ToolError, match="invalid syntax"):
        generator.propose(
            "Improve example.py",
            "example.py",
        )

    assert target.read_text() == "VALUE = 1\n"
