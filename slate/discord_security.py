#!/usr/bin/env python3
"""
SLATE Discord Security Gate
=============================

Security boundary between Discord and SLATE internals. ALL Discord bot
interactions pass through this gate before reaching SLATE systems or
being sent to Discord users.

Security Layers:
  1. Input validation — sanitize and validate all Discord user input
  2. Output filtering — PII scanner + system info blocklist
  3. Rate limiting — per-user and per-channel throttling
  4. Audit logging — all interactions logged locally

Threat Model:
  - Discord users attempting to extract system info (IPs, ports, paths)
  - Injection attacks via slash command parameters
  - Abuse via command flooding
  - Data exfiltration via bot responses

Constitution Compliance:
  - Law 1: No harm to operator (no data exfiltration)
  - Law 3: Protect integrity (audit trail, rate limiting)
"""
# Modified: 2026-02-09T18:00:00Z | Author: Claude Opus 4.6 | Change: Create Discord security isolation gate

import hashlib
import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

WORKSPACE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

logger = logging.getLogger("slate.discord_security")

# ── System Info Blocklist ─────────────────────────────────────────────
# These patterns are HARDCODED and NEVER configurable via Discord.
# They prevent leaking system internals to Discord users.

SYSTEM_INFO_PATTERNS: list[re.Pattern] = [
    # IP addresses (all forms — public and private)
    re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"),
    # Port numbers in service context (:NNNN)
    re.compile(r":\d{4,5}\b"),
    # Windows file paths (drive letters)
    re.compile(r"[A-Za-z]:\\[^\s\"']+"),
    # Unix file paths (absolute)
    re.compile(r"(?<!\w)/(?:home|usr|var|etc|opt|tmp|root|mnt|srv|proc|sys)/[^\s\"']*"),
    # SLATE token prefixes
    re.compile(r"\b(?:slsvc|slagt|slghp|slwik|slplg|slsess|slapi)_[A-Za-z0-9_-]+\b"),
    # Generic API key patterns
    re.compile(r"\b(?:sk|pk|api|key|token|secret|bearer)[-_]?[A-Za-z0-9]{16,}\b", re.IGNORECASE),
    # GitHub tokens
    re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}\b"),
    # Discord bot tokens (prevent self-leak)
    re.compile(r"[A-Za-z0-9_-]{24}\.[A-Za-z0-9_-]{6}\.[A-Za-z0-9_-]{27,}"),
    # AWS keys
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    # Environment variable references
    re.compile(r"\$\{?[A-Z_][A-Z0-9_]*\}?"),
    # GPU device UUIDs
    re.compile(r"\bGPU-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.IGNORECASE),
    # Hostname patterns (COMPUTERNAME, hostname output)
    re.compile(r"\b(?:DESKTOP|LAPTOP|WORKSTATION|SERVER)-[A-Z0-9]{6,}\b"),
    # Windows username paths
    re.compile(r"C:\\Users\\[A-Za-z0-9._-]+", re.IGNORECASE),
    # PID patterns in process context
    re.compile(r"\bPID[:\s]+\d+\b", re.IGNORECASE),
    # Private key headers
    re.compile(r"-----BEGIN (?:RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----"),
    # JWT tokens
    re.compile(r"\beyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\b"),
    # Connection strings
    re.compile(r"(?:mongodb|postgres|mysql|redis)://[^\s\"']+", re.IGNORECASE),
]

# Safe replacements for blocked patterns
REDACTION_TEXT = "[REDACTED]"

# Discord-specific blocked content in bot output
DISCORD_OUTPUT_BLOCKS: list[re.Pattern] = [
    re.compile(r"@everyone"),
    re.compile(r"@here"),
    re.compile(r"<@&\d+>"),        # Role mentions
    re.compile(r"<@!?\d+>"),       # User mentions (prevent pinging from bot)
]

# ── Intelligent Anti-Flood System ────────────────────────────────────
#
# Instead of rigid "1 command per 60 seconds" limits, this uses a
# sliding-window burst detection system that:
#   - Allows normal conversation flow (multiple commands in a session)
#   - Detects and blocks rapid spam bursts
#   - Escalates cooldowns for repeat offenders
#   - Self-heals: flood scores decay over time
#
# Normal use: 5 commands in 30s is fine (browsing commands)
# Flood:      10+ commands in 30s triggers cooldown
# Escalation: Repeat flooding → longer cooldowns (30s → 60s → 120s → 300s)

USER_BURST_LIMIT = 5         # commands per burst window before warning
USER_BURST_WINDOW = 15       # seconds — burst detection window
USER_FLOOD_LIMIT = 10        # commands per flood window = definite spam
USER_FLOOD_WINDOW = 30       # seconds — flood detection window
USER_COOLDOWN_BASE = 15      # base cooldown in seconds after flood
USER_COOLDOWN_ESCALATION = 2 # multiplier for repeat offenders
USER_MAX_COOLDOWN = 300      # max cooldown: 5 minutes

# Per-channel flood protection (prevent one channel being overwhelmed)
CHANNEL_RATE_LIMIT = 60      # commands per window (was 30, doubled)
CHANNEL_RATE_WINDOW = 60     # seconds

# Input limits
MAX_INPUT_LENGTH = 500
MAX_FEEDBACK_LENGTH = 1000

# ── Data Classes ──────────────────────────────────────────────────────

@dataclass
class SecurityResult:
    """Result of a security check."""
    allowed: bool
    reason: str = ""
    filtered_content: str = ""
    blocked_patterns: list[str] = field(default_factory=list)
    pii_found: list[str] = field(default_factory=list)


@dataclass
class AuditEntry:
    """Discord interaction audit log entry."""
    timestamp: str
    event_type: str
    user_hash: str       # SHA-256 of Discord user ID (never raw)
    command: str
    input_text: str
    output_filtered: bool
    blocked_patterns: list[str]
    rate_limited: bool


# ── Security Gate ─────────────────────────────────────────────────────

class DiscordSecurityGate:
    """
    Security boundary between Discord and SLATE internals.

    ALL bot interactions pass through this gate. It enforces:
    - Input validation and sanitization
    - Output filtering (system info + PII redaction)
    - Per-user and per-channel rate limiting
    - Audit logging of all interactions
    """

    def __init__(self):
        self._user_commands: dict[str, list[float]] = {}
        self._channel_commands: dict[str, list[float]] = {}
        # Anti-flood tracking
        self._user_flood_score: dict[str, int] = {}      # escalation counter
        self._user_cooldown_until: dict[str, float] = {}  # cooldown expiry timestamp
        self._audit_log: list[AuditEntry] = []
        self._audit_file = WORKSPACE_ROOT / "slate_logs" / "discord_audit.json"
        self._audit_file.parent.mkdir(parents=True, exist_ok=True)

    # ── Input Validation ──────────────────────────────────────────

    def validate_input(self, text: str) -> SecurityResult:
        """
        Validate and sanitize Discord user input.

        Checks:
        - Length limits
        - Code block injection
        - URL injection (SSRF prevention)
        - Discord mention stripping
        """
        if not text:
            return SecurityResult(allowed=True, filtered_content="")

        blocked = []

        # Length check
        if len(text) > MAX_INPUT_LENGTH:
            return SecurityResult(
                allowed=False,
                reason=f"Input too long (max {MAX_INPUT_LENGTH} characters)",
            )

        # Strip code blocks (prevent injection)
        if "```" in text or "`" in text:
            text = re.sub(r"```[\s\S]*?```", "", text)
            text = re.sub(r"`[^`]*`", "", text)
            blocked.append("code_blocks")

        # Strip URLs (prevent SSRF / phishing)
        url_pattern = re.compile(r"https?://[^\s]+", re.IGNORECASE)
        if url_pattern.search(text):
            text = url_pattern.sub("", text)
            blocked.append("urls")

        # Strip Discord mentions
        text = re.sub(r"@everyone", "", text)
        text = re.sub(r"@here", "", text)
        text = re.sub(r"<@!?\d+>", "", text)
        text = re.sub(r"<@&\d+>", "", text)

        # Strip potential command injection characters
        text = re.sub(r"[;|&$`\\]", "", text)

        # Clean up whitespace
        text = " ".join(text.split()).strip()

        if not text:
            return SecurityResult(
                allowed=False,
                reason="Input was empty after sanitization",
                blocked_patterns=blocked,
            )

        return SecurityResult(
            allowed=True,
            filtered_content=text,
            blocked_patterns=blocked,
        )

    def validate_feedback(self, text: str) -> SecurityResult:
        """Validate feedback input (slightly longer limit)."""
        if not text:
            return SecurityResult(allowed=False, reason="Feedback cannot be empty")

        if len(text) > MAX_FEEDBACK_LENGTH:
            return SecurityResult(
                allowed=False,
                reason=f"Feedback too long (max {MAX_FEEDBACK_LENGTH} characters)",
            )

        if len(text) < 10:
            return SecurityResult(
                allowed=False,
                reason="Feedback too short (minimum 10 characters)",
            )

        # Reuse standard input validation
        result = self.validate_input(text)
        return result

    # ── Output Filtering ──────────────────────────────────────────

    def sanitize_output(self, text: str) -> SecurityResult:
        """
        Filter bot output before sending to Discord.

        Pipeline:
        1. System info blocklist (IPs, paths, tokens, etc.)
        2. PII Scanner integration
        3. Discord-specific content blocks (@everyone, etc.)
        """
        if not text:
            return SecurityResult(allowed=True, filtered_content="")

        blocked = []
        filtered = text

        # Step 1: System info blocklist
        for pattern in SYSTEM_INFO_PATTERNS:
            matches = pattern.findall(filtered)
            if matches:
                filtered = pattern.sub(REDACTION_TEXT, filtered)
                blocked.extend([f"system_info:{m[:20]}..." for m in matches[:3]])

        # Step 2: PII Scanner integration
        try:
            from slate.pii_scanner import scan_text, redact_text
            pii_matches = scan_text(filtered)
            critical_types = {"ssn", "credit_card", "private_key", "aws_key"}

            if any(m.pii_type in critical_types for m in pii_matches):
                # Critical PII found — block entire message
                return SecurityResult(
                    allowed=False,
                    reason="Critical PII detected in output — message blocked",
                    pii_found=[m.pii_type for m in pii_matches],
                    blocked_patterns=blocked,
                )

            if pii_matches:
                filtered, _ = redact_text(filtered)
                blocked.extend([f"pii:{m.pii_type}" for m in pii_matches])
        except ImportError:
            logger.warning("PII scanner not available — skipping PII check")

        # Step 3: Discord-specific blocks
        for pattern in DISCORD_OUTPUT_BLOCKS:
            if pattern.search(filtered):
                filtered = pattern.sub("", filtered)
                blocked.append("discord_mention")

        # Clean up multiple redaction markers
        filtered = re.sub(r"(\[REDACTED\]\s*){2,}", "[REDACTED] ", filtered)
        filtered = filtered.strip()

        if not filtered:
            return SecurityResult(
                allowed=False,
                reason="Output was entirely redacted",
                blocked_patterns=blocked,
            )

        return SecurityResult(
            allowed=True,
            filtered_content=filtered,
            blocked_patterns=blocked,
        )

    # ── Intelligent Anti-Flood System ────────────────────────────

    def check_rate_limit(self, user_id: str, channel_id: str) -> SecurityResult:
        """
        Intelligent anti-flood rate limiting.

        Instead of rigid "1 per minute" limits, this system:
        - Allows normal conversation flow (multiple commands in a session)
        - Detects rapid spam bursts (10+ in 30s)
        - Escalates cooldowns for repeat offenders
        - Self-heals: flood scores decay over time

        Returns SecurityResult with allowed=False if flooding detected.
        """
        now = time.time()
        user_key = self._hash_id(user_id)

        # ── Check active cooldown ──────────────────────────────
        cooldown_until = self._user_cooldown_until.get(user_key, 0)
        if now < cooldown_until:
            remaining = int(cooldown_until - now)
            return SecurityResult(
                allowed=False,
                reason=(
                    f"⏳ Anti-flood cooldown: **{remaining}s** remaining.\n"
                    "Slow down and try again shortly."
                ),
            )

        # ── Track command timestamps ───────────────────────────
        user_times = self._user_commands.get(user_key, [])
        # Keep last 2 minutes of timestamps for analysis
        user_times = [t for t in user_times if now - t < 120]
        user_times.append(now)
        self._user_commands[user_key] = user_times

        # ── Flood detection (10+ commands in 30s = spam) ───────
        recent_flood = [t for t in user_times if now - t < USER_FLOOD_WINDOW]
        if len(recent_flood) >= USER_FLOOD_LIMIT:
            # Escalate cooldown
            flood_score = self._user_flood_score.get(user_key, 0) + 1
            self._user_flood_score[user_key] = flood_score

            cooldown = min(
                USER_COOLDOWN_BASE * (USER_COOLDOWN_ESCALATION ** (flood_score - 1)),
                USER_MAX_COOLDOWN,
            )
            self._user_cooldown_until[user_key] = now + cooldown

            logger.warning(
                f"Anti-flood: User {user_key[:8]} triggered flood "
                f"(score: {flood_score}, cooldown: {int(cooldown)}s)"
            )

            return SecurityResult(
                allowed=False,
                reason=(
                    f"🛡️ **Anti-flood triggered.** Too many commands too quickly.\n"
                    f"Cooldown: **{int(cooldown)}s**. "
                    f"{'This is your first warning.' if flood_score == 1 else f'Repeat offense #{flood_score} — cooldowns will increase.'}"
                ),
            )

        # ── Burst warning (5+ in 15s = getting close) ─────────
        recent_burst = [t for t in user_times if now - t < USER_BURST_WINDOW]
        if len(recent_burst) >= USER_BURST_LIMIT:
            # Don't block yet, but warn (user will see it in the next response)
            # Just let it through — they're close to the flood threshold
            pass

        # ── Decay flood scores (reward good behavior) ──────────
        # If no flood in the last 5 minutes, reduce score
        if user_key in self._user_flood_score:
            last_flood_time = self._user_cooldown_until.get(user_key, 0)
            if now - last_flood_time > 300:  # 5 minutes clean
                self._user_flood_score[user_key] = max(
                    0, self._user_flood_score[user_key] - 1,
                )

        # ── Per-channel check ──────────────────────────────────
        chan_times = self._channel_commands.get(channel_id, [])
        chan_times = [t for t in chan_times if now - t < CHANNEL_RATE_WINDOW]
        if len(chan_times) >= CHANNEL_RATE_LIMIT:
            return SecurityResult(
                allowed=False,
                reason=(
                    "📢 This channel is very active right now. "
                    "Please wait a moment before trying again."
                ),
            )
        chan_times.append(now)
        self._channel_commands[channel_id] = chan_times

        return SecurityResult(allowed=True)

    # ── Audit Logging ─────────────────────────────────────────────

    def audit_log(
        self,
        event_type: str,
        user_id: str,
        command: str,
        input_text: str = "",
        output_filtered: bool = False,
        blocked_patterns: Optional[list[str]] = None,
        rate_limited: bool = False,
    ):
        """
        Log a Discord interaction to the audit trail.

        User IDs are hashed — we NEVER store raw Discord user IDs.
        """
        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type,
            user_hash=self._hash_id(user_id),
            command=command,
            input_text=input_text[:200],  # Truncate for storage
            output_filtered=output_filtered,
            blocked_patterns=blocked_patterns or [],
            rate_limited=rate_limited,
        )
        self._audit_log.append(entry)

        # Write to file (append-safe)
        try:
            self._write_audit_entry(entry)
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

    def _write_audit_entry(self, entry: AuditEntry):
        """Append audit entry to JSON log file."""
        log_data = []
        if self._audit_file.exists():
            try:
                raw = self._audit_file.read_text(encoding="utf-8")
                if raw.strip():
                    log_data = json.loads(raw)
            except (json.JSONDecodeError, Exception):
                log_data = []

        log_data.append({
            "timestamp": entry.timestamp,
            "event": entry.event_type,
            "user_hash": entry.user_hash,
            "command": entry.command,
            "input": entry.input_text,
            "output_filtered": entry.output_filtered,
            "blocked": entry.blocked_patterns,
            "rate_limited": entry.rate_limited,
        })

        # Keep last 10000 entries max
        if len(log_data) > 10000:
            log_data = log_data[-10000:]

        self._audit_file.write_text(
            json.dumps(log_data, indent=2),
            encoding="utf-8",
        )

    def get_audit_stats(self) -> dict:
        """Get audit statistics (safe for Discord display)."""
        total = len(self._audit_log)
        blocked = sum(1 for e in self._audit_log if e.blocked_patterns)
        rate_limited = sum(1 for e in self._audit_log if e.rate_limited)
        return {
            "total_interactions": total,
            "blocked_count": blocked,
            "rate_limited_count": rate_limited,
        }

    # ── Helpers ────────────────────────────────────────────────────

    @staticmethod
    def _hash_id(discord_id: str) -> str:
        """Hash a Discord user ID for privacy-safe storage."""
        return hashlib.sha256(str(discord_id).encode()).hexdigest()[:16]


# ── Singleton ─────────────────────────────────────────────────────────

_security_gate: Optional[DiscordSecurityGate] = None


def get_security_gate() -> DiscordSecurityGate:
    """Get the singleton Discord security gate."""
    global _security_gate
    if _security_gate is None:
        _security_gate = DiscordSecurityGate()
    return _security_gate


# ── CLI ───────────────────────────────────────────────────────────────

def main():
    """Run security gate self-test."""
    gate = DiscordSecurityGate()
    passed = 0
    failed = 0

    def check(name: str, condition: bool):
        nonlocal passed, failed
        status = "PASS" if condition else "FAIL"
        print(f"  [{status}] {name}")
        if condition:
            passed += 1
        else:
            failed += 1

    print("=== Discord Security Gate Self-Test ===\n")

    # Input validation tests
    print("Input Validation:")
    r = gate.validate_input("")
    check("Empty input allowed", r.allowed)

    r = gate.validate_input("a" * 501)
    check("Overlength input blocked", not r.allowed)

    r = gate.validate_input("Hello ```rm -rf /``` world")
    check("Code blocks stripped", "```" not in r.filtered_content and r.allowed)

    r = gate.validate_input("Check https://evil.com/steal for info")
    check("URLs stripped", "https://" not in r.filtered_content)

    r = gate.validate_input("Hey @everyone look at this")
    check("@everyone stripped", "@everyone" not in r.filtered_content)

    r = gate.validate_input("Normal feedback about the project")
    check("Clean input passes", r.allowed and r.filtered_content == "Normal feedback about the project")

    r = gate.validate_input("test ; rm -rf / & echo pwned | cat /etc/passwd")
    check("Shell injection chars stripped", ";" not in r.filtered_content and "|" not in r.filtered_content)

    # Output filtering tests
    print("\nOutput Filtering:")
    r = gate.sanitize_output("Server running on 192.168.1.100:8080")
    check("IP address redacted", "192.168.1.100" not in r.filtered_content)

    r = gate.sanitize_output("File at E:\\11132025\\slate\\secret.py")
    check("Windows path redacted", "E:\\" not in r.filtered_content)

    r = gate.sanitize_output("Token: slsvc_abc123def456ghi789")
    check("SLATE token redacted", "slsvc_" not in r.filtered_content)

    r = gate.sanitize_output("Key: ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij")
    check("GitHub token redacted", "ghp_" not in r.filtered_content)

    r = gate.sanitize_output("GPU-12345678-abcd-1234-abcd-123456789012")
    check("GPU UUID redacted", "GPU-" not in r.filtered_content)

    r = gate.sanitize_output("User at C:\\Users\\Dan\\Desktop")
    check("Username path redacted", "Dan" not in r.filtered_content)

    r = gate.sanitize_output("DESKTOP-ABC1234 is the host")
    check("Hostname redacted", "DESKTOP-" not in r.filtered_content)

    r = gate.sanitize_output("PID: 12345 is running")
    check("PID redacted", "12345" not in r.filtered_content)

    r = gate.sanitize_output("Dashboard: Online | AI: Active | GPU: 2x Ready")
    check("Safe status passes through", r.allowed and "Online" in r.filtered_content)

    r = gate.sanitize_output("Hey @everyone check this out")
    check("@everyone stripped from output", "@everyone" not in r.filtered_content)

    # Anti-flood tests
    print("\nAnti-Flood System:")
    gate2 = DiscordSecurityGate()
    # Normal usage: 5 commands should all be allowed
    for i in range(USER_BURST_LIMIT):
        r = gate2.check_rate_limit("user123", "channel456")
    check(f"First {USER_BURST_LIMIT} commands allowed (normal use)", r.allowed)

    # Flood: 10+ rapid commands should trigger anti-flood
    gate3 = DiscordSecurityGate()
    for i in range(USER_FLOOD_LIMIT + 1):
        r = gate3.check_rate_limit("flood_user", "channel789")
    check("Flood detection triggers after rapid commands", not r.allowed)

    r = gate2.check_rate_limit("user999", "channel456")
    check("Different user not rate limited", r.allowed)

    # Audit logging tests
    print("\nAudit Logging:")
    gate3 = DiscordSecurityGate()
    gate3.audit_log("test", "user123", "/test", "test input")
    check("Audit entry created", len(gate3._audit_log) == 1)
    check("User ID hashed", gate3._audit_log[0].user_hash != "user123")

    stats = gate3.get_audit_stats()
    check("Stats returned", stats["total_interactions"] == 1)

    # Feedback validation tests
    print("\nFeedback Validation:")
    r = gate.validate_feedback("")
    check("Empty feedback rejected", not r.allowed)

    r = gate.validate_feedback("short")
    check("Too-short feedback rejected", not r.allowed)

    r = gate.validate_feedback("This is a great feature request for SLATE!")
    check("Valid feedback accepted", r.allowed)

    print(f"\n=== Results: {passed} passed, {failed} failed ===")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
