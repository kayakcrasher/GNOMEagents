import pytest

from app.tools.registry import ToolRegistry, ToolError
from app.tools.inspector import inspect_workspace


def test_lists_real_files(tmp_path):
    (tmp_path / "hello.py").write_text("print('hello')")

    tools = ToolRegistry(tmp_path)

    result = tools.execute(
        "files.list", {"path": "."}
    )

    assert any(
        entry["name"] == "hello.py"
        for entry in result["entries"]
    )


def test_reads_real_source(tmp_path):
    (tmp_path / "app.py").write_text("VALUE = 42")

    tools = ToolRegistry(tmp_path)

    result = tools.execute(
        "files.read", {"path": "app.py"}
    )

    assert result["content"] == "VALUE = 42"


def test_blocks_parent_escape(tmp_path):
    tools = ToolRegistry(tmp_path)

    with pytest.raises(ToolError):
        tools.execute(
            "files.read",
            {"path": "../secret.txt"},
        )


def test_blocks_absolute_paths(tmp_path):
    tools = ToolRegistry(tmp_path)

    with pytest.raises(ToolError):
        tools.execute(
            "files.read",
            {"path": "/etc/passwd"},
        )


def test_blocks_symlink_escape(tmp_path):
    outside = tmp_path.parent / "outside-secret.txt"
    outside.write_text("secret")

    (tmp_path / "shortcut").symlink_to(outside)

    tools = ToolRegistry(tmp_path)

    with pytest.raises(ToolError):
        tools.execute(
            "files.read",
            {"path": "shortcut"},
        )


def test_blocks_unapproved_commands(tmp_path):
    tools = ToolRegistry(tmp_path)

    with pytest.raises(ToolError):
        tools.execute(
            "shell.run",
            {"command": "python arbitrary.py"},
        )


def test_real_linux_command(tmp_path):
    tools = ToolRegistry(tmp_path)

    result = tools.execute(
        "shell.run", {"command": "pwd"}
    )

    assert result["returncode"] == 0
    assert result["stdout"].strip() == str(tmp_path)


def test_inspector(tmp_path):
    (tmp_path / "project.py").write_text("x = 1")

    report = inspect_workspace(tmp_path)

    assert report["status"] == "completed"
    assert report["files"][0]["name"] == "project.py"
