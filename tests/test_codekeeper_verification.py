from app.tools.codekeeper import Codekeeper


def make_project(tmp_path, expected):
    (tmp_path / "calculator.py").write_text(
        "def add(a, b):\n"
        "    return a - b\n"
    )

    (tmp_path / "test_calculator.py").write_text(
        "from calculator import add\n"
        "def test_add():\n"
        f"    assert add(2, 3) == {expected}\n"
    )


def test_verified_patch_completes(tmp_path):
    make_project(tmp_path, expected=5)

    agent = Codekeeper(
        tmp_path,
        tmp_path / "journal.db",
    )

    prepared = agent.prepare(
        "Fix calculator",
        "calculator.py",
        "def add(a, b):\n"
        "    return a + b\n",
    )

    result = agent.approve(
        prepared["task_id"],
        prepared["proposal"]["id"],
    )

    assert result["status"] == "completed"
    assert result["tests"]["passed"]

    history = agent.journal.history(
        prepared["task_id"]
    )

    assert any(
        event["kind"] == "verification.tests"
        for event in history
    )


def test_broken_patch_fails_verification(tmp_path):
    make_project(tmp_path, expected=5)

    agent = Codekeeper(
        tmp_path,
        tmp_path / "journal.db",
    )

    prepared = agent.prepare(
        "Attempt calculator repair",
        "calculator.py",
        "def add(a, b):\n"
        "    return a * b\n",
    )

    result = agent.approve(
        prepared["task_id"],
        prepared["proposal"]["id"],
    )

    assert result["status"] == "failed"
    assert not result["tests"]["passed"]

    task = agent.journal.get_task(
        prepared["task_id"]
    )

    assert task["status"] == "failed"
