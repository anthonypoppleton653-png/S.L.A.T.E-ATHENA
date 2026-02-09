# test_actions_sdk.py

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
        core.get_input("required_input")

def test_set_output(core, monkeypatch):
    # Mock GITHUB_OUTPUT env var to capture output file changes
    output_file = "/tmp/output.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", output_file)

    # Set output value and check file content
    core.set_output("inference_result", "test_result")
    with open(output_file, "r") as f:
        assert f.read().strip() == "inference_result=test_result"

def test_export_variable(core, monkeypatch):
    # Test exporting environment variable
    core.export_variable("NEW_VAR", "new_value")

    # Check if NEW_VAR is set in the environment
    assert monkeypatch.getsetitem("os", "environ")["NEW_VAR"] == "new_value"