import subprocess

import pytest

from app.tools.devops import DevOpsTools
from app.tools.registry import ToolError


def git(repo, *args):
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )


def test_git_status(tmp_path):
    git(tmp_path, "init")

    (tmp_path / "hello.py").write_text(
        "VALUE = 1\n"
    )

    tools = DevOpsTools(tmp_path)
    result = tools.git_status()

    assert result["passed"]
    assert "hello.py" in result["stdout"]


def test_git_diff(tmp_path):
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test")

    target = tmp_path / "hello.py"
    target.write_text("VALUE = 1\n")

    git(tmp_path, "add", "hello.py")
    git(tmp_path, "commit", "-m", "Initial")

    target.write_text("VALUE = 2\n")

    result = DevOpsTools(tmp_path).git_diff()

    assert result["passed"]
    assert "+VALUE = 2" in result["stdout"]


def test_pytest_runner(tmp_path):
    (tmp_path / "test_math.py").write_text(
        "def test_add():\n"
        "    assert 2 + 2 == 4\n"
    )

    result = DevOpsTools(tmp_path).run_tests()

    assert result["passed"]
    assert "1 passed" in result["stdout"]


def test_pytest_failure_report(tmp_path):
    (tmp_path / "test_math.py").write_text(
        "def test_add():\n"
        "    assert 2 + 2 == 5\n"
    )

    result = DevOpsTools(tmp_path).run_tests()

    assert not result["passed"]
    assert "1 failed" in result["stdout"]


def test_non_git_workspace_denied(tmp_path):
    with pytest.raises(ToolError):
        DevOpsTools(tmp_path).git_status()
