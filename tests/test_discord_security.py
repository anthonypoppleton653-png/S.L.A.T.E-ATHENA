#!/usr/bin/env python3
"""
Tests for SLATE Discord Security Gate.

Tests validate that the security boundary between Discord and SLATE
internals properly blocks system info, PII, and abuse attempts.
"""
# Modified: 2026-02-09T18:00:00Z | Author: Claude Opus 4.6 | Change: Create Discord security gate test suite

import sys
from pathlib import Path

import pytest

WORKSPACE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from slate.discord_security import (
    DiscordSecurityGate,
    get_security_gate,
    USER_RATE_LIMIT,
)


@pytest.fixture
def gate():
    """Fresh security gate for each test."""
    return DiscordSecurityGate()


# ── Input Validation ──────────────────────────────────────────────────

class TestInputValidation:
    """Tests for Discord user input sanitization."""

    def test_empty_input_allowed(self, gate):
        r = gate.validate_input("")
        assert r.allowed

    def test_normal_input_passes(self, gate):
        r = gate.validate_input("I love SLATE's GPU scheduling!")
        assert r.allowed
        assert r.filtered_content == "I love SLATE's GPU scheduling!"

    def test_overlength_blocked(self, gate):
        r = gate.validate_input("x" * 501)
        assert not r.allowed
        assert "too long" in r.reason.lower()

    def test_code_blocks_stripped(self, gate):
        r = gate.validate_input("Look at this ```rm -rf /``` code")
        assert r.allowed
        assert "```" not in r.filtered_content
        assert "rm -rf" not in r.filtered_content

    def test_inline_code_stripped(self, gate):
        r = gate.validate_input("Run `eval(malicious)` now")
        assert r.allowed
        assert "`" not in r.filtered_content

    def test_urls_stripped(self, gate):
        r = gate.validate_input("Visit https://evil.com/steal-data")
        assert r.allowed
        assert "https://" not in r.filtered_content

    def test_everyone_mention_stripped(self, gate):
        r = gate.validate_input("Hey @everyone look!")
        assert r.allowed
        assert "@everyone" not in r.filtered_content

    def test_here_mention_stripped(self, gate):
        r = gate.validate_input("@here check this out")
        assert r.allowed
        assert "@here" not in r.filtered_content

    def test_user_mention_stripped(self, gate):
        r = gate.validate_input("Hey <@123456789> check this")
        assert r.allowed
        assert "<@" not in r.filtered_content

    def test_role_mention_stripped(self, gate):
        r = gate.validate_input("Ping <@&987654321> now")
        assert r.allowed
        assert "<@&" not in r.filtered_content

    def test_shell_injection_stripped(self, gate):
        r = gate.validate_input("test ; rm -rf / & echo pwned | cat /etc/passwd")
        assert r.allowed
        assert ";" not in r.filtered_content
        assert "|" not in r.filtered_content
        assert "&" not in r.filtered_content

    def test_completely_sanitized_input_blocked(self, gate):
        r = gate.validate_input("```@everyone```")
        assert not r.allowed
        assert "empty after sanitization" in r.reason.lower()


# ── Output Filtering ──────────────────────────────────────────────────

class TestOutputFiltering:
    """Tests for bot output sanitization — system info must never leak."""

    def test_ip_address_redacted(self, gate):
        r = gate.sanitize_output("Server at 192.168.1.100")
        assert r.allowed
        assert "192.168.1.100" not in r.filtered_content
        assert "[REDACTED]" in r.filtered_content

    def test_public_ip_redacted(self, gate):
        r = gate.sanitize_output("External IP: 203.0.113.42")
        assert "203.0.113.42" not in r.filtered_content

    def test_localhost_redacted(self, gate):
        r = gate.sanitize_output("Bound to 127.0.0.1")
        assert "127.0.0.1" not in r.filtered_content

    def test_port_number_redacted(self, gate):
        r = gate.sanitize_output("Dashboard on :8080")
        assert ":8080" not in r.filtered_content

    def test_windows_path_redacted(self, gate):
        r = gate.sanitize_output("File at E:\\11132025\\slate\\secret.py")
        assert "E:\\" not in r.filtered_content
        assert "11132025" not in r.filtered_content

    def test_unix_path_redacted(self, gate):
        r = gate.sanitize_output("Config at /home/user/.env")
        assert "/home/user" not in r.filtered_content

    def test_slate_token_redacted(self, gate):
        r = gate.sanitize_output("Token: slsvc_abc123def456ghi789jkl")
        assert "slsvc_" not in r.filtered_content

    def test_github_token_redacted(self, gate):
        r = gate.sanitize_output("Auth: ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij")
        assert "ghp_" not in r.filtered_content

    def test_gpu_uuid_redacted(self, gate):
        r = gate.sanitize_output("Device GPU-12345678-abcd-1234-abcd-123456789012")
        assert "GPU-12345678" not in r.filtered_content

    def test_hostname_redacted(self, gate):
        r = gate.sanitize_output("Host: DESKTOP-ABC1234")
        assert "DESKTOP-ABC1234" not in r.filtered_content

    def test_username_path_redacted(self, gate):
        r = gate.sanitize_output("Path: C:\\Users\\Dan\\workspace")
        assert "Dan" not in r.filtered_content

    def test_pid_redacted(self, gate):
        r = gate.sanitize_output("Process PID: 12345 running")
        assert "12345" not in r.filtered_content

    def test_env_var_redacted(self, gate):
        r = gate.sanitize_output("Set $DISCORD_BOT_TOKEN to login")
        assert "$DISCORD_BOT_TOKEN" not in r.filtered_content

    def test_jwt_redacted(self, gate):
        r = gate.sanitize_output("Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0In0.abc123def456")
        assert "eyJ" not in r.filtered_content

    def test_connection_string_redacted(self, gate):
        r = gate.sanitize_output("DB: postgres://user:pass@host:5432/db")
        assert "postgres://" not in r.filtered_content

    def test_aws_key_redacted(self, gate):
        r = gate.sanitize_output("Key: AKIAIOSFODNN7EXAMPLE")
        assert "AKIAIOSFODNN" not in r.filtered_content

    def test_safe_status_passes(self, gate):
        safe = "Dashboard: Online | AI Backend: Active | GPU: 2x Ready"
        r = gate.sanitize_output(safe)
        assert r.allowed
        assert "Online" in r.filtered_content
        assert "Active" in r.filtered_content

    def test_everyone_blocked_in_output(self, gate):
        r = gate.sanitize_output("Alert @everyone: system update")
        assert "@everyone" not in r.filtered_content

    def test_empty_output_allowed(self, gate):
        r = gate.sanitize_output("")
        assert r.allowed

    def test_fully_redacted_output_blocked(self, gate):
        r = gate.sanitize_output("192.168.1.1:8080")
        assert not r.allowed or "[REDACTED]" in r.filtered_content


# ── Rate Limiting ─────────────────────────────────────────────────────

class TestRateLimiting:
    """Tests for per-user and per-channel rate limiting."""

    def test_initial_commands_allowed(self, gate):
        for _ in range(USER_RATE_LIMIT):
            r = gate.check_rate_limit("user1", "channel1")
            assert r.allowed

    def test_exceeding_limit_blocked(self, gate):
        for _ in range(USER_RATE_LIMIT):
            gate.check_rate_limit("user1", "channel1")
        r = gate.check_rate_limit("user1", "channel1")
        assert not r.allowed
        assert "rate limited" in r.reason.lower()

    def test_different_users_independent(self, gate):
        for _ in range(USER_RATE_LIMIT):
            gate.check_rate_limit("user1", "channel1")
        # user1 is rate limited
        r = gate.check_rate_limit("user1", "channel1")
        assert not r.allowed
        # user2 should still be fine
        r = gate.check_rate_limit("user2", "channel1")
        assert r.allowed


# ── Audit Logging ─────────────────────────────────────────────────────

class TestAuditLogging:
    """Tests for interaction audit trail."""

    def test_audit_entry_created(self, gate):
        gate.audit_log("command", "user123", "/slate-status")
        assert len(gate._audit_log) == 1

    def test_user_id_hashed(self, gate):
        gate.audit_log("command", "user123", "/slate-status")
        assert gate._audit_log[0].user_hash != "user123"
        assert len(gate._audit_log[0].user_hash) == 16

    def test_audit_stats(self, gate):
        gate.audit_log("command", "user1", "/status")
        gate.audit_log("blocked", "user2", "/hack", blocked_patterns=["system_info"])
        stats = gate.get_audit_stats()
        assert stats["total_interactions"] == 2
        assert stats["blocked_count"] == 1

    def test_input_truncated(self, gate):
        long_input = "x" * 500
        gate.audit_log("command", "user1", "/feedback", input_text=long_input)
        assert len(gate._audit_log[0].input_text) <= 200


# ── Feedback Validation ───────────────────────────────────────────────

class TestFeedbackValidation:
    """Tests for feedback-specific validation."""

    def test_empty_feedback_rejected(self, gate):
        r = gate.validate_feedback("")
        assert not r.allowed

    def test_short_feedback_rejected(self, gate):
        r = gate.validate_feedback("bad")
        assert not r.allowed
        assert "too short" in r.reason.lower()

    def test_valid_feedback_accepted(self, gate):
        r = gate.validate_feedback("SLATE's tech tree visualization is amazing!")
        assert r.allowed

    def test_feedback_with_urls_sanitized(self, gate):
        r = gate.validate_feedback("Check https://phishing.com for my idea about improvements")
        assert r.allowed
        assert "https://" not in r.filtered_content


# ── Singleton ─────────────────────────────────────────────────────────

class TestSingleton:
    """Test singleton pattern."""

    def test_get_security_gate_returns_instance(self):
        gate = get_security_gate()
        assert isinstance(gate, DiscordSecurityGate)

    def test_singleton_same_instance(self):
        g1 = get_security_gate()
        g2 = get_security_gate()
        assert g1 is g2
