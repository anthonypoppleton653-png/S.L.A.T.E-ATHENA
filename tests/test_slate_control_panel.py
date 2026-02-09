# tests/test_slate_control_panel.py

import pytest
from slate.slate_control_panel import (
    ActionState,
    ControlAction,
    CONTROL_ACTIONS,
)

def test_control_action_init():
    action = ControlAction(
        id="test_id",
        label="Test Label",
        description="Test Description",
        command="echo 'Test Command'"
    )
    assert action.id == "test_id"
    assert action.label == "Test Label"
    assert action.description == "Test Description"
    assert action.command == "echo 'Test Command'"
    assert action.state == ActionState.READY
    assert action.last_result is None
    assert action.last_run is None

def test_control_actions_dict():
    actions = CONTROL_ACTIONS["health"]
    assert len(actions) == 3
    assert actions[0].id == "quick_status"
    assert actions[1].id == "full_diagnostics"
    assert actions[2].id == "runtime_check"

def test_action_state_transitions():
    action = ControlAction(
        id="test_id",
        label="Test Label",
        description="Test Description",
        command="echo 'Test Command'"
    )
    assert action.state == ActionState.READY
    # TODO: Implement state transitions and tests for running, success, error states.