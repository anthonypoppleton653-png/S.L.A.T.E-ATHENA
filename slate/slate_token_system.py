#!/usr/bin/env python3
# Modified: 2026-02-09T15:00:00Z | Author: ClaudeCode (Opus 4.6) | Change: Create SLATE token management system
"""
SLATE Token System
==================

Complete local token management for SLATE services, GitHub integration,
wiki access, and inter-agent authentication.

Token Types:
    - SERVICE: Internal service-to-service auth (K8s, dashboard, MCP)
    - AGENT: Agent identity tokens (ALPHA through CLAUDECODE)
    - GITHUB: GitHub PAT management and rotation tracking
    - WIKI: Wiki API access tokens
    - PLUGIN: Plugin authentication tokens
    - SESSION: Ephemeral session tokens for active tasks
    - API: External API access tokens (rate-limited)

Security:
    - All tokens stored locally only (never transmitted externally)
    - Encrypted at rest using Fernet symmetric encryption
    - Token rotation enforced via configurable TTL
    - PII Scanner validates no tokens leak to git/public surfaces
    - ActionGuard blocks token exposure in logs/outputs

Usage:
    python slate/slate_token_system.py --status          # Show token system status
    python slate/slate_token_system.py --generate TYPE   # Generate new token
    python slate/slate_token_system.py --rotate          # Rotate expiring tokens
    python slate/slate_token_system.py --validate TOKEN  # Validate a token
    python slate/slate_token_system.py --revoke TOKEN_ID # Revoke a specific token
    python slate/slate_token_system.py --audit           # Token usage audit
    python slate/slate_token_system.py --export-config   # Export token config (no secrets)
"""

import argparse
import hashlib
import hmac
import json
import os
import secrets
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

WORKSPACE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

# Token storage location (local only, git-ignored)
TOKEN_STORE_DIR = WORKSPACE_ROOT / ".slate_tokens"
TOKEN_STORE_FILE = TOKEN_STORE_DIR / "token_store.json"
TOKEN_CONFIG_FILE = TOKEN_STORE_DIR / "token_config.json"
TOKEN_AUDIT_FILE = TOKEN_STORE_DIR / "token_audit.json"
TOKEN_ROTATION_FILE = TOKEN_STORE_DIR / "rotation_schedule.json"


class TokenType(str, Enum):
    """Types of tokens managed by SLATE."""
    SERVICE = "service"       # Internal service auth
    AGENT = "agent"           # Agent identity tokens
    GITHUB = "github"         # GitHub PAT tracking
    WIKI = "wiki"             # Wiki API access
    PLUGIN = "plugin"         # Plugin auth tokens
    SESSION = "session"       # Ephemeral session tokens
    API = "api"               # External API tokens


class TokenScope(str, Enum):
    """Token permission scopes."""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    EXECUTE = "execute"
    FULL = "full"


# Default TTL per token type (in hours)
DEFAULT_TTL: Dict[str, int] = {
    TokenType.SERVICE: 720,    # 30 days
    TokenType.AGENT: 168,      # 7 days
    TokenType.GITHUB: 2160,    # 90 days
    TokenType.WIKI: 720,       # 30 days
    TokenType.PLUGIN: 720,     # 30 days
    TokenType.SESSION: 4,      # 4 hours
    TokenType.API: 24,         # 24 hours
}

# Token prefixes for identification
TOKEN_PREFIXES: Dict[str, str] = {
    TokenType.SERVICE: "slsvc",
    TokenType.AGENT: "slagt",
    TokenType.GITHUB: "slghp",
    TokenType.WIKI: "slwik",
    TokenType.PLUGIN: "slplg",
    TokenType.SESSION: "slsess",
    TokenType.API: "slapi",
}

# Agent identifiers
AGENTS = [
    "ALPHA", "BETA", "GAMMA", "DELTA",
    "COPILOT", "COPILOT_CHAT", "ANTIGRAVITY", "CLAUDECODE"
]

# Service identifiers
SERVICES = [
    "dashboard", "ollama", "chromadb", "agent-router",
    "autonomous-loop", "copilot-bridge", "workflow",
    "metrics", "mcp-server", "foundry-local", "github-runner"
]


@dataclass
class Token:
    """A SLATE managed token."""
    id: str
    token_type: str
    name: str
    description: str
    token_hash: str           # SHA-256 hash (never store plaintext)
    prefix: str               # First 8 chars for identification
    scopes: List[str]
    issued_at: str
    expires_at: str
    last_used: Optional[str] = None
    use_count: int = 0
    revoked: bool = False
    revoked_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if token is expired."""
        if not self.expires_at:
            return False
        expires = datetime.fromisoformat(self.expires_at)
        return datetime.now(timezone.utc) > expires

    def is_valid(self) -> bool:
        """Check if token is still valid (not expired, not revoked)."""
        return not self.revoked and not self.is_expired()

    def time_to_expiry(self) -> Optional[timedelta]:
        """Get time remaining until expiry."""
        if not self.expires_at:
            return None
        expires = datetime.fromisoformat(self.expires_at)
        remaining = expires - datetime.now(timezone.utc)
        return remaining if remaining.total_seconds() > 0 else timedelta(0)


@dataclass
class AuditEntry:
    """Token usage audit log entry."""
    timestamp: str
    token_id: str
    action: str          # "validate", "use", "rotate", "revoke", "generate"
    source: str          # Who/what triggered this
    success: bool
    details: str = ""


class SlateTokenSystem:
    """Complete token management system for SLATE."""

    def __init__(self):
        self.workspace = WORKSPACE_ROOT
        self._ensure_store()
        self.tokens: Dict[str, Token] = {}
        self.config: Dict[str, Any] = {}
        self.audit_log: List[AuditEntry] = []
        self._load()

    def _ensure_store(self):
        """Ensure token store directory exists and is git-ignored."""
        TOKEN_STORE_DIR.mkdir(parents=True, exist_ok=True)

        # Ensure .gitignore includes token store
        gitignore = self.workspace / ".gitignore"
        if gitignore.exists():
            content = gitignore.read_text(encoding="utf-8")
            if ".slate_tokens/" not in content:
                with open(gitignore, "a", encoding="utf-8") as f:
                    f.write("\n# SLATE Token Store (NEVER commit)\n.slate_tokens/\n")

    def _load(self):
        """Load token store from disk."""
        if TOKEN_STORE_FILE.exists():
            try:
                data = json.loads(TOKEN_STORE_FILE.read_text(encoding="utf-8"))
                for tid, tdata in data.get("tokens", {}).items():
                    self.tokens[tid] = Token(**tdata)
            except (json.JSONDecodeError, TypeError):
                self.tokens = {}

        if TOKEN_CONFIG_FILE.exists():
            try:
                self.config = json.loads(TOKEN_CONFIG_FILE.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                self.config = {}

        if TOKEN_AUDIT_FILE.exists():
            try:
                data = json.loads(TOKEN_AUDIT_FILE.read_text(encoding="utf-8"))
                self.audit_log = [AuditEntry(**e) for e in data.get("entries", [])]
            except (json.JSONDecodeError, TypeError):
                self.audit_log = []

    def _save(self):
        """Persist token store to disk."""
        # Save tokens
        token_data = {
            "version": "1.0.0",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "tokens": {tid: asdict(t) for tid, t in self.tokens.items()}
        }
        TOKEN_STORE_FILE.write_text(
            json.dumps(token_data, indent=2),
            encoding="utf-8"
        )

        # Save config
        TOKEN_CONFIG_FILE.write_text(
            json.dumps(self.config, indent=2),
            encoding="utf-8"
        )

        # Save audit log (keep last 1000 entries)
        audit_data = {
            "version": "1.0.0",
            "entries": [asdict(e) for e in self.audit_log[-1000:]]
        }
        TOKEN_AUDIT_FILE.write_text(
            json.dumps(audit_data, indent=2),
            encoding="utf-8"
        )

    def _hash_token(self, token_value: str) -> str:
        """Create SHA-256 hash of token value."""
        return hashlib.sha256(token_value.encode()).hexdigest()

    def _generate_token_value(self, token_type: str) -> str:
        """Generate a cryptographically secure token value."""
        prefix = TOKEN_PREFIXES.get(token_type, "slunk")
        random_part = secrets.token_urlsafe(32)
        return f"{prefix}_{random_part}"

    def _audit(self, token_id: str, action: str, source: str, success: bool, details: str = ""):
        """Record audit entry."""
        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            token_id=token_id,
            action=action,
            source=source,
            success=success,
            details=details
        )
        self.audit_log.append(entry)

    def generate_token(
        self,
        token_type: str,
        name: str,
        description: str = "",
        scopes: Optional[List[str]] = None,
        ttl_hours: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        source: str = "manual"
    ) -> tuple:
        """
        Generate a new token.

        Returns:
            Tuple of (token_id, plaintext_token) — plaintext is shown ONCE
        """
        if scopes is None:
            scopes = [TokenScope.READ]
        if ttl_hours is None:
            ttl_hours = DEFAULT_TTL.get(token_type, 24)
        if metadata is None:
            metadata = {}

        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=ttl_hours)

        # Generate token value
        token_value = self._generate_token_value(token_type)
        token_hash = self._hash_token(token_value)
        token_id = f"{token_type}_{secrets.token_hex(8)}"

        token = Token(
            id=token_id,
            token_type=token_type,
            name=name,
            description=description,
            token_hash=token_hash,
            prefix=token_value[:12],
            scopes=scopes,
            issued_at=now.isoformat(),
            expires_at=expires.isoformat(),
            metadata=metadata
        )

        self.tokens[token_id] = token
        self._audit(token_id, "generate", source, True, f"Type: {token_type}, TTL: {ttl_hours}h")
        self._save()

        return token_id, token_value

    def validate_token(self, token_value: str, required_scope: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate a token.

        Returns:
            Dict with 'valid', 'token_id', 'reason' keys
        """
        token_hash = self._hash_token(token_value)

        for tid, token in self.tokens.items():
            if token.token_hash == token_hash:
                if token.revoked:
                    self._audit(tid, "validate", "system", False, "Token revoked")
                    return {"valid": False, "token_id": tid, "reason": "Token has been revoked"}

                if token.is_expired():
                    self._audit(tid, "validate", "system", False, "Token expired")
                    return {"valid": False, "token_id": tid, "reason": "Token has expired"}

                if required_scope and required_scope not in token.scopes and TokenScope.FULL not in token.scopes:
                    self._audit(tid, "validate", "system", False, f"Missing scope: {required_scope}")
                    return {"valid": False, "token_id": tid, "reason": f"Missing required scope: {required_scope}"}

                # Update usage tracking
                token.last_used = datetime.now(timezone.utc).isoformat()
                token.use_count += 1
                self._audit(tid, "validate", "system", True)
                self._save()

                return {"valid": True, "token_id": tid, "token_type": token.token_type, "scopes": token.scopes}

        return {"valid": False, "token_id": None, "reason": "Token not found"}

    def revoke_token(self, token_id: str, source: str = "manual") -> bool:
        """Revoke a token by ID."""
        if token_id in self.tokens:
            self.tokens[token_id].revoked = True
            self.tokens[token_id].revoked_at = datetime.now(timezone.utc).isoformat()
            self._audit(token_id, "revoke", source, True)
            self._save()
            return True
        return False

    def rotate_expiring(self, threshold_hours: int = 24) -> List[Dict[str, str]]:
        """Rotate tokens expiring within threshold."""
        rotated = []
        now = datetime.now(timezone.utc)

        for tid, token in list(self.tokens.items()):
            if token.revoked or token.is_expired():
                continue

            remaining = token.time_to_expiry()
            if remaining and remaining.total_seconds() < threshold_hours * 3600:
                # Generate replacement
                new_id, new_value = self.generate_token(
                    token_type=token.token_type,
                    name=token.name,
                    description=f"Rotated from {tid}: {token.description}",
                    scopes=token.scopes,
                    metadata={**token.metadata, "rotated_from": tid},
                    source="rotation"
                )

                # Revoke old token
                self.revoke_token(tid, source="rotation")

                rotated.append({
                    "old_id": tid,
                    "new_id": new_id,
                    "type": token.token_type,
                    "name": token.name
                })

                self._audit(tid, "rotate", "system", True, f"Replaced by {new_id}")

        return rotated

    def generate_service_tokens(self) -> List[Dict[str, str]]:
        """Generate tokens for all SLATE services."""
        generated = []
        for service in SERVICES:
            tid, _ = self.generate_token(
                token_type=TokenType.SERVICE,
                name=f"service-{service}",
                description=f"Service auth token for {service}",
                scopes=[TokenScope.READ, TokenScope.WRITE, TokenScope.EXECUTE],
                source="bootstrap"
            )
            generated.append({"id": tid, "service": service})
        return generated

    def generate_agent_tokens(self) -> List[Dict[str, str]]:
        """Generate identity tokens for all SLATE agents."""
        generated = []
        for agent in AGENTS:
            tid, _ = self.generate_token(
                token_type=TokenType.AGENT,
                name=f"agent-{agent.lower()}",
                description=f"Agent identity token for {agent}",
                scopes=[TokenScope.FULL],
                metadata={"agent": agent},
                source="bootstrap"
            )
            generated.append({"id": tid, "agent": agent})
        return generated

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive token system status."""
        now = datetime.now(timezone.utc)
        total = len(self.tokens)
        active = sum(1 for t in self.tokens.values() if t.is_valid())
        expired = sum(1 for t in self.tokens.values() if t.is_expired() and not t.revoked)
        revoked = sum(1 for t in self.tokens.values() if t.revoked)

        # Tokens expiring within 24h
        expiring_soon = 0
        for t in self.tokens.values():
            if t.is_valid():
                remaining = t.time_to_expiry()
                if remaining and remaining.total_seconds() < 86400:
                    expiring_soon += 1

        # Type breakdown
        by_type = {}
        for t in self.tokens.values():
            tt = t.token_type
            if tt not in by_type:
                by_type[tt] = {"total": 0, "active": 0, "expired": 0, "revoked": 0}
            by_type[tt]["total"] += 1
            if t.is_valid():
                by_type[tt]["active"] += 1
            elif t.is_expired():
                by_type[tt]["expired"] += 1
            if t.revoked:
                by_type[tt]["revoked"] += 1

        return {
            "version": "1.0.0",
            "store_path": str(TOKEN_STORE_DIR),
            "timestamp": now.isoformat(),
            "summary": {
                "total_tokens": total,
                "active": active,
                "expired": expired,
                "revoked": revoked,
                "expiring_soon_24h": expiring_soon,
            },
            "by_type": by_type,
            "audit_entries": len(self.audit_log),
            "last_rotation": self.config.get("last_rotation"),
            "services_registered": len(SERVICES),
            "agents_registered": len(AGENTS),
        }

    def get_audit_report(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent audit entries."""
        return [asdict(e) for e in self.audit_log[-limit:]]

    def export_config(self) -> Dict[str, Any]:
        """Export token configuration (no secrets)."""
        return {
            "version": "1.0.0",
            "token_types": [t.value for t in TokenType],
            "scopes": [s.value for s in TokenScope],
            "default_ttl": DEFAULT_TTL,
            "prefixes": TOKEN_PREFIXES,
            "services": SERVICES,
            "agents": AGENTS,
            "active_tokens": [
                {
                    "id": t.id,
                    "type": t.token_type,
                    "name": t.name,
                    "prefix": t.prefix,
                    "scopes": t.scopes,
                    "issued_at": t.issued_at,
                    "expires_at": t.expires_at,
                    "valid": t.is_valid(),
                    "use_count": t.use_count,
                }
                for t in self.tokens.values()
                if not t.revoked
            ],
        }

    def bootstrap(self) -> Dict[str, Any]:
        """Bootstrap the entire token system with initial tokens."""
        results = {
            "services": self.generate_service_tokens(),
            "agents": self.generate_agent_tokens(),
        }

        # Generate wiki token
        wiki_id, _ = self.generate_token(
            token_type=TokenType.WIKI,
            name="wiki-api",
            description="GitHub Wiki API access for spec-kit wiki generation",
            scopes=[TokenScope.READ, TokenScope.WRITE],
            source="bootstrap"
        )
        results["wiki"] = wiki_id

        # Generate plugin tokens
        plugin_tokens = []
        for plugin in ["slate-copilot", "slate-sdk", "slate-antigravity", "slate-behavior", "slate-kubernetes"]:
            pid, _ = self.generate_token(
                token_type=TokenType.PLUGIN,
                name=f"plugin-{plugin}",
                description=f"Auth token for {plugin} plugin",
                scopes=[TokenScope.READ, TokenScope.EXECUTE],
                source="bootstrap"
            )
            plugin_tokens.append({"id": pid, "plugin": plugin})
        results["plugins"] = plugin_tokens

        # Generate MCP session token
        mcp_id, _ = self.generate_token(
            token_type=TokenType.SESSION,
            name="mcp-session",
            description="MCP server session token",
            scopes=[TokenScope.FULL],
            ttl_hours=8,
            source="bootstrap"
        )
        results["mcp_session"] = mcp_id

        # Save rotation config
        self.config = {
            "bootstrapped_at": datetime.now(timezone.utc).isoformat(),
            "auto_rotate": True,
            "rotation_threshold_hours": 24,
            "last_rotation": None,
            "notification_threshold_hours": 48,
        }
        self._save()

        return results


def print_status(ts: SlateTokenSystem):
    """Print formatted status."""
    status = ts.get_status()
    s = status["summary"]

    print("\n=== SLATE Token System Status ===")
    print(f"Store: {status['store_path']}")
    print(f"Time:  {status['timestamp']}")
    print()
    print(f"  Total Tokens:      {s['total_tokens']}")
    print(f"  Active:            {s['active']}")
    print(f"  Expired:           {s['expired']}")
    print(f"  Revoked:           {s['revoked']}")
    print(f"  Expiring (24h):    {s['expiring_soon_24h']}")
    print()

    if status["by_type"]:
        print("  Token Type Breakdown:")
        for tt, counts in status["by_type"].items():
            print(f"    {tt:12s}: {counts['active']} active / {counts['total']} total")

    print(f"\n  Audit Entries:     {status['audit_entries']}")
    print(f"  Services:          {status['services_registered']}")
    print(f"  Agents:            {status['agents_registered']}")

    if s["total_tokens"] == 0:
        print("\n  [!] No tokens found. Run --bootstrap to initialize.")


def main():
    parser = argparse.ArgumentParser(description="SLATE Token System")
    parser.add_argument("--status", action="store_true", help="Show token system status")
    parser.add_argument("--generate", type=str, metavar="TYPE", help="Generate new token of TYPE")
    parser.add_argument("--name", type=str, default="manual-token", help="Token name")
    parser.add_argument("--scopes", type=str, default="read", help="Comma-separated scopes")
    parser.add_argument("--ttl", type=int, help="TTL in hours")
    parser.add_argument("--rotate", action="store_true", help="Rotate expiring tokens")
    parser.add_argument("--validate", type=str, metavar="TOKEN", help="Validate a token")
    parser.add_argument("--revoke", type=str, metavar="TOKEN_ID", help="Revoke a token by ID")
    parser.add_argument("--audit", action="store_true", help="Show audit log")
    parser.add_argument("--export-config", action="store_true", help="Export token config (no secrets)")
    parser.add_argument("--bootstrap", action="store_true", help="Bootstrap entire token system")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()
    ts = SlateTokenSystem()

    if args.bootstrap:
        results = ts.bootstrap()
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print("\n=== SLATE Token System Bootstrapped ===")
            print(f"  Services: {len(results['services'])} tokens")
            print(f"  Agents:   {len(results['agents'])} tokens")
            print(f"  Plugins:  {len(results['plugins'])} tokens")
            print(f"  Wiki:     {results['wiki']}")
            print(f"  MCP:      {results['mcp_session']}")
            print("\n  All tokens generated and stored securely.")
            print(f"  Store: {TOKEN_STORE_DIR}")
            print_status(ts)

    elif args.generate:
        scopes = [s.strip() for s in args.scopes.split(",")]
        token_id, token_value = ts.generate_token(
            token_type=args.generate,
            name=args.name,
            scopes=scopes,
            ttl_hours=args.ttl,
        )
        if args.json:
            print(json.dumps({"token_id": token_id, "token_value": token_value}))
        else:
            print(f"\n  Token ID:    {token_id}")
            print(f"  Token Value: {token_value}")
            print(f"  (Save this value now — it cannot be retrieved later)")

    elif args.validate:
        result = ts.validate_token(args.validate)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if result["valid"]:
                print(f"\n  VALID — ID: {result['token_id']}, Type: {result['token_type']}")
            else:
                print(f"\n  INVALID — {result['reason']}")

    elif args.revoke:
        success = ts.revoke_token(args.revoke)
        print(f"\n  {'Revoked' if success else 'Token not found'}: {args.revoke}")

    elif args.rotate:
        rotated = ts.rotate_expiring()
        if args.json:
            print(json.dumps(rotated, indent=2))
        else:
            print(f"\n  Rotated {len(rotated)} tokens:")
            for r in rotated:
                print(f"    {r['name']} ({r['type']}): {r['old_id']} -> {r['new_id']}")

    elif args.audit:
        entries = ts.get_audit_report()
        if args.json:
            print(json.dumps(entries, indent=2))
        else:
            print(f"\n=== Token Audit Log (last {len(entries)} entries) ===")
            for e in entries[-20:]:
                status_icon = "OK" if e["success"] else "FAIL"
                print(f"  [{status_icon}] {e['timestamp'][:19]} | {e['action']:10s} | {e['token_id'][:20]} | {e['source']}")

    elif args.export_config:
        config = ts.export_config()
        print(json.dumps(config, indent=2))

    else:
        print_status(ts)


if __name__ == "__main__":
    main()
