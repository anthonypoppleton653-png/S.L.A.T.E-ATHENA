# Modified: 2026-02-09T22:30:00Z | Author: COPILOT | Change: Add LM Studio provider integration tests
"""Tests for LMStudioProvider integration in unified_ai_backend.py.

Tests cover:
1. Provider class instantiation and configuration
2. Status check (online/offline graceful handling)
3. Model listing and auto-selection
4. Generate via OpenAI-compatible API
5. Native API generate
6. Embedding support
7. Integration with UnifiedAIBackend routing
8. Docker-compose env var presence
"""

import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from io import BytesIO
from http.client import HTTPResponse

# Ensure workspace root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestLMStudioProviderImport(unittest.TestCase):
    """Test that LMStudioProvider can be imported and instantiated."""

    def test_import_provider(self):
        from slate.unified_ai_backend import LMStudioProvider
        provider = LMStudioProvider()
        self.assertEqual(provider.name, "lmstudio")
        self.assertEqual(provider.host, "http://127.0.0.1:1234")

    def test_import_with_custom_host(self):
        from slate.unified_ai_backend import LMStudioProvider
        provider = LMStudioProvider(host="http://192.168.1.100:1234")
        self.assertEqual(provider.host, "http://192.168.1.100:1234")

    def test_provider_in_backend(self):
        from slate.unified_ai_backend import UnifiedAIBackend
        backend = UnifiedAIBackend()
        self.assertIn("lmstudio", backend.providers)
        self.assertEqual(backend.providers["lmstudio"].name, "lmstudio")

    def test_six_providers_registered(self):
        from slate.unified_ai_backend import UnifiedAIBackend
        backend = UnifiedAIBackend()
        self.assertEqual(len(backend.providers), 6)
        expected = {"ollama", "claude_code", "gemini", "copilot", "foundry", "lmstudio"}
        self.assertEqual(set(backend.providers.keys()), expected)


class TestLMStudioConfig(unittest.TestCase):
    """Test LM Studio configuration in TASK_MODELS and TASK_ROUTING."""

    def test_lmstudio_in_task_models(self):
        from slate.unified_ai_backend import TASK_MODELS
        for task_type, models in TASK_MODELS.items():
            self.assertIn("lmstudio", models,
                          f"lmstudio missing from TASK_MODELS['{task_type}']")
            self.assertEqual(models["lmstudio"], "auto",
                             f"lmstudio model should be 'auto' for '{task_type}'")

    def test_lmstudio_in_task_routing(self):
        from slate.unified_ai_backend import TASK_ROUTING
        for task_type, providers in TASK_ROUTING.items():
            self.assertIn("lmstudio", providers,
                          f"lmstudio missing from TASK_ROUTING['{task_type}']")

    def test_lmstudio_host_config(self):
        from slate.unified_ai_backend import LMSTUDIO_HOST
        self.assertTrue(LMSTUDIO_HOST.startswith("http"))
        self.assertIn("1234", LMSTUDIO_HOST)

    def test_model_defaults_include_lmstudio(self):
        from slate.unified_ai_backend import UnifiedAIBackend
        backend = UnifiedAIBackend()
        model = backend.get_model_for_task("code_generation", "lmstudio")
        self.assertEqual(model, "auto")


class TestLMStudioStatusCheck(unittest.TestCase):
    """Test LMStudioProvider.check_status() with mocked HTTP."""

    def _mock_urlopen(self, response_data, status=200):
        """Create a mock for urllib.request.urlopen."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        return mock_response

    @patch("urllib.request.urlopen")
    def test_status_online(self, mock_urlopen):
        mock_urlopen.return_value = self._mock_urlopen({
            "data": [
                {"id": "qwen2.5-coder-7b", "object": "model"},
                {"id": "llama-3.2-3b", "object": "model"},
            ]
        })

        from slate.unified_ai_backend import LMStudioProvider
        provider = LMStudioProvider()
        status = provider.check_status()

        self.assertTrue(status.available)
        self.assertEqual(status.name, "lmstudio")
        self.assertEqual(len(status.models), 2)
        self.assertIn("qwen2.5-coder-7b", status.models)
        self.assertEqual(status.cost, "FREE")
        self.assertGreaterEqual(status.latency_ms, 0)

    @patch("urllib.request.urlopen")
    def test_status_offline(self, mock_urlopen):
        mock_urlopen.side_effect = ConnectionRefusedError("Connection refused")

        from slate.unified_ai_backend import LMStudioProvider
        provider = LMStudioProvider()
        status = provider.check_status()

        self.assertFalse(status.available)
        self.assertEqual(status.name, "lmstudio")
        self.assertIn("Connection refused", status.error)

    @patch("urllib.request.urlopen")
    def test_status_no_models(self, mock_urlopen):
        mock_urlopen.return_value = self._mock_urlopen({"data": []})

        from slate.unified_ai_backend import LMStudioProvider
        provider = LMStudioProvider()
        status = provider.check_status()

        self.assertTrue(status.available)
        self.assertEqual(len(status.models), 0)


class TestLMStudioGenerate(unittest.TestCase):
    """Test LMStudioProvider.generate() with mocked HTTP."""

    def _mock_urlopen(self, response_data):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        return mock_response

    @patch("urllib.request.urlopen")
    def test_generate_success(self, mock_urlopen):
        mock_urlopen.return_value = self._mock_urlopen({
            "choices": [
                {"message": {"role": "assistant", "content": "Hello world!"}}
            ],
            "model": "qwen2.5-coder-7b",
            "usage": {"completion_tokens": 3, "prompt_tokens": 5, "total_tokens": 8},
        })

        from slate.unified_ai_backend import LMStudioProvider
        provider = LMStudioProvider()
        result = provider.generate("Say hello")

        self.assertTrue(result.success)
        self.assertEqual(result.provider, "lmstudio")
        self.assertEqual(result.response, "Hello world!")
        self.assertEqual(result.tokens, 3)
        self.assertEqual(result.model, "qwen2.5-coder-7b")
        self.assertEqual(result.cost, "FREE")

    @patch("urllib.request.urlopen")
    def test_generate_auto_model(self, mock_urlopen):
        """When model='auto', the model field should not be in the request payload."""
        mock_urlopen.return_value = self._mock_urlopen({
            "choices": [{"message": {"content": "response"}}],
            "model": "picked-model",
            "usage": {"completion_tokens": 1},
        })

        from slate.unified_ai_backend import LMStudioProvider
        provider = LMStudioProvider()
        result = provider.generate("test", model="auto")

        self.assertTrue(result.success)
        # Verify the request payload did NOT include "model"
        call_args = mock_urlopen.call_args
        request_obj = call_args[0][0]
        payload = json.loads(request_obj.data.decode("utf-8"))
        self.assertNotIn("model", payload)

    @patch("urllib.request.urlopen")
    def test_generate_specific_model(self, mock_urlopen):
        """When a specific model is given, it should appear in the payload."""
        mock_urlopen.return_value = self._mock_urlopen({
            "choices": [{"message": {"content": "response"}}],
            "model": "llama-3.2-3b",
            "usage": {"completion_tokens": 1},
        })

        from slate.unified_ai_backend import LMStudioProvider
        provider = LMStudioProvider()
        result = provider.generate("test", model="llama-3.2-3b")

        call_args = mock_urlopen.call_args
        request_obj = call_args[0][0]
        payload = json.loads(request_obj.data.decode("utf-8"))
        self.assertEqual(payload["model"], "llama-3.2-3b")

    @patch("urllib.request.urlopen")
    def test_generate_failure(self, mock_urlopen):
        mock_urlopen.side_effect = ConnectionRefusedError("Connection refused")

        from slate.unified_ai_backend import LMStudioProvider
        provider = LMStudioProvider()
        result = provider.generate("test")

        self.assertFalse(result.success)
        self.assertIn("Connection refused", result.error)


class TestLMStudioNativeGenerate(unittest.TestCase):
    """Test LMStudioProvider.generate_native() with mocked HTTP."""

    def _mock_urlopen(self, response_data):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        return mock_response

    @patch("urllib.request.urlopen")
    def test_native_generate_success(self, mock_urlopen):
        mock_urlopen.return_value = self._mock_urlopen({
            "output": [
                {"type": "message", "content": "Native response here"},
            ],
            "stats": {"total_output_tokens": 5},
            "model_instance_id": "qwen2.5-coder-7b",
        })

        from slate.unified_ai_backend import LMStudioProvider
        provider = LMStudioProvider()
        result = provider.generate_native("Explain X")

        self.assertTrue(result.success)
        self.assertEqual(result.response, "Native response here")
        self.assertEqual(result.tokens, 5)

    @patch("urllib.request.urlopen")
    def test_native_generate_multi_block(self, mock_urlopen):
        mock_urlopen.return_value = self._mock_urlopen({
            "output": [
                {"type": "message", "content": "Part 1"},
                {"type": "tool_call", "content": "tool data"},
                {"type": "message", "content": "Part 2"},
            ],
            "stats": {"total_output_tokens": 10},
        })

        from slate.unified_ai_backend import LMStudioProvider
        provider = LMStudioProvider()
        result = provider.generate_native("test")

        self.assertTrue(result.success)
        # Only message blocks should be joined
        self.assertEqual(result.response, "Part 1\nPart 2")


class TestLMStudioEmbed(unittest.TestCase):
    """Test LMStudioProvider.embed() with mocked HTTP."""

    def _mock_urlopen(self, response_data):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        return mock_response

    @patch("urllib.request.urlopen")
    def test_embed_success(self, mock_urlopen):
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_urlopen.return_value = self._mock_urlopen({
            "data": [{"embedding": embedding, "index": 0}],
            "model": "nomic-embed-text",
        })

        from slate.unified_ai_backend import LMStudioProvider
        provider = LMStudioProvider()
        result = provider.embed("test text")

        self.assertEqual(result, embedding)

    @patch("urllib.request.urlopen")
    def test_embed_offline(self, mock_urlopen):
        mock_urlopen.side_effect = ConnectionRefusedError("offline")

        from slate.unified_ai_backend import LMStudioProvider
        provider = LMStudioProvider()
        result = provider.embed("test text")

        self.assertEqual(result, [])


class TestLMStudioNativeStatus(unittest.TestCase):
    """Test LMStudioProvider.get_native_status() with mocked HTTP."""

    def _mock_urlopen(self, response_data):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        return mock_response

    @patch("urllib.request.urlopen")
    def test_native_status_success(self, mock_urlopen):
        native_data = {
            "models": [
                {
                    "id": "qwen2.5-coder-7b",
                    "architecture": "qwen2",
                    "quantization": "Q4_K_M",
                    "context_length": 32768,
                    "state": "loaded",
                }
            ]
        }
        mock_urlopen.return_value = self._mock_urlopen(native_data)

        from slate.unified_ai_backend import LMStudioProvider
        provider = LMStudioProvider()
        result = provider.get_native_status()

        self.assertEqual(result["models"][0]["id"], "qwen2.5-coder-7b")
        self.assertEqual(result["models"][0]["quantization"], "Q4_K_M")

    @patch("urllib.request.urlopen")
    def test_native_status_offline(self, mock_urlopen):
        mock_urlopen.side_effect = ConnectionRefusedError("offline")

        from slate.unified_ai_backend import LMStudioProvider
        provider = LMStudioProvider()
        result = provider.get_native_status()

        self.assertEqual(result, {})


class TestLMStudioRouting(unittest.TestCase):
    """Test that LM Studio is properly integrated into task routing."""

    def test_routing_includes_lmstudio(self):
        from slate.unified_ai_backend import UnifiedAIBackend
        backend = UnifiedAIBackend()
        for task_type in [
            "code_generation", "code_review", "test_generation",
            "bug_fix", "refactoring", "documentation", "analysis",
            "research", "planning", "classification", "prompt_engineering",
            "verification",
        ]:
            route = backend.route_task(task_type)
            self.assertIn("lmstudio", route,
                          f"lmstudio not in route for {task_type}")

    def test_model_for_all_tasks(self):
        from slate.unified_ai_backend import UnifiedAIBackend
        backend = UnifiedAIBackend()
        for task_type in [
            "code_generation", "code_review", "test_generation",
            "bug_fix", "documentation", "classification",
        ]:
            model = backend.get_model_for_task(task_type, "lmstudio")
            self.assertEqual(model, "auto",
                             f"Expected 'auto' for {task_type}, got '{model}'")


class TestDockerComposeConfig(unittest.TestCase):
    """Test that docker-compose.yml includes LMSTUDIO_HOST."""

    def test_lmstudio_host_in_compose(self):
        compose_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "docker-compose.yml"
        )
        with open(compose_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("LMSTUDIO_HOST", content)
        self.assertIn("host.docker.internal:1234", content)


if __name__ == "__main__":
    unittest.main()
