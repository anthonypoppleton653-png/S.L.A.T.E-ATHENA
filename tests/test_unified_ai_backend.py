# tests/test_unified_ai_backend.py
# Modified: 2026-02-09T22:45:00Z | Author: COPILOT | Change: Add LMStudioProvider to import and existence tests (6 providers)

import pytest
from unittest.mock import patch, MagicMock


def test_module_importable():
    """Verify unified_ai_backend module imports correctly."""
    from slate.unified_ai_backend import (
        UnifiedAIBackend,
        OllamaProvider,
        ClaudeCodeProvider,
        GeminiCliProvider,
        CopilotCliProvider,
        FoundryProvider,
        LMStudioProvider,
        InferenceResult,
        ProviderStatus,
    )
    assert UnifiedAIBackend is not None
    assert OllamaProvider is not None
    assert LMStudioProvider is not None


def test_provider_classes_exist():
    """Verify all 6 provider classes exist."""
    from slate.unified_ai_backend import (
        OllamaProvider,
        ClaudeCodeProvider,
        GeminiCliProvider,
        CopilotCliProvider,
        FoundryProvider,
        LMStudioProvider,
    )
    # All should be classes
    assert callable(OllamaProvider)
    assert callable(ClaudeCodeProvider)
    assert callable(GeminiCliProvider)
    assert callable(CopilotCliProvider)
    assert callable(FoundryProvider)
    assert callable(LMStudioProvider)


def test_inference_result_dataclass():
    """Verify InferenceResult is usable."""
    from slate.unified_ai_backend import InferenceResult
    result = InferenceResult(success=True, provider="ollama", model="test",
                             response="hello", tokens=10, duration_ms=0.5)
    assert result.response == "hello"
    assert result.success is True
    assert result.cost == "FREE"


def test_provider_status_dataclass():
    """Verify ProviderStatus is usable."""
    from slate.unified_ai_backend import ProviderStatus
    status = ProviderStatus(name="ollama", available=True, endpoint="localhost:11434", models=["test"])
    assert status.name == "ollama"
    assert status.available is True
    assert status.cost == "FREE"


def test_unified_backend_instantiation():
    """Verify UnifiedAIBackend can be created."""
    from slate.unified_ai_backend import UnifiedAIBackend
    try:
        backend = UnifiedAIBackend()
        assert backend is not None
    except Exception as e:
        # May fail if Ollama not running — that's OK for unit test
        pytest.skip(f"Backend init requires live services: {e}")