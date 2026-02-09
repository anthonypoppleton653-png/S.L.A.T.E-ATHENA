# test_actions_sdk.py

import os
import pytest
from slate.actions_sdk import ActionsCore

@pytest.fixture
def core():
    return ActionsCore()

def test_get_input(core):
    # Test getting input with default value
    assert core.get_input("model_name", default="default_model") == "default_model"

    # Test getting required input without value raises ValueError
    with pytest.raises(ValueError):
        core.get_input("required_input", required=True)

def test_set_output(monkeypatch, tmp_path):
    # _in_actions is set at construction time, so set env BEFORE creating core
    output_file = str(tmp_path / "output.txt")
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_OUTPUT", output_file)
    core = ActionsCore()

    # Set output value and check file content
    core.set_output("inference_result", "test_result")
    with open(output_file, "r") as f:
        assert f.read().strip() == "inference_result=test_result"

def test_export_variable(core, monkeypatch):
    # Test exporting environment variable
    core.export_variable("NEW_VAR", "new_value")

    # Check if NEW_VAR is set in the environment
    assert os.environ.get("NEW_VAR") == "new_value"