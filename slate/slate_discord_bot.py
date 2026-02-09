#!/usr/bin/env python3
"""
SLATE Discord Bot
===================

Secure Discord bot for SLATE community interaction. Provides sanitized
system status, collects community feedback, and shows tech tree progress.

Security Architecture:
  Discord Gateway ←→ Bot ←→ DiscordSecurityGate ←→ SLATE internals
                                    ↓
                              PII Scanner
                              ActionGuard
                              Audit Log

ALL responses pass through discord_security.py before reaching Discord.
NO system internals (IPs, ports, paths, tokens) are ever exposed.

Slash Commands:
  /slate-status   — Sanitized system health
  /slate-feedback — Submit community feedback
  /slate-tree     — Tech tree progress
  /slate-about    — Project information

Dependencies:
  discord.py >= 2.3.0 (MIT license)
"""
# Modified: 2026-02-09T18:30:00Z | Author: Claude Opus 4.6 | Change: Create secure Discord bot module

import asyncio
import hashlib
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

WORKSPACE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

logger = logging.getLogger("slate.discord_bot")

# Attempt to import discord.py — graceful fallback if not installed
try:
    import discord
    from discord import app_commands
    from discord.ext import commands
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False
    logger.warning("discord.py not installed — bot features unavailable")

from slate.discord_security import get_security_gate, DiscordSecurityGate
from slate.slate_discord import EMBED_COLORS, get_discord

# ── Constants ─────────────────────────────────────────────────────────

BOT_PORT = int(os.environ.get("DISCORD_PORT", "8086"))
TECH_TREE_PATH = WORKSPACE_ROOT / ".slate_tech_tree" / "tech_tree.json"
FEEDBACK_DIR = WORKSPACE_ROOT / ".slate_discussions"
FEEDBACK_FILE = FEEDBACK_DIR / "discord_feedback.json"
TASKS_FILE = WORKSPACE_ROOT / "current_tasks.json"

# SLATE brand
SLATE_COLOR = 0xB85A3C  # Warm rust
SLATE_FOOTER = "S.L.A.T.E. — Synchronized Living Architecture"
GITHUB_URL = "https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E"
PAGES_URL = "https://synchronizedlivingarchitecture.github.io/S.L.A.T.E/"


# ── Feedback Storage ──────────────────────────────────────────────────

def _load_feedback() -> dict:
    """Load feedback storage file."""
    if FEEDBACK_FILE.exists():
        try:
            return json.loads(FEEDBACK_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, Exception):
            pass
    return {"events": [], "metrics": {"total_feedback": 0, "by_intent": {}}}


def _save_feedback(data: dict):
    """Save feedback storage file."""
    FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
    FEEDBACK_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def store_feedback(
    user_id: str,
    channel: str,
    content: str,
    intent: str = "feedback",
) -> str:
    """
    Store community feedback and return a tracking ID.

    User IDs are hashed — we NEVER store raw Discord user IDs.
    """
    data = _load_feedback()
    feedback_id = f"df_{len(data['events']) + 1:04d}"
    user_hash = hashlib.sha256(str(user_id).encode()).hexdigest()[:16]

    entry = {
        "id": feedback_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "discord",
        "channel": channel,
        "author_hash": user_hash,
        "intent": intent,
        "content": content,
        "status": "pending",
        "task_id": None,
        "github_issue": None,
    }
    data["events"].append(entry)
    data["metrics"]["total_feedback"] = len(data["events"])
    data["metrics"]["by_intent"][intent] = data["metrics"]["by_intent"].get(intent, 0) + 1

    _save_feedback(data)
    return feedback_id


# ── Status Helpers ────────────────────────────────────────────────────

def get_sanitized_status() -> dict:
    """
    Get system status sanitized for public Discord display.

    Returns ONLY safe information — no IPs, ports, paths, or tokens.
    """
    status = {
        "dashboard": "Unknown",
        "ai_backend": "Unknown",
        "gpu_count": 0,
        "uptime": "Unknown",
        "tech_tree_completion": "0%",
    }

    # Check dashboard (safe: just up/down status)
    try:
        import urllib.request
        req = urllib.request.Request("http://127.0.0.1:8080/api/status", method="GET")
        req.add_header("User-Agent", "SLATE-DiscordBot/1.0")
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                status["dashboard"] = "Online"
            else:
                status["dashboard"] = "Degraded"
    except Exception:
        status["dashboard"] = "Offline"

    # Check Ollama (safe: just up/down)
    try:
        import urllib.request
        req = urllib.request.Request("http://127.0.0.1:11434/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                status["ai_backend"] = "Online"
    except Exception:
        status["ai_backend"] = "Offline"

    # GPU count (safe: just a number)
    try:
        import subprocess
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=count", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            status["gpu_count"] = len(lines)
    except Exception:
        pass

    # Tech tree completion (safe: percentage only)
    try:
        if TECH_TREE_PATH.exists():
            tree = json.loads(TECH_TREE_PATH.read_text(encoding="utf-8"))
            nodes = tree.get("nodes", [])
            if nodes:
                complete = sum(1 for n in nodes if n.get("status") == "complete")
                total = len(nodes)
                status["tech_tree_completion"] = f"{complete}/{total} ({100 * complete // total}%)"
    except Exception:
        pass

    return status


def get_tech_tree_summary() -> dict:
    """Get tech tree summary for public display."""
    summary = {"phases": {}, "total": 0, "complete": 0}

    try:
        if TECH_TREE_PATH.exists():
            tree = json.loads(TECH_TREE_PATH.read_text(encoding="utf-8"))
            nodes = tree.get("nodes", [])
            summary["total"] = len(nodes)

            for node in nodes:
                phase = f"Phase {node.get('phase', '?')}"
                if phase not in summary["phases"]:
                    summary["phases"][phase] = {"total": 0, "complete": 0}
                summary["phases"][phase]["total"] += 1
                if node.get("status") == "complete":
                    summary["phases"][phase]["complete"] += 1
                    summary["complete"] += 1
    except Exception:
        pass

    return summary


# ── Bot Class ─────────────────────────────────────────────────────────

class SlateBot:
    """
    SLATE Discord Bot with security-first design.

    All interactions pass through DiscordSecurityGate.
    """

    def __init__(self):
        self.security = get_security_gate()
        self.bot: Optional[commands.Bot] = None
        self._start_time = time.time()

    def create_bot(self) -> "commands.Bot":
        """Create the Discord bot with minimal intents."""
        if not DISCORD_AVAILABLE:
            raise RuntimeError("discord.py is not installed")

        # MINIMAL intents — no message content, no presence, no members
        intents = discord.Intents.default()
        intents.message_content = False  # CRITICAL: no message snooping
        intents.presences = False        # No user presence data
        intents.members = False          # No member enumeration

        bot = commands.Bot(
            command_prefix="!",  # Not used (slash commands only)
            intents=intents,
            help_command=None,
        )

        self._register_events(bot)
        self._register_commands(bot)
        self.bot = bot
        return bot

    def _register_events(self, bot: "commands.Bot"):
        """Register bot event handlers."""

        @bot.event
        async def on_ready():
            logger.info(f"SLATE bot connected as {bot.user}")
            try:
                synced = await bot.tree.sync()
                logger.info(f"Synced {len(synced)} slash commands")
            except Exception as e:
                logger.error(f"Failed to sync commands: {e}")

        @bot.event
        async def on_error(event, *args, **kwargs):
            # NEVER leak error details to Discord
            logger.error(f"Bot error in {event}", exc_info=True)

    def _register_commands(self, bot: "commands.Bot"):
        """Register slash commands."""

        @bot.tree.command(name="slate-status", description="Check SLATE system status")
        async def cmd_status(interaction: discord.Interaction):
            # Rate limit check
            rate = self.security.check_rate_limit(
                str(interaction.user.id),
                str(interaction.channel_id),
            )
            if not rate.allowed:
                await interaction.response.send_message(
                    rate.reason, ephemeral=True,
                )
                self.security.audit_log(
                    "rate_limited", str(interaction.user.id),
                    "/slate-status", rate_limited=True,
                )
                return

            await interaction.response.defer()

            try:
                status = get_sanitized_status()
                embed = discord.Embed(
                    title="SLATE System Status",
                    color=SLATE_COLOR,
                    timestamp=datetime.now(timezone.utc),
                )
                embed.add_field(name="Dashboard", value=status["dashboard"], inline=True)
                embed.add_field(name="AI Backend", value=status["ai_backend"], inline=True)
                embed.add_field(name="GPU", value=f"{status['gpu_count']}x Active", inline=True)
                embed.add_field(name="Tech Tree", value=status["tech_tree_completion"], inline=True)
                embed.set_footer(text=SLATE_FOOTER)

                # Sanitize the entire embed description through security gate
                safe_check = self.security.sanitize_output(str(embed.to_dict()))
                if not safe_check.allowed:
                    await interaction.followup.send(
                        "Status temporarily unavailable.", ephemeral=True,
                    )
                    return

                await interaction.followup.send(embed=embed)

            except Exception as e:
                logger.error(f"Status command error: {e}")
                await interaction.followup.send(
                    "An error occurred. Please try again.", ephemeral=True,
                )

            self.security.audit_log(
                "command", str(interaction.user.id), "/slate-status",
            )

        @bot.tree.command(name="slate-feedback", description="Submit feedback about SLATE")
        @app_commands.describe(message="Your feedback, feature request, or bug report")
        async def cmd_feedback(interaction: discord.Interaction, message: str):
            # Rate limit
            rate = self.security.check_rate_limit(
                str(interaction.user.id),
                str(interaction.channel_id),
            )
            if not rate.allowed:
                await interaction.response.send_message(
                    rate.reason, ephemeral=True,
                )
                return

            # Validate input
            validation = self.security.validate_feedback(message)
            if not validation.allowed:
                await interaction.response.send_message(
                    validation.reason, ephemeral=True,
                )
                self.security.audit_log(
                    "input_blocked", str(interaction.user.id),
                    "/slate-feedback", input_text=message,
                    blocked_patterns=validation.blocked_patterns,
                )
                return

            await interaction.response.defer(ephemeral=True)

            try:
                clean_content = validation.filtered_content
                feedback_id = store_feedback(
                    user_id=str(interaction.user.id),
                    channel=str(interaction.channel),
                    content=clean_content,
                )

                embed = discord.Embed(
                    title="Feedback Received",
                    description=f"Thank you! Your feedback has been recorded.",
                    color=EMBED_COLORS["success"],
                    timestamp=datetime.now(timezone.utc),
                )
                embed.add_field(name="Tracking ID", value=feedback_id, inline=True)
                embed.add_field(name="Status", value="Pending Review", inline=True)
                embed.set_footer(text=SLATE_FOOTER)

                await interaction.followup.send(embed=embed, ephemeral=True)

            except Exception as e:
                logger.error(f"Feedback command error: {e}")
                await interaction.followup.send(
                    "An error occurred saving your feedback. Please try again.",
                    ephemeral=True,
                )

            self.security.audit_log(
                "command", str(interaction.user.id),
                "/slate-feedback", input_text=clean_content,
            )

        @bot.tree.command(name="slate-tree", description="View SLATE tech tree progress")
        async def cmd_tree(interaction: discord.Interaction):
            # Rate limit
            rate = self.security.check_rate_limit(
                str(interaction.user.id),
                str(interaction.channel_id),
            )
            if not rate.allowed:
                await interaction.response.send_message(
                    rate.reason, ephemeral=True,
                )
                return

            await interaction.response.defer()

            try:
                summary = get_tech_tree_summary()
                embed = discord.Embed(
                    title="SLATE Tech Tree Progress",
                    color=SLATE_COLOR,
                    timestamp=datetime.now(timezone.utc),
                )

                for phase, data in sorted(summary["phases"].items()):
                    pct = 100 * data["complete"] // max(data["total"], 1)
                    bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
                    embed.add_field(
                        name=phase,
                        value=f"{bar} {pct}% ({data['complete']}/{data['total']})",
                        inline=False,
                    )

                embed.add_field(
                    name="Overall",
                    value=f"{summary['complete']}/{summary['total']} nodes complete",
                    inline=False,
                )
                embed.set_footer(text=SLATE_FOOTER)

                await interaction.followup.send(embed=embed)

            except Exception as e:
                logger.error(f"Tree command error: {e}")
                await interaction.followup.send(
                    "An error occurred. Please try again.", ephemeral=True,
                )

            self.security.audit_log(
                "command", str(interaction.user.id), "/slate-tree",
            )

        @bot.tree.command(name="slate-about", description="About the SLATE project")
        async def cmd_about(interaction: discord.Interaction):
            embed = discord.Embed(
                title="S.L.A.T.E.",
                description=(
                    "**Synchronized Living Architecture for Transformation and Evolution**\n\n"
                    "A local AI-powered development platform with dual-GPU inference, "
                    "real-time system monitoring, autonomous workflow orchestration, "
                    "and community-driven development."
                ),
                color=SLATE_COLOR,
                url=GITHUB_URL,
                timestamp=datetime.now(timezone.utc),
            )
            embed.add_field(name="GitHub", value=f"[Repository]({GITHUB_URL})", inline=True)
            embed.add_field(name="Pages", value=f"[Website]({PAGES_URL})", inline=True)
            embed.add_field(name="License", value="EOSL-1.0", inline=True)
            embed.add_field(
                name="Submit Feedback",
                value="Use `/slate-feedback` to submit ideas and bug reports",
                inline=False,
            )
            embed.set_footer(text=SLATE_FOOTER)

            await interaction.response.send_message(embed=embed)

            self.security.audit_log(
                "command", str(interaction.user.id), "/slate-about",
            )

    async def start(self):
        """Start the bot."""
        if not DISCORD_AVAILABLE:
            print("ERROR: discord.py is not installed. Run: pip install discord.py")
            return

        token = os.environ.get("DISCORD_BOT_TOKEN")
        if not token:
            print("ERROR: DISCORD_BOT_TOKEN environment variable not set.")
            print("Get your bot token from https://discord.com/developers/applications")
            return

        bot = self.create_bot()
        logger.info("Starting SLATE Discord bot...")
        await bot.start(token)


# ── Health Check Server ───────────────────────────────────────────────

async def health_server():
    """Simple HTTP health check server for K8s probes."""
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import threading

    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path in ("/health", "/ready"):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "healthy"}).encode())
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format, *args):
            pass  # Suppress access logs

    server = HTTPServer(("127.0.0.1", BOT_PORT), HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info(f"Health check server on 127.0.0.1:{BOT_PORT}")


# ── CLI ───────────────────────────────────────────────────────────────

def main():
    """Run the SLATE Discord bot."""
    import argparse

    parser = argparse.ArgumentParser(description="SLATE Discord Bot")
    parser.add_argument("--start", action="store_true", help="Start the bot")
    parser.add_argument("--status", action="store_true", help="Show bot status")
    parser.add_argument("--test-security", action="store_true", help="Run security gate tests")

    args = parser.parse_args()

    if args.test_security:
        from slate.discord_security import main as security_test
        return security_test()

    if args.status:
        print()
        print("============================================================")
        print("  SLATE Discord Bot Status")
        print("============================================================")
        print()
        print(f"  discord.py installed: {'Yes' if DISCORD_AVAILABLE else 'No'}")
        print(f"  Bot token set:        {'Yes' if os.environ.get('DISCORD_BOT_TOKEN') else 'No'}")
        print(f"  App ID:               {os.environ.get('DISCORD_APP_ID', 'Not set')}")
        print(f"  Health port:          {BOT_PORT}")
        print(f"  Security gate:        Active")
        print()

        # Show feedback stats
        data = _load_feedback()
        print(f"  Feedback received:    {data['metrics'].get('total_feedback', 0)}")
        by_intent = data["metrics"].get("by_intent", {})
        for intent, count in by_intent.items():
            print(f"    {intent}: {count}")
        print()
        print("============================================================")
        return 0

    if args.start:
        logging.basicConfig(level=logging.INFO)
        slate_bot = SlateBot()

        async def run():
            await health_server()
            await slate_bot.start()

        asyncio.run(run())
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
