# tests/test_slate_live_update.py

import pytest
from slate.slate_live_update import LiveUpdateManager, DeploymentComponent

@pytest.fixture
def manager():
    return LiveUpdateManager()

def test_load_state(manager):
    state = manager.load_state()
    assert isinstance(state, dict)
    assert "last_update" in state
    assert "last_version" in state
    assert "rollback_version" in state
    assert "rollback_sha" in state
    assert "components" in state
    assert "update_history" in state
    assert "in_progress" in state

def test_save_state(manager):
    state = {"test_key": "test_value"}
    manager.save_state(state)
    saved_state = manager.load_state()
    assert saved_state == {"test_key": "test_value", **manager.load_state()}

def test_take_snapshot(manager):
    snapshot = manager.take_snapshot()
    assert isinstance(snapshot, dict)
    assert "timestamp" in snapshot