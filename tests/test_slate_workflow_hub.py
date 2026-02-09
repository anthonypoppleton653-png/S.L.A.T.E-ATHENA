# tests/test_slate_workflow_hub.py

import pytest
from slate.slate_workflow_hub import OllamaClient, MODEL_MAP

def test_ollama_client_available():
    client = OllamaClient()
    assert client.available is True
    assert client.models != []

def test_ollama_client_resolve_model():
    client = OllamaClient()
    task_type = "docs"
    model = client.resolve_model(task_type)
    assert model == MODEL_MAP["docs"]

    task_type = "unknown"
    model = client.resolve_model(task_type)
    assert model == MODEL_MAP["fallback"]

def test_ollama_client_warmup():
    client = OllamaClient()
    result = client.warmup("fast")
    assert result is True