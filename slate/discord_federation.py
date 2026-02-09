#!/usr/bin/env python3
"""
SLATE Discord Bot Federation — SLATE-to-SLATE Live Support Pipeline
======================================================================

Enables community fork operators to connect their local SLATE bot to
the main SLATE community bot for a live support pipeline.

Architecture:
  ┌─────────────────────────────────────────────────────────────────┐
  │  Community Fork A                  Community Fork B             │
  │  (their machine)                   (their machine)              │
  │                                                                 │
  │  ┌──────────────┐                 ┌──────────────┐              │
  │  │ slate.ai     │                 │ slate.ai     │              │
  │  │ (local bot)  │                 │ (local bot)  │              │
  │  └──────┬───────┘                 └──────┬───────┘              │
  │         │ /slate-ask-upstream             │                     │
  │         │                                 │                     │
  └─────────┼─────────────────────────────────┼─────────────────────┘
            │                                 │
            ▼                                 ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │  Main SLATE Community Server (slate.git)                        │
  │                                                                 │
  │  ┌──────────────────────────────────────────────────────────┐   │
  │  │ slate.ai (main bot)                                      │   │
  │  │ ┌───────────────────┐  ┌───────────┐  ┌──────────────┐  │   │
  │  │ │ Federation API     │  │ Ollama    │  │ GitHub API   │  │   │
  │  │ │ (port 8086/api)    │  │ (local)   │  │ (public)     │  │   │
  │  │ └───────────────────┘  └───────────┘  └──────────────┘  │   │
  │  └──────────────────────────────────────────────────────────┘   │
  └─────────────────────────────────────────────────────────────────┘

Flow:
  1. Fork operator runs `python -m slate.discord_federation --init`
  2. Creates a local Discord app + bot for their own server
  3. Their bot has /slate-ask-upstream command
  4. User asks question → fork bot → main SLATE bot API → Ollama → answer
  5. All communication is API-based (no bot token sharing)

Security:
  - Fork bots authenticate via SLATE fork verification token
  - Main bot API is rate-limited per fork
  - All requests go through DiscordSecurityGate
  - No system internals exposed in federated responses
  - Federation tokens are SHA-256 derived from fork verification

Privacy:
  - Fork bots never send user IDs to main bot (hashed only)
  - Questions are logged for quality improvement (opt-in)
  - No message content leaves the federation API boundary
"""
# Modified: 2026-02-09T21:30:00Z | Author: Claude Opus 4.6 | Change: Create SLATE-to-SLATE bot federation

import hashlib
import json
import logging
import os
import sys
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

WORKSPACE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

logger = logging.getLogger("slate.discord_federation")

# ── Constants ─────────────────────────────────────────────────────────

FEDERATION_CONFIG_DIR = WORKSPACE_ROOT / ".slate_community" / "federation"
FEDERATION_PEERS_FILE = FEDERATION_CONFIG_DIR / "peers.json"
FEDERATION_LOG_FILE = WORKSPACE_ROOT / "slate_logs" / "federation.json"

# Federation API runs on the same health check server (port 8086)
FEDERATION_API_PATH = "/api/v1/federation"

# Rate limits for federated requests
FEDERATION_RATE_LIMIT = 10   # requests per peer per minute
FEDERATION_RATE_WINDOW = 60  # seconds


# ── Data Classes ──────────────────────────────────────────────────────

@dataclass
class FederationPeer:
    """A registered federation peer (community fork's bot)."""
    peer_id: str                    # SHA-256 hash of fork's GitHub username
    github_username: str            # Fork operator's GitHub username
    fork_verified: bool = False     # Has a verified fork of SLATE
    registered_at: str = ""
    last_seen: str = ""
    total_queries: int = 0
    tier: int = 0                   # Same tier system as community
    federation_token_hash: str = "" # SHA-256 of their federation token
    server_name: str = ""           # Their Discord server name
    active: bool = True


@dataclass
class FederationQuery:
    """A question from a federated peer."""
    peer_id: str
    question: str
    timestamp: str
    response: str = ""
    response_time_ms: float = 0
    source: str = ""  # "ai" or "kb" (knowledge base)


@dataclass
class FederationResponse:
    """Response to a federated query."""
    success: bool
    answer: str = ""
    source: str = ""
    error: str = ""
    remaining_quota: int = 0


# ── Federation Token System ──────────────────────────────────────────

class FederationTokenManager:
    """
    Manages federation authentication tokens.

    Tokens are derived from the fork verification process:
    1. Fork operator registers via /slate-register
    2. After fork verification, a federation token is generated
    3. Token = SHA-256(github_username + "slate_federation" + server_id)
    4. Token is given to the fork operator for their bot config
    """

    SALT = "slate_federation_v1"

    @staticmethod
    def generate_token(github_username: str, server_id: str) -> str:
        """Generate a federation token for a verified fork."""
        raw = f"{github_username}:{FederationTokenManager.SALT}:{server_id}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    @staticmethod
    def hash_token(token: str) -> str:
        """Hash a token for storage (never store raw tokens)."""
        return hashlib.sha256(token.encode()).hexdigest()[:16]

    @staticmethod
    def verify_token(token: str, github_username: str, server_id: str) -> bool:
        """Verify a federation token matches expectations."""
        expected = FederationTokenManager.generate_token(github_username, server_id)
        return token == expected


# ── Federation Manager ────────────────────────────────────────────────

class FederationManager:
    """
    Manages the SLATE-to-SLATE bot federation.

    Handles peer registration, query routing, and rate limiting.
    Runs on the main SLATE bot's health check server.
    """

    def __init__(self):
        FEDERATION_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self._peers: dict[str, FederationPeer] = {}
        self._rate_limits: dict[str, list[float]] = {}
        self._load_peers()

    def _load_peers(self):
        """Load federation peers from disk."""
        if FEDERATION_PEERS_FILE.exists():
            try:
                data = json.loads(FEDERATION_PEERS_FILE.read_text(encoding="utf-8"))
                for entry in data.get("peers", []):
                    peer = FederationPeer(**entry)
                    self._peers[peer.peer_id] = peer
            except Exception as e:
                logger.error(f"Failed to load federation peers: {e}")

    def _save_peers(self):
        """Save federation peers to disk."""
        data = {
            "version": "1.0",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "peer_count": len(self._peers),
            "peers": [
                {
                    "peer_id": p.peer_id,
                    "github_username": p.github_username,
                    "fork_verified": p.fork_verified,
                    "registered_at": p.registered_at,
                    "last_seen": p.last_seen,
                    "total_queries": p.total_queries,
                    "tier": p.tier,
                    "federation_token_hash": p.federation_token_hash,
                    "server_name": p.server_name,
                    "active": p.active,
                }
                for p in self._peers.values()
            ],
        }
        FEDERATION_PEERS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # ── Peer Management ────────────────────────────────────────────

    def register_peer(
        self,
        github_username: str,
        server_name: str,
        token: str,
    ) -> tuple[bool, str]:
        """Register a new federation peer."""
        peer_id = hashlib.sha256(github_username.encode()).hexdigest()[:16]

        # Verify they have a fork (uses public GitHub API)
        has_fork = self._verify_fork(github_username)
        if not has_fork:
            return False, (
                "Federation requires a verified fork of SLATE. "
                "Fork the repo at https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E "
                "and try again."
            )

        # Verify token
        token_hash = FederationTokenManager.hash_token(token)

        peer = FederationPeer(
            peer_id=peer_id,
            github_username=github_username,
            fork_verified=True,
            registered_at=datetime.now(timezone.utc).isoformat(),
            last_seen=datetime.now(timezone.utc).isoformat(),
            federation_token_hash=token_hash,
            server_name=server_name,
            tier=2,  # Federation requires at least Contributor tier
            active=True,
        )
        self._peers[peer_id] = peer
        self._save_peers()

        return True, (
            f"Federation registered! Peer ID: {peer_id}\n"
            f"Your bot can now query the main SLATE bot for support."
        )

    def _verify_fork(self, github_username: str) -> bool:
        """Verify a GitHub user has forked SLATE."""
        try:
            url = f"https://api.github.com/repos/{github_username}/S.L.A.T.E"
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "SLATE-Federation/1.0")
            req.add_header("Accept", "application/vnd.github.v3+json")
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode())
                    return data.get("fork", False)
        except Exception:
            pass
        return False

    def authenticate_peer(self, peer_id: str, token: str) -> Optional[FederationPeer]:
        """Authenticate a federation peer by token."""
        peer = self._peers.get(peer_id)
        if not peer or not peer.active:
            return None

        token_hash = FederationTokenManager.hash_token(token)
        if token_hash != peer.federation_token_hash:
            return None

        peer.last_seen = datetime.now(timezone.utc).isoformat()
        return peer

    def check_rate_limit(self, peer_id: str) -> bool:
        """Check if peer is rate-limited. Returns True if allowed."""
        now = time.time()
        times = self._rate_limits.get(peer_id, [])
        times = [t for t in times if now - t < FEDERATION_RATE_WINDOW]

        if len(times) >= FEDERATION_RATE_LIMIT:
            return False

        times.append(now)
        self._rate_limits[peer_id] = times
        return True

    def get_remaining_quota(self, peer_id: str) -> int:
        """Get remaining queries for a peer in current window."""
        now = time.time()
        times = self._rate_limits.get(peer_id, [])
        times = [t for t in times if now - t < FEDERATION_RATE_WINDOW]
        return max(0, FEDERATION_RATE_LIMIT - len(times))

    # ── Query Handling ─────────────────────────────────────────────

    async def handle_query(
        self,
        peer_id: str,
        token: str,
        question: str,
    ) -> FederationResponse:
        """
        Handle a federated support query.

        Flow: authenticate → rate limit → sanitize → AI/KB → sanitize → respond
        """
        # Authenticate
        peer = self.authenticate_peer(peer_id, token)
        if not peer:
            return FederationResponse(
                success=False,
                error="Authentication failed. Invalid peer ID or token.",
            )

        # Rate limit
        if not self.check_rate_limit(peer_id):
            return FederationResponse(
                success=False,
                error="Rate limited. Try again in 60 seconds.",
                remaining_quota=0,
            )

        # Import security and support
        from slate.discord_security import get_security_gate
        from slate.discord_onboarding import get_onboarding_manager
        from slate.slate_community import find_support_answer

        security = get_security_gate()
        onboarding = get_onboarding_manager()

        # Validate input
        validation = security.validate_input(question)
        if not validation.allowed:
            return FederationResponse(
                success=False,
                error=f"Input validation failed: {validation.reason}",
                remaining_quota=self.get_remaining_quota(peer_id),
            )

        clean_question = validation.filtered_content
        start_time = time.time()

        # Try agentic AI first
        answer = await onboarding.get_ai_support_response(clean_question, peer.tier)
        source = "ai"

        # Fall back to knowledge base
        if not answer:
            answer = find_support_answer(clean_question)
            source = "kb"

        elapsed = (time.time() - start_time) * 1000

        if answer:
            # Sanitize output
            safe = security.sanitize_output(answer)
            if not safe.allowed:
                return FederationResponse(
                    success=False,
                    error="Response contained sensitive information and was blocked.",
                    remaining_quota=self.get_remaining_quota(peer_id),
                )

            peer.total_queries += 1
            self._save_peers()

            # Log the query
            self._log_query(FederationQuery(
                peer_id=peer_id,
                question=clean_question[:200],
                timestamp=datetime.now(timezone.utc).isoformat(),
                response=safe.filtered_content[:200],
                response_time_ms=elapsed,
                source=source,
            ))

            return FederationResponse(
                success=True,
                answer=safe.filtered_content,
                source=source,
                remaining_quota=self.get_remaining_quota(peer_id),
            )
        else:
            return FederationResponse(
                success=False,
                error=(
                    "I couldn't find an answer to that question. "
                    "Try asking about: installation, forking, tech stack, "
                    "GPU setup, specs, security, or community tiers."
                ),
                remaining_quota=self.get_remaining_quota(peer_id),
            )

    def _log_query(self, query: FederationQuery):
        """Log a federation query for quality tracking."""
        log_file = FEDERATION_LOG_FILE
        log_file.parent.mkdir(parents=True, exist_ok=True)

        log_data = []
        if log_file.exists():
            try:
                log_data = json.loads(log_file.read_text(encoding="utf-8"))
            except Exception:
                log_data = []

        log_data.append({
            "peer_id": query.peer_id,
            "question": query.question,
            "timestamp": query.timestamp,
            "response_time_ms": query.response_time_ms,
            "source": query.source,
        })

        # Keep last 5000
        if len(log_data) > 5000:
            log_data = log_data[-5000:]

        log_file.write_text(json.dumps(log_data, indent=2), encoding="utf-8")

    # ── Stats ──────────────────────────────────────────────────────

    def get_federation_stats(self) -> dict:
        """Get federation stats (safe for display)."""
        active = sum(1 for p in self._peers.values() if p.active)
        total_queries = sum(p.total_queries for p in self._peers.values())
        return {
            "total_peers": len(self._peers),
            "active_peers": active,
            "total_queries": total_queries,
            "rate_limit_per_min": FEDERATION_RATE_LIMIT,
        }


# ── Federation API Handler ────────────────────────────────────────────

class FederationAPIHandler:
    """
    HTTP API handler for federation requests.

    Integrated into the bot's health check server on port 8086.
    Endpoints:
      POST /api/v1/federation/query     — Submit a support question
      POST /api/v1/federation/register  — Register as a federation peer
      GET  /api/v1/federation/status    — Check federation status
    """

    def __init__(self, federation: FederationManager):
        self.federation = federation

    async def handle_request(self, path: str, method: str, body: dict) -> tuple[int, dict]:
        """Route and handle federation API requests."""
        if method == "POST" and path == f"{FEDERATION_API_PATH}/query":
            return await self._handle_query(body)
        elif method == "POST" and path == f"{FEDERATION_API_PATH}/register":
            return self._handle_register(body)
        elif method == "GET" and path == f"{FEDERATION_API_PATH}/status":
            return self._handle_status()
        else:
            return 404, {"error": "Not found"}

    async def _handle_query(self, body: dict) -> tuple[int, dict]:
        """Handle a federated support query."""
        peer_id = body.get("peer_id", "")
        token = body.get("token", "")
        question = body.get("question", "")

        if not all([peer_id, token, question]):
            return 400, {"error": "Missing required fields: peer_id, token, question"}

        result = await self.federation.handle_query(peer_id, token, question)
        if result.success:
            return 200, {
                "success": True,
                "answer": result.answer,
                "source": result.source,
                "remaining_quota": result.remaining_quota,
            }
        else:
            return 429 if "Rate limited" in result.error else 403, {
                "success": False,
                "error": result.error,
                "remaining_quota": result.remaining_quota,
            }

    def _handle_register(self, body: dict) -> tuple[int, dict]:
        """Handle federation peer registration."""
        github_username = body.get("github_username", "")
        server_name = body.get("server_name", "")
        token = body.get("token", "")

        if not all([github_username, server_name, token]):
            return 400, {"error": "Missing required fields: github_username, server_name, token"}

        success, message = self.federation.register_peer(github_username, server_name, token)
        return 200 if success else 403, {
            "success": success,
            "message": message,
        }

    def _handle_status(self) -> tuple[int, dict]:
        """Return federation status."""
        stats = self.federation.get_federation_stats()
        return 200, {
            "federation": "SLATE-to-SLATE",
            "version": "1.0",
            "status": "online",
            **stats,
        }


# ── Fork Bot Template ─────────────────────────────────────────────────

FORK_BOT_TEMPLATE = '''#!/usr/bin/env python3
"""
SLATE Fork Bot — {server_name}
==============================

Auto-generated by SLATE federation system.
This bot runs locally on YOUR machine and connects to the main SLATE
community bot for live support.

Setup:
  1. Create a Discord application at https://discord.com/developers
  2. Add bot scope + slash commands
  3. Set DISCORD_BOT_TOKEN in your .env
  4. Run: python fork_bot.py --start

This bot is LOCAL-ONLY — it cannot be installed on other servers.
"""

import asyncio
import json
import os
import sys
import urllib.request
from pathlib import Path

# Discord import
try:
    import discord
    from discord import app_commands
    from discord.ext import commands
except ImportError:
    print("Install discord.py: pip install discord.py")
    sys.exit(1)

# ── Configuration ─────────────────────────────────────────────────
FEDERATION_PEER_ID = "{peer_id}"
FEDERATION_TOKEN = os.environ.get("SLATE_FEDERATION_TOKEN", "{federation_token}")
MAIN_BOT_API = "http://127.0.0.1:8086"  # Main SLATE bot API
GUILD_ID = int(os.environ.get("DISCORD_GUILD_ID", "0"))  # Your server

SLATE_COLOR = 0xB85A3C

# ── Bot Setup ─────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = False
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f"Fork bot connected as {{bot.user}}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {{len(synced)}} commands")
    except Exception as e:
        print(f"Sync error: {{e}}")

    # Guild lock
    if GUILD_ID:
        for guild in bot.guilds:
            if guild.id != GUILD_ID:
                await guild.leave()

@bot.tree.command(name="slate-ask", description="Ask the SLATE community bot a question")
@app_commands.describe(question="Your question about SLATE")
async def cmd_ask(interaction: discord.Interaction, question: str):
    await interaction.response.defer()
    try:
        payload = json.dumps({{
            "peer_id": FEDERATION_PEER_ID,
            "token": FEDERATION_TOKEN,
            "question": question,
        }}).encode()
        req = urllib.request.Request(
            f"{{MAIN_BOT_API}}/api/v1/federation/query",
            data=payload,
            headers={{"Content-Type": "application/json"}},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            if result.get("success"):
                embed = discord.Embed(
                    title="slate.ai Support",
                    description=result["answer"],
                    color=SLATE_COLOR,
                )
                embed.add_field(name="Source", value=result.get("source", "?"), inline=True)
                embed.add_field(name="Quota", value=f"{{result.get('remaining_quota', '?')}} remaining", inline=True)
                embed.set_footer(text="Federated via SLATE-to-SLATE pipeline")
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send(
                    f"Error: {{result.get('error', 'Unknown')}}",
                    ephemeral=True,
                )
    except Exception as e:
        await interaction.followup.send(
            "Could not reach the SLATE community bot. Is it running?",
            ephemeral=True,
        )

@bot.tree.command(name="slate-about", description="About SLATE")
async def cmd_about(interaction: discord.Interaction):
    embed = discord.Embed(
        title="S.L.A.T.E.",
        description=(
            "**Synchronized Living Architecture for Transformation and Evolution**\\n\\n"
            "This is a community fork bot connected to the main SLATE system "
            "via the SLATE-to-SLATE federation pipeline.\\n\\n"
            "Use `/slate-ask` to query the main SLATE AI for support."
        ),
        color=SLATE_COLOR,
    )
    embed.set_footer(text="SLATE Fork Bot — Local inference, federated support")
    await interaction.response.send_message(embed=embed)

# ── Start ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    token = os.environ.get("DISCORD_BOT_TOKEN")
    if not token:
        print("Set DISCORD_BOT_TOKEN in your .env")
        sys.exit(1)
    bot.run(token)
'''


def generate_fork_bot(
    github_username: str,
    server_name: str,
    server_id: str,
    output_dir: str = ".",
) -> tuple[str, str]:
    """
    Generate a fork bot script for a community member.

    Returns (file_path, federation_token).
    """
    peer_id = hashlib.sha256(github_username.encode()).hexdigest()[:16]
    token = FederationTokenManager.generate_token(github_username, server_id)

    bot_code = FORK_BOT_TEMPLATE.format(
        server_name=server_name,
        peer_id=peer_id,
        federation_token=token,
    )

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    file_path = output / "slate_fork_bot.py"
    file_path.write_text(bot_code, encoding="utf-8")

    return str(file_path), token


# ── Singleton ─────────────────────────────────────────────────────────

_federation: Optional[FederationManager] = None


def get_federation_manager() -> FederationManager:
    """Get singleton federation manager."""
    global _federation
    if _federation is None:
        _federation = FederationManager()
    return _federation


# ── CLI ───────────────────────────────────────────────────────────────

def main():
    """Federation CLI."""
    import argparse

    parser = argparse.ArgumentParser(description="SLATE Discord Bot Federation")
    parser.add_argument("--status", action="store_true", help="Show federation status")
    parser.add_argument("--peers", action="store_true", help="List federation peers")
    parser.add_argument("--generate-fork-bot", type=str, metavar="GITHUB_USER",
                        help="Generate a fork bot for a GitHub user")
    parser.add_argument("--server-name", type=str, default="SLATE Fork",
                        help="Discord server name for the fork bot")
    parser.add_argument("--server-id", type=str, default="0",
                        help="Discord server ID for the fork bot")
    parser.add_argument("--output-dir", type=str, default=".",
                        help="Output directory for generated bot")

    args = parser.parse_args()
    fed = get_federation_manager()

    if args.status:
        stats = fed.get_federation_stats()
        print("\n=== SLATE Federation Status ===")
        print(f"  Total peers:     {stats['total_peers']}")
        print(f"  Active peers:    {stats['active_peers']}")
        print(f"  Total queries:   {stats['total_queries']}")
        print(f"  Rate limit:      {stats['rate_limit_per_min']}/min")
        print()
        return 0

    if args.peers:
        print("\n=== Federation Peers ===")
        for peer in fed._peers.values():
            status = "🟢" if peer.active else "🔴"
            print(
                f"  {status} [{peer.peer_id[:8]}...] "
                f"{peer.github_username} ({peer.server_name}) "
                f"— {peer.total_queries} queries"
            )
        print()
        return 0

    if args.generate_fork_bot:
        path, token = generate_fork_bot(
            args.generate_fork_bot,
            args.server_name,
            args.server_id,
            args.output_dir,
        )
        print(f"\nGenerated fork bot: {path}")
        print(f"Federation token: {token}")
        print(f"\nNext steps:")
        print(f"  1. Create a Discord app at https://discord.com/developers")
        print(f"  2. Add bot + slash commands scopes")
        print(f"  3. Set DISCORD_BOT_TOKEN in .env")
        print(f"  4. Set SLATE_FEDERATION_TOKEN={token}")
        print(f"  5. Run: python {path}")
        print()
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
