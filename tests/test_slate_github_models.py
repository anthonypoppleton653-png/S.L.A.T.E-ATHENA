#!/usr/bin/env python3
# Modified: 2026-02-09T02:00:00Z | Author: COPILOT | Change: Tests for GitHub Models free-tier integration
"""
Tests for slate/slate_github_models.py

Validates the GitHub Models client, rate limiting, fallback chain,
Semantic Kernel connector, SLATE role mapping, and CLI interface.
All tests are offline (no real API calls) unless explicitly opted in.
"""

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

WORKSPACE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from slate.slate_github_models import (
    ChatResponse,
    GitHubModelsClient,
    GitHubModelsWithFallback,
    GITHUB_MODELS_CATALOG,
    GITHUB_MODELS_ENDPOINT,
    RATE_LIMITS,
    RateTracker,
    SLATE_ROLE_MAP,
    get_github_token,
)


class TestRateTracker(unittest.TestCase):
    """Tests for the free-tier rate limiter."""

    def test_initial_state_allows_calls(self):
        tracker = RateTracker()
        self.assertTrue(tracker.can_call("low"))
        self.assertTrue(tracker.can_call("high"))

    def test_records_calls(self):
        tracker = RateTracker()
        tracker.record_call()
        remaining = tracker.remaining("low")
        self.assertEqual(remaining["rpm_remaining"], 14)
        self.assertEqual(remaining["rpd_remaining"], 149)

    def test_blocks_at_rpm_limit(self):
        tracker = RateTracker()
        for _ in range(15):
            tracker.record_call()
        self.assertFalse(tracker.can_call("low"))

    def test_remaining_calculation(self):
        tracker = RateTracker()
        for _ in range(5):
            tracker.record_call()
        remaining = tracker.remaining("high")
        self.assertEqual(remaining["rpm_remaining"], 10)
        self.assertEqual(remaining["rpd_remaining"], 145)


class TestChatResponse(unittest.TestCase):
    """Tests for the ChatResponse dataclass."""

    def test_ok_with_content(self):
        r = ChatResponse(content="hello", model="gpt-4o")
        self.assertTrue(r.ok)

    def test_not_ok_with_error(self):
        r = ChatResponse(content="", model="gpt-4o", error="rate limit")
        self.assertFalse(r.ok)

    def test_not_ok_with_empty_content(self):
        r = ChatResponse(content="", model="gpt-4o")
        self.assertFalse(r.ok)

    def test_usage_defaults(self):
        r = ChatResponse(content="test", model="m")
        self.assertEqual(r.usage, {})
        self.assertEqual(r.finish_reason, "")
        self.assertAlmostEqual(r.latency_ms, 0.0, places=1)


class TestModelCatalog(unittest.TestCase):
    """Tests for the static model catalog."""

    def test_catalog_not_empty(self):
        self.assertGreater(len(GITHUB_MODELS_CATALOG), 0)

    def test_all_models_have_required_fields(self):
        for name, info in GITHUB_MODELS_CATALOG.items():
            self.assertIn("provider", info, f"{name} missing provider")
            self.assertIn("tier", info, f"{name} missing tier")
            self.assertIn("best_for", info, f"{name} missing best_for")
            self.assertIn(info["tier"], ("low", "high"), f"{name} invalid tier")

    def test_gpt4o_mini_in_catalog(self):
        self.assertIn("gpt-4o-mini", GITHUB_MODELS_CATALOG)

    def test_gpt4o_in_catalog(self):
        self.assertIn("gpt-4o", GITHUB_MODELS_CATALOG)

    def test_endpoint_is_github_models(self):
        self.assertEqual(GITHUB_MODELS_ENDPOINT, "https://models.inference.ai.azure.com")


class TestSlateRoleMap(unittest.TestCase):
    """Tests for SLATE role → model mapping."""

    def test_all_standard_roles_mapped(self):
        expected_roles = ["code", "fast", "planner", "analysis", "reasoning", "summary", "general"]
        for role in expected_roles:
            self.assertIn(role, SLATE_ROLE_MAP, f"Role '{role}' not mapped")

    def test_mapped_models_exist_in_catalog(self):
        for role, model in SLATE_ROLE_MAP.items():
            self.assertIn(
                model, GITHUB_MODELS_CATALOG,
                f"Role '{role}' maps to '{model}' which is not in catalog"
            )


class TestGitHubModelsClient(unittest.TestCase):
    """Tests for the main client class."""

    def test_init_with_token(self):
        client = GitHubModelsClient(token="test_token_123")
        self.assertTrue(client.authenticated)
        self.assertEqual(client.token, "test_token_123")

    def test_init_without_token(self):
        with patch("slate.slate_github_models.get_github_token", return_value=""):
            client = GitHubModelsClient(token="")
            # token is empty string, authenticated should be False
            self.assertFalse(client.authenticated)

    def test_default_model(self):
        client = GitHubModelsClient(token="t")
        self.assertEqual(client.default_model, "gpt-4o-mini")

    def test_resolve_model_by_role(self):
        client = GitHubModelsClient(token="t")
        self.assertEqual(client.resolve_model("code"), "gpt-4o")
        self.assertEqual(client.resolve_model("fast"), "gpt-4o-mini")

    def test_resolve_model_unknown_role(self):
        client = GitHubModelsClient(token="t")
        self.assertEqual(client.resolve_model("unknown_role"), "gpt-4o-mini")

    def test_get_model_tier(self):
        client = GitHubModelsClient(token="t")
        self.assertEqual(client.get_model_tier("gpt-4o"), "low")
        self.assertEqual(client.get_model_tier("gpt-4o-mini"), "high")

    def test_list_available_models(self):
        client = GitHubModelsClient(token="t")
        models = client.list_available_models()
        self.assertGreater(len(models), 0)
        for m in models:
            self.assertIn("name", m)
            self.assertIn("provider", m)

    def test_status_format(self):
        client = GitHubModelsClient(token="t")
        status = client.status()
        self.assertIn("authenticated", status)
        self.assertIn("endpoint", status)
        self.assertIn("catalog_size", status)
        self.assertIn("rate_limits", status)
        self.assertTrue(status["authenticated"])

    def test_chat_rate_limited(self):
        """Verify rate limiter blocks when exhausted."""
        client = GitHubModelsClient(token="t")
        # Exhaust rate limit
        for _ in range(15):
            client._rate_tracker.record_call()
        response = client.chat("test prompt")
        self.assertFalse(response.ok)
        self.assertIn("Rate limit exceeded", response.error)

    @patch("slate.slate_github_models.GitHubModelsClient.get_sync_client")
    def test_chat_success(self, mock_get_client):
        """Mock a successful chat completion."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello from GPT!"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        client = GitHubModelsClient(token="test_token")
        response = client.chat("Hello", model="gpt-4o-mini")

        self.assertTrue(response.ok)
        self.assertEqual(response.content, "Hello from GPT!")
        self.assertEqual(response.model, "gpt-4o-mini")
        self.assertEqual(response.usage["total_tokens"], 15)

    @patch("slate.slate_github_models.GitHubModelsClient.get_sync_client")
    def test_chat_auth_error(self, mock_get_client):
        """Verify auth error handling."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("401 Unauthorized")
        mock_get_client.return_value = mock_client

        client = GitHubModelsClient(token="bad_token")
        response = client.chat("Hello")

        self.assertFalse(response.ok)
        self.assertIn("Authentication failed", response.error)


class TestGitHubModelsWithFallback(unittest.TestCase):
    """Tests for the fallback chain (GitHub Models → Ollama)."""

    def test_ollama_fallback_map_has_all_roles(self):
        fb = GitHubModelsWithFallback.__dict__
        fallback_map = GitHubModelsWithFallback.OLLAMA_FALLBACK_MAP
        for role in SLATE_ROLE_MAP:
            self.assertIn(role, fallback_map, f"Role '{role}' missing from Ollama fallback map")

    @patch("slate.slate_github_models.get_github_token", return_value="")
    @patch("subprocess.run")
    def test_fallback_to_ollama(self, mock_run, mock_token):
        """When no GitHub token, should fall back to Ollama."""
        # Mock Ollama list (available)
        mock_list_result = MagicMock()
        mock_list_result.returncode = 0
        mock_list_result.stdout = "NAME\nslate-fast:latest"

        # Mock Ollama run (response)
        mock_run_result = MagicMock()
        mock_run_result.returncode = 0
        mock_run_result.stdout = "Ollama fallback response"

        mock_run.side_effect = [mock_list_result, mock_run_result]

        fb = GitHubModelsWithFallback()
        response = fb.chat("test prompt", role="fast")

        self.assertTrue(response.ok)
        self.assertIn("ollama/", response.model)

    @patch("slate.slate_github_models.get_github_token", return_value="")
    @patch("subprocess.run")
    def test_both_unavailable(self, mock_run, mock_token):
        """When both GitHub Models and Ollama unavailable."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        fb = GitHubModelsWithFallback()
        response = fb.chat("test prompt")

        self.assertFalse(response.ok)
        self.assertIn("unavailable", response.error)


class TestRateLimits(unittest.TestCase):
    """Tests for rate limit configuration."""

    def test_rate_limits_defined(self):
        self.assertIn("low", RATE_LIMITS)
        self.assertIn("high", RATE_LIMITS)

    def test_low_tier_limits(self):
        low = RATE_LIMITS["low"]
        self.assertEqual(low["rpm"], 15)
        self.assertEqual(low["rpd"], 150)

    def test_high_tier_limits(self):
        high = RATE_LIMITS["high"]
        self.assertEqual(high["rpm"], 15)
        self.assertEqual(high["rpd"], 150)


class TestSKConnector(unittest.TestCase):
    """Tests for the Semantic Kernel connector factory."""

    @patch("slate.slate_github_models.get_github_token", return_value="test_token")
    def test_creates_sk_service(self, mock_token):
        """Verify SK service creation succeeds with token."""
        from slate.slate_github_models import create_github_models_sk_service
        service = create_github_models_sk_service(role="code", token="test_token")
        # Service should be an OpenAIChatCompletion instance
        self.assertIsNotNone(service)
        self.assertEqual(service.service_id, "github_models_code")

    @patch("slate.slate_github_models.get_github_token", return_value="")
    def test_sk_service_fails_without_token(self, mock_token):
        """Verify SK service creation fails gracefully without token."""
        from slate.slate_github_models import create_github_models_sk_service
        with self.assertRaises(RuntimeError):
            create_github_models_sk_service(role="code")


if __name__ == "__main__":
    unittest.main()
