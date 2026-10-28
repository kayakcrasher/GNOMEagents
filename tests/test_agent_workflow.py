from app.agent_workflow import AgentWorkflow


def test_workflow_analyzes_lead():
    state = AgentWorkflow().run(
        "lead:process",
        {"message": "I need a quote ASAP"},
    )

    assert state.status == "awaiting_approval"
    assert state.steps == 1
    assert state.result["analysis"]["intent"] == "quote_request"


def test_high_priority_decision():
    state = AgentWorkflow().run(
        "lead:process",
        {"message": "Need an urgent quote"},
    )

    assert state.result["decision"]["action"] == (
        "prepare_response"
    )
    assert state.result["decision"]["requires_human_review"]


def test_unknown_objective_blocked():
    state = AgentWorkflow().run(
        "system:delete",
        {"message": "Delete everything"},
    )

    assert state.status == "blocked"
    assert state.steps == 0


def test_invalid_message_blocked():
    state = AgentWorkflow().run(
        "lead:process",
        {"message": ""},
    )

    assert state.status == "blocked"


def test_step_limit_blocks_execution():
    state = AgentWorkflow(max_steps=1).run(
        "lead:process",
        {"message": "Need a quote"},
    )

    assert state.steps == 1
    assert state.status == "awaiting_approval"


def test_workflow_records_decision():
    state = AgentWorkflow().run(
        "lead:process",
        {"message": "Hello"},
    )

    assert any(
        event.get("event") == "decision"
        for event in state.trace
    )
