# Modified: 2026-02-09T12:00:00Z | Author: COPILOT | Change: Add PROTECTED_PATHS and validate_file_write to prevent AI overwriting production files
# Modified: 2026-02-07T09:00:00Z | Author: COPILOT | Change: Add Kubernetes security patterns and container validation
"""
ActionGuard - Security enforcement for SLATE agent actions.

Validates all agent actions before execution, blocks dangerous operations,
enforces network binding rules, and logs security decisions.

Security rules:
- ALL network bindings must use 127.0.0.1 (never 0.0.0.0)
- Blocked patterns: eval(, exec(os, rm -rf /, base64.b64decode
- Blocked external API domains (local-first enforcement)
- Rate limiting on API calls
- Kubernetes: privileged pods, hostNetwork, hostPID blocked
- Container images: only trusted registries allowed
- PROTECTED_PATHS: production files AI must never overwrite
"""

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger("slate.action_guard")

# ── Security Configuration ──────────────────────────────────────────────

BLOCKED_PATTERNS = [
    # Code execution safety
    r"eval\(",
    r"exec\(os",
    r"rm\s+-rf\s+/",
    r"base64\.b64decode",
    r"0\.0\.0\.0",
    r"subprocess\.call.*shell\s*=\s*True",
    r"__import__\(",
    r"os\.system\(",
    # Ethics enforcement (Constitution Section II)
    r"nmap\s+",                       # Network scanning / hacking tools
    r"metasploit",                    # Exploitation framework
    r"sqlmap",                        # SQL injection tool
    r"hashcat",                       # Password cracking
    r"john\s+",                       # John the Ripper password cracking
    r"hydra\s+",                      # Brute force tool
    r"aircrack",                      # WiFi cracking
    r"wireshark.*capture",            # Packet capture (passive surveillance)
    r"keylog",                        # Keylogger patterns
    r"reverse.?shell",               # Reverse shell creation
    r"bind.?shell",                   # Bind shell creation
    r"payload.*msfvenom",            # Metasploit payload generation
    r"exploit[_\-]db",               # Exploit database queries
    r"cve[_\-]\d{4}[_\-]\d+.*exploit",  # CVE exploitation (research reading is OK)
    r"cryptominer|xmrig|minerd",     # Cryptocurrency mining
    r"phish|spoof.*email",           # Phishing/spoofing
    r"ddos|flood.*attack",           # DDoS attack tools
    r"ransomware|encrypt.*ransom",   # Ransomware patterns
]

# Kubernetes-specific blocked patterns (YAML manifest scanning)
K8S_BLOCKED_PATTERNS = [
    r"privileged:\s*true",
    r"hostNetwork:\s*true",
    r"hostPID:\s*true",
    r"hostIPC:\s*true",
    r"allowPrivilegeEscalation:\s*true",
    r"runAsUser:\s*0\b",  # Running as root
    r"hostPort:",  # Exposing host ports
    r"type:\s*NodePort",  # Exposing services externally (use ClusterIP + port-forward)
    r"type:\s*LoadBalancer",  # External exposure
    r"automountServiceAccountToken:\s*true",
]

# Trusted container registries
TRUSTED_REGISTRIES = [
    "ghcr.io/synchronizedlivingarchitecture/",
    "ollama/ollama",
    "chromadb/chroma",
    "nvidia/cuda",
    "python:",
    "ubuntu:",
    "docker.io/library/",
]

BLOCKED_DOMAINS = [
    "api.openai.com",
    "api.anthropic.com",
    "api.cohere.com",
    "generativelanguage.googleapis.com",
]

# Production files that autonomous AI must NEVER overwrite.
# These are matched as suffixes against normalized paths (forward slashes).
# Modified: 2026-02-09T12:00:00Z | Author: COPILOT | Change: Add protected path list for AI write prevention
PROTECTED_PATHS: list[str] = [
    # ── Core SDK (the engine itself) ─────────────────────────────────────
    "slate/slate_unified_autonomous.py",
    "slate/integrated_autonomous_loop.py",
    "slate/copilot_slate_runner.py",
    "slate/action_guard.py",
    "slate/sdk_source_guard.py",
    "slate/pii_scanner.py",
    "slate/mcp_server.py",
    "slate/slate_status.py",
    "slate/slate_runtime.py",
    "slate/slate_runner_manager.py",
    "slate/slate_orchestrator.py",
    "slate/slate_workflow_manager.py",
    "slate/slate_hardware_optimizer.py",
    "slate/slate_gpu_manager.py",
    "slate/slate_k8s_deploy.py",
    "slate/slate_benchmark.py",
    "slate/slate_chromadb.py",
    "slate/ml_orchestrator.py",
    "slate/slate_model_trainer.py",
    "slate/slate_project_board.py",
    "slate/slate_fork_manager.py",
    "slate/adaptive_instructions.py",
    "slate/copilot_agent_bridge.py",
    "slate/unified_ai_backend.py",
    "slate/slate_semantic_kernel.py",
    "slate/instruction_loader.py",
    "slate/feature_flags.py",
    "slate/install_tracker.py",
    # ── Agents & APIs ───────────────────────────────────────────────────
    "agents/runner_api.py",
    "agents/slate_dashboard_server.py",
    "agents/install_api.py",
    # ── Config & Infrastructure ─────────────────────────────────────────
    "pyproject.toml",
    "requirements.txt",
    "Dockerfile",
    "Dockerfile.cpu",
    "Dockerfile.dev",
    "docker-compose.yml",
    "docker-compose.dev.yml",
    "docker-compose.prod.yml",
    "install_slate.py",
    "slate_startup.py",
    # ── Instruction & Protocol Files ────────────────────────────────────
    "AGENTS.md",
    "CLAUDE.md",
    "FORGE.md",
    "README.md",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "current_tasks.json",
]

# Directory patterns that are entirely protected (AI cannot write any file in them)
# CRITICAL: This is the PRIMARY defense against autonomous AI overwriting production code.
# The deny-by-default policy (AI_WRITABLE_DIRS allowlist) is the SECONDARY defense.
# Both must agree before any write is allowed.
PROTECTED_DIRS: list[str] = [
    # ── Production Source Code (NEVER writable by AI) ──────────────────
    "slate/",                    # ALL production engine modules
    "slate_core/",               # Shared infrastructure
    "agents/",                   # Dashboard server, APIs
    "src/",                      # Frontend/backend source
    # ── Configuration & Infrastructure ─────────────────────────────────
    ".github/",
    ".claude/",
    ".claude-plugin/",
    "k8s/",
    "helm/",
    "actions-runner/",
    # ── Plugin Source Code ─────────────────────────────────────────────
    "plugins/",
    "skills/",
    "instructions/",
    "hooks/",
    # ── Documentation & Pages ──────────────────────────────────────────
    "docs/",
    "specs/",
    # ── Security-Sensitive ─────────────────────────────────────────────
    "grafana/",
    "scripts/",
    "vendor/",
    "models/",
]

# Directories where AI IS allowed to write
AI_WRITABLE_DIRS: list[str] = [
    "tests/",
    "slate_logs/",
    "slate_memory/",
    "logs/",
    "data/",
]

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "::1",
]

ALLOWED_GITHUB_DOMAINS = [
    "api.github.com",
    "github.com",
    "raw.githubusercontent.com",
    "models.inference.ai.azure.com",  # GitHub Models free-tier AI endpoint
]
# Modified: 2026-02-09T02:00:00Z | Author: COPILOT | Change: Add GitHub Models endpoint to allowed domains

# Discord API domains (bot gateway + CDN only)
# Modified: 2026-02-09T18:00:00Z | Author: Claude Opus 4.6 | Change: Add Discord domains for bot integration
ALLOWED_DISCORD_DOMAINS = [
    "discord.com",
    "gateway.discord.gg",
    "cdn.discordapp.com",
]

# Discord-specific blocked patterns (prevent bot abuse)
DISCORD_BLOCKED_PATTERNS = [
    r"@everyone",           # Mass ping prevention
    r"@here",               # Mass ping prevention
    r"discord\.gg/",        # No invite link generation from bot
    r"<@&\d+>",            # No role mentions from bot output
]

# Rate limiting: max calls per minute per action type
RATE_LIMITS = {
    "api_call": 60,
    "file_write": 120,
    "command_exec": 30,
    "network_request": 30,
    "discord_command": 60,  # Discord slash command processing
    "discord_send": 30,     # Discord webhook/message sends
}


# ── Data Classes ────────────────────────────────────────────────────────

@dataclass
class ActionResult:
    """Result of an action guard validation."""
    allowed: bool
    action: str
    reason: str = ""
    timestamp: float = field(default_factory=time.time)

    def __str__(self) -> str:
        status = "ALLOWED" if self.allowed else "BLOCKED"
        return f"[{status}] {self.action}: {self.reason}"


@dataclass
class RateTracker:
    """Tracks action rates for rate limiting."""
    calls: list = field(default_factory=list)

    def add(self) -> None:
        self.calls.append(time.time())

    def count_recent(self, window: float = 60.0) -> int:
        cutoff = time.time() - window
        self.calls = [t for t in self.calls if t > cutoff]
        return len(self.calls)


# ── ActionGuard Class ───────────────────────────────────────────────────

class ActionGuard:
    """
    Validates agent actions against SLATE security policies.

    Usage:
        guard = ActionGuard()
        result = guard.validate_action("command_exec", "python slate/slate_status.py --quick")
        if result.allowed:
            # proceed
        else:
            logger.warning(f"Action blocked: {result}")
    """

    def __init__(self, strict: bool = True):
        self.strict = strict
        self._rate_trackers: dict[str, RateTracker] = {}
        self._audit_log: list[ActionResult] = []
        self._compiled_patterns = [re.compile(p, re.IGNORECASE) for p in BLOCKED_PATTERNS]

    def validate_action(self, action_type: str, content: str) -> ActionResult:
        """
        Validate an action against security policies.

        Args:
            action_type: Type of action (command_exec, api_call, file_write, network_request)
            content: The content/command to validate

        Returns:
            ActionResult with allowed status and reason
        """
        # Check blocked patterns
        for pattern in self._compiled_patterns:
            if pattern.search(content):
                result = ActionResult(
                    allowed=False,
                    action=action_type,
                    reason=f"Blocked pattern: {pattern.pattern}",
                )
                self._audit(result)
                return result

        # Check network binding
        if "0.0.0.0" in content:
            result = ActionResult(
                allowed=False,
                action=action_type,
                reason="Network binding violation: must use 127.0.0.1",
            )
            self._audit(result)
            return result

        # Check blocked domains
        for domain in BLOCKED_DOMAINS:
            if domain in content:
                result = ActionResult(
                    allowed=False,
                    action=action_type,
                    reason=f"Blocked external domain: {domain}",
                )
                self._audit(result)
                return result

        # Rate limiting
        if action_type in RATE_LIMITS:
            tracker = self._rate_trackers.setdefault(action_type, RateTracker())
            if tracker.count_recent() >= RATE_LIMITS[action_type]:
                result = ActionResult(
                    allowed=False,
                    action=action_type,
                    reason=f"Rate limit exceeded: {RATE_LIMITS[action_type]}/min",
                )
                self._audit(result)
                return result
            tracker.add()

        result = ActionResult(
            allowed=True,
            action=action_type,
            reason="Passed all security checks",
        )
        self._audit(result)
        return result

    def validate_host(self, host: str) -> ActionResult:
        """Validate a network host binding."""
        if host in ALLOWED_HOSTS:
            return ActionResult(allowed=True, action="host_bind", reason=f"Allowed host: {host}")
        if host in ALLOWED_GITHUB_DOMAINS:
            return ActionResult(allowed=True, action="host_bind", reason=f"Allowed GitHub domain: {host}")
        return ActionResult(
            allowed=False,
            action="host_bind",
            reason=f"Blocked host: {host}. Only 127.0.0.1/localhost allowed.",
        )

    def validate_command(self, command: str) -> ActionResult:
        """Shorthand for validating a command execution."""
        return self.validate_action("command_exec", command)

    def validate_file_path(self, path: str) -> ActionResult:
        """Validate a file path for safety."""
        dangerous_paths = ["/etc/passwd", "/etc/shadow", "C:\\Windows\\System32"]
        for dp in dangerous_paths:
            if dp.lower() in path.lower():
                return ActionResult(
                    allowed=False,
                    action="file_access",
                    reason=f"Dangerous path: {dp}",
                )
        return ActionResult(allowed=True, action="file_access", reason="Path OK")

    # Modified: 2026-02-09T12:00:00Z | Author: COPILOT | Change: Add validate_file_write for AI production file protection
    def validate_file_write(self, path: str) -> ActionResult:
        """Validate whether the autonomous AI is allowed to write to a file.

        This is the CRITICAL safety gate that prevents the local AI inference
        loop from overwriting production source code, configs, workflows,
        K8s manifests, instruction files, and security guards.

        AI is ONLY allowed to write to:
        - tests/         (generated test files)
        - slate_logs/    (audit logs, backups)
        - slate_memory/  (context memory)
        - logs/          (runtime logs)
        - data/          (data artifacts)

        Everything else is BLOCKED.
        """
        # Normalize to forward slashes for consistent matching
        norm = path.replace("\\", "/")
        # Strip workspace prefix if present (handle absolute paths)
        for prefix in ["E:/11132025/", "e:/11132025/", "/workspace/"]:
            if norm.lower().startswith(prefix.lower()):
                norm = norm[len(prefix):]
                break

        # Check against explicitly protected individual files
        for protected in PROTECTED_PATHS:
            if norm == protected or norm.endswith("/" + protected):
                result = ActionResult(
                    allowed=False,
                    action="file_write",
                    reason=f"PROTECTED production file: {protected}",
                )
                self._audit(result)
                return result

        # Check against protected directory patterns
        for pdir in PROTECTED_DIRS:
            if norm.startswith(pdir) or ("/" + pdir) in norm:
                result = ActionResult(
                    allowed=False,
                    action="file_write",
                    reason=f"PROTECTED directory: {pdir}",
                )
                self._audit(result)
                return result

        # Explicitly allow writable directories
        for wdir in AI_WRITABLE_DIRS:
            if norm.startswith(wdir):
                result = ActionResult(
                    allowed=True,
                    action="file_write",
                    reason=f"AI-writable directory: {wdir}",
                )
                self._audit(result)
                return result

        # Default: BLOCK any file not in the writable list
        # This is a deny-by-default policy — AI must write to designated dirs only
        result = ActionResult(
            allowed=False,
            action="file_write",
            reason=f"Not in AI-writable directories: {norm}",
        )
        self._audit(result)
        return result

    def validate_k8s_manifest(self, manifest_content: str) -> ActionResult:
        """Validate a Kubernetes manifest for security violations.

        Checks for:
        - Privileged containers
        - hostNetwork/hostPID/hostIPC usage
        - Running as root (UID 0)
        - Host port exposure
        - NodePort/LoadBalancer services (should use ClusterIP)
        - Auto-mounted service account tokens
        """
        compiled_k8s = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in K8S_BLOCKED_PATTERNS]
        violations = []
        for pattern in compiled_k8s:
            matches = pattern.findall(manifest_content)
            if matches:
                violations.append(pattern.pattern)

        if violations:
            result = ActionResult(
                allowed=False,
                action="k8s_manifest",
                reason=f"K8s security violations: {', '.join(violations)}",
            )
            self._audit(result)
            return result

        result = ActionResult(
            allowed=True,
            action="k8s_manifest",
            reason="K8s manifest passed all security checks",
        )
        self._audit(result)
        return result

    def validate_container_image(self, image: str) -> ActionResult:
        """Validate a container image is from a trusted registry."""
        for registry in TRUSTED_REGISTRIES:
            if image.startswith(registry):
                return ActionResult(
                    allowed=True,
                    action="container_image",
                    reason=f"Trusted registry: {registry}",
                )

        result = ActionResult(
            allowed=False,
            action="container_image",
            reason=f"Untrusted container image: {image}. Only trusted registries allowed.",
        )
        self._audit(result)
        return result

    def get_audit_log(self) -> list[ActionResult]:
        """Return the audit log of all validated actions."""
        return self._audit_log.copy()

    def get_blocked_count(self) -> int:
        """Return count of blocked actions."""
        return sum(1 for r in self._audit_log if not r.allowed)

    def _audit(self, result: ActionResult) -> None:
        """Record action in audit log."""
        self._audit_log.append(result)
        if not result.allowed:
            logger.warning(str(result))
        else:
            logger.debug(str(result))


# ── Module-Level Functions ──────────────────────────────────────────────

_default_guard: Optional[ActionGuard] = None


def get_guard() -> ActionGuard:
    """Get the default ActionGuard singleton."""
    global _default_guard
    if _default_guard is None:
        _default_guard = ActionGuard()
    return _default_guard


def validate_action(action_type: str, content: str) -> ActionResult:
    """Validate an action using the default guard."""
    return get_guard().validate_action(action_type, content)


def validate_command(command: str) -> ActionResult:
    """Validate a command using the default guard."""
    return get_guard().validate_command(command)


def is_safe(action_type: str, content: str) -> bool:
    """Quick check - returns True if action is allowed."""
    return get_guard().validate_action(action_type, content).allowed


# ── CLI ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    guard = ActionGuard()

    # Self-test
    tests = [
        ("command_exec", "python slate/slate_status.py --quick", True),
        ("command_exec", 'eval("dangerous")', False),
        ("command_exec", "rm -rf /", False),
        ("network_request", "http://127.0.0.1:8080/api", True),
        ("network_request", "http://0.0.0.0:8080", False),
        ("network_request", "https://api.openai.com/v1/chat", False),
        ("network_request", "https://api.github.com/repos", True),
        ("command_exec", 'exec(os.system("whoami"))', False),
        ("command_exec", "base64.b64decode(payload)", False),
    ]

    # K8s manifest tests
    k8s_tests = [
        ("privileged: true", False),
        ("hostNetwork: true", False),
        ("allowPrivilegeEscalation: false\nrunAsNonRoot: true", True),
        ("type: NodePort", False),
        ("type: ClusterIP", True),
        ("runAsUser: 0", False),
        ("runAsUser: 1000\nrunAsNonRoot: true", True),
    ]

    # Container image tests
    image_tests = [
        ("ghcr.io/synchronizedlivingarchitecture/slate:latest-gpu", True),
        ("ollama/ollama:latest", True),
        ("nvidia/cuda:12.4.1-runtime-ubuntu22.04", True),
        ("evil-registry.io/malware:latest", False),
        ("chromadb/chroma:latest", True),
    ]

    # Modified: 2026-02-09T12:00:00Z | Author: COPILOT | Change: Add file write self-tests
    # File write protection tests (AI autonomous write validation)
    file_write_tests = [
        # BLOCKED: production source files
        ("slate/slate_unified_autonomous.py", False),
        ("slate/action_guard.py", False),
        ("slate/slate_status.py", False),
        ("slate/ml_orchestrator.py", False),
        ("agents/runner_api.py", False),
        ("agents/slate_dashboard_server.py", False),
        # BLOCKED: config & infra files
        ("pyproject.toml", False),
        ("Dockerfile", False),
        ("docker-compose.yml", False),
        ("AGENTS.md", False),
        ("current_tasks.json", False),
        ("install_slate.py", False),
        # BLOCKED: protected directories
        (".github/workflows/ci.yml", False),
        (".claude/settings.json", False),
        ("k8s/deployments.yaml", False),
        ("helm/values.yaml", False),
        ("plugins/slate-copilot/src/extension.ts", False),
        ("skills/slate-status/skill.md", False),
        ("instructions/slate-python.instructions.md", False),
        ("vendor/spec-kit/README.md", False),
        ("models/Modelfile.slate-coder", False),
        ("scripts/deploy.ps1", False),
        # ALLOWED: test files
        ("tests/test_guided_mode.py", True),
        ("tests/test_action_guard.py", True),
        # ALLOWED: log files
        ("slate_logs/backups/file_20260209.py.bak", True),
        ("logs/output.log", True),
        # ALLOWED: data directory
        ("data/results.json", True),
        # BLOCKED: arbitrary source files not in writable list
        ("slate/new_module.py", False),
        ("some_random_file.py", False),
    ]

    print("=" * 50)
    print("  ActionGuard Self-Test")
    print("=" * 50)

    passed = 0
    failed = 0
    for action_type, content, expected in tests:
        result = guard.validate_action(action_type, content)
        ok = result.allowed == expected
        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        else:
            failed += 1
        print(f"  {status}: {action_type} | {content[:50]} | expected={expected} got={result.allowed}")

    print(f"\n  Results: {passed} passed, {failed} failed")
    print(f"  Blocked: {guard.get_blocked_count()} actions")

    # K8s manifest tests
    print("\n  K8s Manifest Tests:")
    for manifest, expected in k8s_tests:
        result = guard.validate_k8s_manifest(manifest)
        ok = result.allowed == expected
        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        else:
            failed += 1
        print(f"  {status}: k8s_manifest | {manifest[:50]} | expected={expected} got={result.allowed}")

    # Container image tests
    print("\n  Container Image Tests:")
    for image, expected in image_tests:
        result = guard.validate_container_image(image)
        ok = result.allowed == expected
        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        else:
            failed += 1
        print(f"  {status}: container_image | {image} | expected={expected} got={result.allowed}")
    # File write protection tests
    print("\n  AI File Write Protection Tests:")
    for fpath, expected in file_write_tests:
        result = guard.validate_file_write(fpath)
        ok = result.allowed == expected
        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        else:
            failed += 1
        print(f"  {status}: file_write | {fpath[:50]} | expected={expected} got={result.allowed}")
    print(f"\n  Total Results: {passed} passed, {failed} failed")
    print("=" * 50)

    if failed > 0:
        sys.exit(1)
