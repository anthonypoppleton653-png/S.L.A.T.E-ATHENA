# tests/test_interactive_api.py

import pytest
from fastapi.testclient import TestClient
from slate.interactive_api import app, learning_router, dev_cycle_router, feedback_router

# Initialize test client for the FastAPI application
client = TestClient(app)

def test_list_learning_paths():
    # Test listing all available learning paths
    response = client.get("/api/interactive/paths")
    assert response.status_code == 200
    data = response.json()
    assert "learning_paths" in data

def test_start_session_valid_request():
    # Test starting a session with valid request body
    request_body = {"path_id": "valid_path_id"}
    response = client.post("/api/interactive/sessions/start", json=request_body)
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data

def test_start_session_invalid_request():
    # Test starting a session with invalid request body
    request_body = {"invalid_key": "invalid_value"}
    response = client.post("/api/interactive/sessions/start", json=request_body)
    assert response.status_code == 422  # Unprocessable Entity

def test_complete_step_valid_request():
    # Test completing a step with valid request body
    request_body = {"step_id": "valid_step_id", "result": {}}
    response = client.post("/api/interactive/sessions/steps/complete", json=request_body)
    assert response.status_code == 200
    data = response.json()
    assert "completed" in data

def test_complete_step_invalid_request():
    # Test completing a step with invalid request body
    request_body = {"invalid_key": "invalid_value"}
    response = client.post("/api/interactive/sessions/steps/complete", json=request_body)
    assert response.status_code == 422  # Unprocessable Entity

def test_dev_cycle_transition_valid_request():
    # Test transitioning between dev cycle stages with valid request body
    request_body = {"to_stage": "PLAN"}
    response = client.post("/api/interactive/devcycle/stages/transition", json=request_body)
    assert response.status_code == 200
    data = response.json()
    assert "stage" in data

def test_dev_cycle_transition_invalid_request():
    # Test transitioning between dev cycle stages with invalid request body
    request_body = {"invalid_key": "invalid_value"}
    response = client.post("/api/interactive/devcycle/stages/transition", json=request_body)
    assert response.status_code == 422  # Unprocessable Entity

def test_feedback_tool_event_valid_request():
    # Test sending tool event with valid request body
    request_body = {
        "tool_name": "valid_tool_name",
        "tool_input": {},
        "success": True,
        "duration_ms": 0
    }
    response = client.post("/api/interactive/feedback/toolevent", json=request_body)
    assert response.status_code == 200
    data = response.json()
    assert "event_id" in data

def test_feedback_tool_event_invalid_request():
    # Test sending tool event with invalid request body
    request_body = {"invalid_key": "invalid_value"}
    response = client.post("/api/interactive/feedback/toolevent", json=request_body)
    assert response.status_code == 422  # Unprocessable Entity