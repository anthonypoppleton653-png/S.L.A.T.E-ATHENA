# test_slate_control_intelligence.py

import pytest
from slate.slate_control_intelligence import SlateControlIntelligence

@pytest.fixture
def sci():
    return SlateControlIntelligence()

def test_pre_flight(sci):
    state = {"system_state": "Nominal"}
    prompt = sci.PROMPTS["pre-flight"].format(state=state)
    response = sci._ollama_generate(prompt)
    assert response is not None
    assert len(response) > 0

def test_post_action(sci):
    action = "Launch"
    output = "Success"
    prompt = sci.PROMPTS["post-action"].format(action=action, output=output)
    response = sci._ollama_generate(prompt)
    assert response is not None
    assert len(response) > 0

def test_error_recovery(sci):
    action = "Launch"
    error = "Insufficient fuel"
    prompt = sci.PROMPTS["error-recovery"].format(action=action, error=error)
    response = sci._ollama_generate(prompt)
    assert response is not None
    assert len(response) > 0

def test_smart_order(sci):
    controls = ["Launch", "Abort", "Retarget"]
    history = [{"action": "Launch"}, {"action": "Abort"}]
    prompt = sci.PROMPTS["smart-order"].format(controls=controls, history=history)
    response = sci._ollama_generate(prompt)
    assert response is not None
    assert len(response) > 0
    # Strip markdown code fences if present (LLMs often wrap JSON in ```)
    cleaned = response.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]  # Remove first ``` line
    if cleaned.endswith("```"):
        cleaned = cleaned.rsplit("```", 1)[0]
    cleaned = cleaned.strip()
    assert cleaned.startswith("[")
    assert cleaned.endswith("]")