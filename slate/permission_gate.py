#!/usr/bin/env python3
# Modified: 2026-02-09T12:39:00-05:00 | Author: Gemini (Antigravity)
# Change: Create SLATE permission gate enforcement engine
# NOTE: All AIs modifying this file must add a dated comment.
"""
SLATE Permission Gate
=====================

Central enforcement engine for all AI operations in the SLATE ecosystem.
Every AI action passes through this gate before execution.

The gate checks:
1. Agent's permission tier (0-5)
2. Target path against allowed/blocked lists
3. Operation type against tier capabilities
4. Guardrail constraints
5. Budget limits (token/API call quotas)

Usage:
    from slate.permission_gate import PermissionGate, PermissionResult

    gate = PermissionGate()
    result = gate.check("antigravity", "write", "slate/new_module.py")
    if result.allowed:
        # proceed
    else:
        print(f"Blocked: {result.reason}")
"""

import json
import os
import sys
import fnmatch
import hashlib
from datetime import datetime, timezone, timedelta
from enum import Enum
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any

# Workspace root detection
WORKSPACE_ROOT = Path(os.environ.get("SLATE_WORKSPACE", Path(__file__).parent.parent))
CONFIG_PATH = WORKSPACE_ROOT / ".slate_config" / "permissions.yaml"
AUDIT_DIR = WORKSPACE_ROOT / ".slate_analytics" / "permission_audit"

# ──────────────────────────────────────────────────────────
# Enums & Data Classes
# ──────────────────────────────────────────────────────────

class PermissionResult(Enum):
    """Result of a permission check."""
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


class OperationType(Enum):
    """Types of operations that can be checked."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    COMMIT = "commit"
    DEPLOY = "deploy"
    WORKFLOW_MODIFY = "workflow_modification"
    SECRET_ACCESS = "secret_access"
    BRANCH_DELETE = "branch_deletion"
    PERMISSION_CHANGE = "permission_change"


# Tier capability matrix — what each tier CAN do
TIER_CAPABILITIES: Dict[int, Dict[str, bool]] = {
    0: {  # OBSERVER
        "read": True, "write": False, "delete": False, "execute": False,
        "commit": False, "deploy": False, "workflow_modification": False,
        "secret_access": False, "branch_deletion": False, "permission_change": False,
    },
    1: {  # ADVISOR
        "read": True, "write": False, "delete": False, "execute": False,
        "commit": False, "deploy": False, "workflow_modification": False,
        "secret_access": False, "branch_deletion": False, "permission_change": False,
    },
    2: {  # COLLABORATOR
        "read": True, "write": True, "delete": False, "execute": True,
        "commit": True, "deploy": False, "workflow_modification": False,
        "secret_access": False, "branch_deletion": False, "permission_change": False,
    },
    3: {  # DEVELOPER
        "read": True, "write": True, "delete": True, "execute": True,
        "commit": True, "deploy": False, "workflow_modification": False,
        "secret_access": False, "branch_deletion": False, "permission_change": False,
    },
    4: {  # ARCHITECT
        "read": True, "write": True, "delete": True, "execute": True,
        "commit": True, "deploy": True, "workflow_modification": True,
        "secret_access": False, "branch_deletion": False, "permission_change": False,
    },
    5: {  # AUTONOMOUS
        "read": True, "write": True, "delete": True, "execute": True,
        "commit": True, "deploy": True, "workflow_modification": True,
        "secret_access": True, "branch_deletion": True, "permission_change": True,
    },
}

TIER_NAMES = {
    0: "OBSERVER",
    1: "ADVISOR",
    2: "COLLABORATOR",
    3: "DEVELOPER",
    4: "ARCHITECT",
    5: "AUTONOMOUS",
}


@dataclass
class CheckResult:
    """Full result of a permission check."""
    result: PermissionResult
    allowed: bool
    agent: str
    operation: str
    target: str
    tier: int
    tier_name: str
    reason: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["result"] = self.result.value
        return d


@dataclass
class AuditEntry:
    """Immutable audit trail entry."""
    timestamp: str
    agent: str
    operation: str
    target: str
    result: str
    tier: int
    reason: str
    session_id: str = ""


@dataclass
class BudgetTracker:
    """Per-agent budget tracking."""
    agent: str
    window_start: datetime
    tokens_used: int = 0
    api_calls: int = 0
    max_tokens: int = 500000
    max_calls: int = 100

    @property
    def tokens_remaining(self) -> int:
        return max(0, self.max_tokens - self.tokens_used)

    @property
    def calls_remaining(self) -> int:
        return max(0, self.max_calls - self.api_calls)

    @property
    def window_expired(self) -> bool:
        return datetime.now(timezone.utc) - self.window_start > timedelta(hours=1)

    def reset_if_expired(self):
        if self.window_expired:
            self.window_start = datetime.now(timezone.utc)
            self.tokens_used = 0
            self.api_calls = 0


# ──────────────────────────────────────────────────────────
# Configuration Loader
# ──────────────────────────────────────────────────────────

def _load_permissions_config(config_path: Path = CONFIG_PATH) -> Dict[str, Any]:
    """Load permissions.yaml, handling both YAML and fallback."""
    if not config_path.exists():
        return _default_config()

    try:
        # Attempt YAML import
        import yaml
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        return config if config else _default_config()
    except ImportError:
        # Fallback: parse key YAML fields manually for minimal YAML subset
        return _parse_minimal_yaml(config_path)
    except Exception:
        return _default_config()


def _parse_minimal_yaml(path: Path) -> Dict[str, Any]:
    """Minimal YAML parser for the permissions config (handles our known format)."""
    config = _default_config()
    try:
        text = path.read_text(encoding="utf-8")
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("default_tier:"):
                val = stripped.split(":", 1)[1].strip()
                config["default_tier"] = int(val)
    except Exception:
        pass
    return config


def _default_config() -> Dict[str, Any]:
    """Default permission configuration."""
    return {
        "version": "1.0.0",
        "default_tier": 3,
        "agents": {},
        "guardrails": {
            "require_audit_trail": True,
            "max_files_per_commit": 50,
            "banned_operations": [],
            "protected_branches": ["main"],
            "require_approval_for": [
                "workflow_modification",
                "secret_access",
                "deployment",
                "branch_deletion",
                "permission_change",
            ],
        },
        "notifications": {
            "on_tier_escalation": True,
            "on_blocked_action": True,
            "on_autonomous_completion": True,
            "on_budget_exceeded": True,
        },
    }


# ──────────────────────────────────────────────────────────
# Permission Gate
# ──────────────────────────────────────────────────────────

class PermissionGate:
    """
    Central permission enforcement for all AI operations.

    Every AI action passes through this gate. The gate checks:
    1. Agent's permission tier
    2. Target path against allowed/blocked lists
    3. Operation type against tier capabilities
    4. Guardrail constraints
    5. Budget limits (token/API call quotas)
    """

    def __init__(self, config_path: Path = CONFIG_PATH):
        self.config_path = config_path
        self.config = _load_permissions_config(config_path)
        self._budgets: Dict[str, BudgetTracker] = {}
        self._audit_buffer: List[AuditEntry] = []
        self._session_id = hashlib.md5(
            datetime.now(timezone.utc).isoformat().encode()
        ).hexdigest()[:12]

        # Ensure audit directory
        AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    def reload_config(self):
        """Reload the permissions config from disk."""
        self.config = _load_permissions_config(self.config_path)

    # ──── Primary API ────

    def check(self, agent: str, operation: str, target: str = "") -> CheckResult:
        """
        Check whether an agent is allowed to perform an operation on a target.

        Args:
            agent: Agent identifier (e.g., "antigravity", "copilot", "claude")
            operation: Operation type (e.g., "read", "write", "commit", "deploy")
            target: Target path or resource (e.g., "slate/new_module.py")

        Returns:
            CheckResult with allow/deny/require_approval and reason
        """
        # 1. Resolve agent tier
        tier = self._resolve_tier(agent)
        tier_name = TIER_NAMES.get(tier, f"TIER_{tier}")

        # 2. Check tier capability
        capabilities = TIER_CAPABILITIES.get(tier, TIER_CAPABILITIES[0])
        op_key = operation.lower()

        if op_key not in capabilities or not capabilities.get(op_key, False):
            result = self._make_result(
                PermissionResult.DENY, agent, operation, target, tier, tier_name,
                f"Tier {tier} ({tier_name}) does not have '{operation}' capability"
            )
            self._log_audit(result)
            return result

        # 3. Check blocked paths
        agent_config = self.config.get("agents", {}).get(agent, {})
        blocked = agent_config.get("blocked_paths", [])
        for pattern in blocked:
            if fnmatch.fnmatch(target, pattern):
                result = self._make_result(
                    PermissionResult.DENY, agent, operation, target, tier, tier_name,
                    f"Path '{target}' matches blocked pattern '{pattern}'"
                )
                self._log_audit(result)
                return result

        # 4. Check allowed paths (if specified — empty means all allowed)
        allowed = agent_config.get("allowed_paths", [])
        if allowed and target:
            path_allowed = any(fnmatch.fnmatch(target, p) for p in allowed)
            if not path_allowed:
                result = self._make_result(
                    PermissionResult.DENY, agent, operation, target, tier, tier_name,
                    f"Path '{target}' not in allowed paths: {allowed}"
                )
                self._log_audit(result)
                return result

        # 5. Check guardrails
        guardrails = self.config.get("guardrails", {})
        approval_required = guardrails.get("require_approval_for", [])
        if op_key in approval_required or operation in approval_required:
            require_approval = True
            # Tier 5 (AUTONOMOUS) bypasses approval requirements
            if tier >= 5:
                require_approval = False
            if require_approval:
                result = self._make_result(
                    PermissionResult.REQUIRE_APPROVAL, agent, operation, target,
                    tier, tier_name,
                    f"Operation '{operation}' requires user approval (guardrail)"
                )
                self._log_audit(result)
                return result

        # 6. Check banned operations
        banned = guardrails.get("banned_operations", [])
        if target in banned or operation in banned:
            result = self._make_result(
                PermissionResult.DENY, agent, operation, target, tier, tier_name,
                f"Operation/target is in banned list"
            )
            self._log_audit(result)
            return result

        # 7. Check specific agent flags
        if operation == "commit" and not agent_config.get("can_commit", True):
            result = self._make_result(
                PermissionResult.DENY, agent, operation, target, tier, tier_name,
                f"Agent '{agent}' has can_commit=false"
            )
            self._log_audit(result)
            return result

        if operation == "deploy" and not agent_config.get("can_deploy", False):
            result = self._make_result(
                PermissionResult.DENY, agent, operation, target, tier, tier_name,
                f"Agent '{agent}' has can_deploy=false"
            )
            self._log_audit(result)
            return result

        # 8. Budget check
        budget = self._get_budget(agent)
        if budget and budget.calls_remaining <= 0:
            result = self._make_result(
                PermissionResult.DENY, agent, operation, target, tier, tier_name,
                f"Agent '{agent}' has exceeded API call budget ({budget.max_calls}/hr)"
            )
            self._log_audit(result)
            return result

        # ✅ ALLOWED
        result = self._make_result(
            PermissionResult.ALLOW, agent, operation, target, tier, tier_name,
            f"Allowed: tier={tier} ({tier_name})"
        )
        self._log_audit(result)
        return result

    def record_usage(self, agent: str, tokens: int = 0, api_calls: int = 1):
        """Record token/API usage against agent budget."""
        budget = self._get_budget(agent)
        if budget:
            budget.reset_if_expired()
            budget.tokens_used += tokens
            budget.api_calls += api_calls

    def get_agent_status(self, agent: str) -> Dict[str, Any]:
        """Get complete status for an agent."""
        tier = self._resolve_tier(agent)
        budget = self._get_budget(agent)
        agent_config = self.config.get("agents", {}).get(agent, {})

        return {
            "agent": agent,
            "tier": tier,
            "tier_name": TIER_NAMES.get(tier, f"TIER_{tier}"),
            "can_commit": agent_config.get("can_commit", True),
            "can_deploy": agent_config.get("can_deploy", False),
            "review_required": agent_config.get("review_required", False),
            "budget": {
                "tokens_used": budget.tokens_used if budget else 0,
                "tokens_remaining": budget.tokens_remaining if budget else "unlimited",
                "api_calls_used": budget.api_calls if budget else 0,
                "api_calls_remaining": budget.calls_remaining if budget else "unlimited",
            } if budget else None,
            "allowed_paths": agent_config.get("allowed_paths", ["**/*"]),
            "blocked_paths": agent_config.get("blocked_paths", []),
        }

    def get_all_agents_status(self) -> List[Dict[str, Any]]:
        """Get status for all configured agents."""
        agents = list(self.config.get("agents", {}).keys())
        return [self.get_agent_status(a) for a in agents]

    def escalate(self, agent: str, reason: str, target_tier: int = None) -> CheckResult:
        """
        Request temporary tier escalation from user.

        This returns a REQUIRE_APPROVAL result that the UI layer
        should present to the user for decision.
        """
        current_tier = self._resolve_tier(agent)
        requested = target_tier if target_tier is not None else current_tier + 1

        result = self._make_result(
            PermissionResult.REQUIRE_APPROVAL, agent, "escalation",
            f"tier_{current_tier}_to_{requested}",
            current_tier, TIER_NAMES.get(current_tier, ""),
            f"Escalation request: {reason}. Current={current_tier}, Requested={requested}"
        )
        self._log_audit(result)
        return result

    # ──── Internal Methods ────

    def _resolve_tier(self, agent: str) -> int:
        """Resolve the effective tier for an agent."""
        agents_config = self.config.get("agents", {})
        if agent in agents_config:
            return agents_config[agent].get("tier", self.config.get("default_tier", 3))
        return self.config.get("default_tier", 3)

    def _get_budget(self, agent: str) -> Optional[BudgetTracker]:
        """Get or create budget tracker for an agent."""
        agent_config = self.config.get("agents", {}).get(agent, {})
        budget_config = agent_config.get("budget")

        if not budget_config:
            return None

        if agent not in self._budgets:
            self._budgets[agent] = BudgetTracker(
                agent=agent,
                window_start=datetime.now(timezone.utc),
                max_tokens=budget_config.get("max_tokens_per_hour", 500000),
                max_calls=budget_config.get("max_api_calls_per_hour", 100),
            )
        tracker = self._budgets[agent]
        tracker.reset_if_expired()
        return tracker

    def _make_result(self, result: PermissionResult, agent: str, operation: str,
                     target: str, tier: int, tier_name: str, reason: str) -> CheckResult:
        return CheckResult(
            result=result,
            allowed=(result == PermissionResult.ALLOW),
            agent=agent,
            operation=operation,
            target=target,
            tier=tier,
            tier_name=tier_name,
            reason=reason,
        )

    def _log_audit(self, check_result: CheckResult):
        """Log to audit trail (append-only)."""
        entry = AuditEntry(
            timestamp=check_result.timestamp,
            agent=check_result.agent,
            operation=check_result.operation,
            target=check_result.target,
            result=check_result.result.value,
            tier=check_result.tier,
            reason=check_result.reason,
            session_id=self._session_id,
        )
        self._audit_buffer.append(entry)

        # Flush every 10 entries
        if len(self._audit_buffer) >= 10:
            self.flush_audit()

    def flush_audit(self):
        """Write buffered audit entries to disk."""
        if not self._audit_buffer:
            return
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        audit_file = AUDIT_DIR / f"audit_{today}.jsonl"
        try:
            with open(audit_file, "a", encoding="utf-8") as f:
                for entry in self._audit_buffer:
                    f.write(json.dumps(asdict(entry)) + "\n")
            self._audit_buffer.clear()
        except Exception as e:
            print(f"[PermissionGate] Audit flush error: {e}", file=sys.stderr)

    def get_audit_entries(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Read recent audit entries."""
        entries = []
        # Include buffer
        for e in self._audit_buffer[-limit:]:
            entries.append(asdict(e))

        # Read from today's file
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        audit_file = AUDIT_DIR / f"audit_{today}.jsonl"
        if audit_file.exists():
            try:
                lines = audit_file.read_text(encoding="utf-8").strip().splitlines()
                for line in lines[-limit:]:
                    entries.append(json.loads(line))
            except Exception:
                pass

        return entries[-limit:]

    def __del__(self):
        """Flush remaining audit entries on shutdown."""
        try:
            self.flush_audit()
        except Exception:
            pass


# ──────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────

def main():
    """CLI entry point: slate permissions [show|check|audit]"""
    import argparse
    parser = argparse.ArgumentParser(description="SLATE Permission Gate CLI")
    sub = parser.add_subparsers(dest="command")

    # show
    show_p = sub.add_parser("show", help="Show agent permission status")
    show_p.add_argument("--agent", help="Specific agent to show")

    # check
    check_p = sub.add_parser("check", help="Check a specific permission")
    check_p.add_argument("agent", help="Agent identifier")
    check_p.add_argument("operation", help="Operation type")
    check_p.add_argument("target", nargs="?", default="", help="Target path/resource")

    # audit
    audit_p = sub.add_parser("audit", help="Show recent audit entries")
    audit_p.add_argument("--limit", type=int, default=20, help="Number of entries")

    args = parser.parse_args()
    gate = PermissionGate()

    if args.command == "show":
        if args.agent:
            status = gate.get_agent_status(args.agent)
            print(json.dumps(status, indent=2))
        else:
            statuses = gate.get_all_agents_status()
            for s in statuses:
                print(f"  {s['agent']:20s}  Tier {s['tier']} ({s['tier_name']})"
                      f"  commit={s['can_commit']}  deploy={s['can_deploy']}")
    elif args.command == "check":
        result = gate.check(args.agent, args.operation, args.target)
        icon = "✅" if result.allowed else ("⚠️" if result.result == PermissionResult.REQUIRE_APPROVAL else "❌")
        print(f"{icon} {result.result.value.upper()}: {result.reason}")
    elif args.command == "audit":
        entries = gate.get_audit_entries(args.limit)
        for e in entries:
            icon = "✅" if e.get("result") == "allow" else "❌"
            print(f"  {icon} [{e.get('timestamp', '?')[:19]}] "
                  f"{e.get('agent', '?'):15s} {e.get('operation', '?'):10s} "
                  f"{e.get('target', '?')}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
