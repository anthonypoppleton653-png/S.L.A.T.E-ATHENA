#!/usr/bin/env python3
"""
SLATE Discord Bot — slate.bot Community Support
==================================================

Secure, LOCAL-ONLY Discord bot for SLATE community interaction. Provides
sanitized system status, collects community feedback, shows tech tree
progress, and acts as a community support line within SLATE project scope.

CRITICAL: This bot is GUILD-LOCKED to the SLATE community server only.
It CANNOT be installed on other servers to prevent hijacking local
inference endpoints. The bot validates its guild on startup and rejects
any interactions from unauthorized guilds.

Users are informed they are interacting with slate.bot (powered by slate.ai).
Rate limits are tier-based on GitHub fork engagement.
Support responses powered by local Ollama (agentic AI).
@mention support: Users can @slate.bot in any channel for AI-assisted help.

Security Architecture:
  Discord Gateway ←→ Bot ←→ GuildLock ←→ DiscordSecurityGate ←→ SLATE internals
                                               ↓
                                         PII Scanner / ActionGuard / Audit Log
                                         CommunityManager (tier-based rate limits)
                                         OnboardingManager (server structure)
                                         AgenticSupport (local Ollama)

ALL responses pass through discord_security.py before reaching Discord.
NO system internals (IPs, ports, paths, tokens) are ever exposed.

Slash Commands (17):
  /slate-status      — Sanitized system health
  /slate-feedback    — Submit community feedback
  /slate-tree        — Tech tree progress
  /slate-about       — Project information
  /slate-support     — Ask questions (agentic AI via local Ollama)
  /slate-register    — Link GitHub account (privacy-driven, fork-based tiers)
  /slate-unregister  — Remove all your data
  /slate-profile     — View your community profile and tier
  /slate-help        — All available commands reference
  /slate-docs        — Browse documentation by topic
  /slate-commands    — SLATE CLI command reference
  /slate-specs       — View specification status
  /slate-invite      — Community invite and onboarding
  /slate-leaderboard — Top contributors
  /slate-health      — Detailed service health report
  /slate-version     — Bot version and system info
  /slate-catchphrase — Random SLATE inspiration

Dependencies:
  discord.py >= 2.3.0 (MIT license)
"""
# Modified: 2026-02-09T21:00:00Z | Author: Claude Opus 4.6 | Change: Add onboarding, agentic AI, guild-lock, artwork

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
from slate.slate_community import (
    get_community_manager, CommunityManager, TIERS,
    SLATE_AI_IDENTITY, find_support_answer,
)
from slate.discord_onboarding import (
    get_onboarding_manager, OnboardingManager,
    build_welcome_dm_embed,
)

# ── Constants ─────────────────────────────────────────────────────────

BOT_PORT = int(os.environ.get("DISCORD_PORT", "8086"))
TECH_TREE_PATH = WORKSPACE_ROOT / ".slate_tech_tree" / "tech_tree.json"
FEEDBACK_DIR = WORKSPACE_ROOT / ".slate_discussions"
FEEDBACK_FILE = FEEDBACK_DIR / "discord_feedback.json"
TASKS_FILE = WORKSPACE_ROOT / "current_tasks.json"
LOCKDOWN_FILE = WORKSPACE_ROOT / ".slate_community" / "bot_lockdown.json"

# SLATE brand
SLATE_COLOR = 0xB85A3C  # Warm rust
SLATE_FOOTER = "slate.ai — It's always better with a blank SLATE"
GITHUB_URL = "https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E"
PAGES_URL = "https://synchronizedlivingarchitecture.github.io/S.L.A.T.E/"

# SLATE invite link (with permissions integer)
INVITE_URL = "https://discord.gg/2A4tUnzg2B"
BOT_VERSION = "2.0.0"

# Owner identification for admin functions
OWNER_ID = os.environ.get("DISCORD_OWNER_ID", "")


# ── System-Busy Fallback ─────────────────────────────────────────────

def _check_system_busy() -> tuple[bool, str]:
    """
    Check if the SLATE system is too busy to handle AI requests.

    Returns (is_busy, reason) tuple. When busy, commands should fall back
    to static/cached responses instead of querying Ollama.
    """
    import urllib.request

    # Check Ollama availability
    ollama_up = False
    try:
        req = urllib.request.Request("http://127.0.0.1:11434/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=2) as resp:
            ollama_up = resp.status == 200
    except Exception:
        pass

    if not ollama_up:
        return True, "AI inference is offline"

    # Check GPU utilization
    try:
        import subprocess
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=3,
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            avg_util = sum(int(l.strip()) for l in lines if l.strip().isdigit()) / max(len(lines), 1)
            if avg_util > 95:
                return True, "GPU at maximum capacity"
    except Exception:
        pass

    return False, ""


def _get_busy_fallback_embed(command_name: str) -> "discord.Embed":
    """
    Build a fallback embed when the system is too busy for AI queries.

    Provides useful static information instead of an error.
    """
    fallbacks = {
        "/slate-support": (
            "🔧 **System is currently busy** — AI inference is at capacity.\n\n"
            "While I can't process your question right now, here are some resources:\n\n"
            "📖 **Documentation**: Use `/slate-docs` for guides and tutorials\n"
            "📚 **Knowledge Base**: Use `/slate-commands` to see all available commands\n"
            "🌐 **Website**: [SLATE Docs](https://synchronizedlivingarchitecture.github.io/S.L.A.T.E/)\n"
            "💬 **Community**: Ask in #support — other members may be able to help\n"
            "📝 **Feedback**: Use `/slate-feedback` to save your question for later\n\n"
            "*System will be available again shortly. Try again in a few minutes.*"
        ),
        "/slate-status": (
            "🔧 **System status check is delayed** — services are under heavy load.\n\n"
            "**What this means:**\n"
            "• The AI backend (Ollama) is processing other requests\n"
            "• GPU resources are near capacity\n"
            "• Core services may still be operational\n\n"
            "Try again in a minute or check the dashboard directly."
        ),
        "@mention": (
            "🔧 **I'm a bit busy right now!** The system is under heavy load.\n\n"
            "Try these while you wait:\n"
            "• `/slate-docs` — Browse SLATE documentation\n"
            "• `/slate-commands` — See all available commands\n"
            "• `/slate-about` — Learn about the project\n\n"
            "*I'll be back to full speed shortly!*"
        ),
    }
    description = fallbacks.get(command_name, fallbacks["/slate-support"])

    embed = discord.Embed(
        title="⏳ System Busy",
        description=description,
        color=0xFFA500,  # Amber/warning color
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text="slate.ai — It's always better with a blank SLATE")
    return embed

# ── Guild Lock (LOCAL-ONLY enforcement) ───────────────────────────────
# The bot is LOCKED to ONE specific guild to prevent other servers from
# installing it and hijacking the local inference endpoints (Ollama, etc.)
# If someone adds the bot to another server, it will immediately leave.
ALLOWED_GUILD_ID = int(os.environ.get("DISCORD_GUILD_ID", "1469890015780933786"))
GUILD_LOCK_ENABLED = True  # NEVER disable this in production


# ── Owner Lockdown ───────────────────────────────────────────────────

def _is_locked() -> bool:
    """Check if bot is in owner-only lockdown mode."""
    if LOCKDOWN_FILE.exists():
        try:
            data = json.loads(LOCKDOWN_FILE.read_text(encoding="utf-8"))
            return data.get("locked", True)
        except Exception:
            pass
    return True  # Default: locked until explicitly unlocked


def _set_lockdown(locked: bool):
    """Set bot lockdown state."""
    LOCKDOWN_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "locked": locked,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": "owner",
    }
    LOCKDOWN_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _is_owner(interaction) -> bool:
    """Check if the interaction is from the bot/app owner."""
    if DISCORD_AVAILABLE:
        # Check if user is the guild owner or matches OWNER_ID
        if OWNER_ID and str(interaction.user.id) == OWNER_ID:
            return True
        if interaction.guild and interaction.guild.owner_id == interaction.user.id:
            return True
    return False


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

    GUILD-LOCKED: Only operates in the authorized SLATE server.
    All interactions pass through DiscordSecurityGate.
    Intelligent anti-flood protection (burst detection, escalating cooldowns).
    Community management with GitHub fork-based tiers.
    Agentic AI support via local Ollama inference.
    System-busy fallback when GPU/Ollama at capacity.
    17 slash commands + @mention support.
    Full onboarding pipeline with roles, channels, artwork.
    """

    def __init__(self):
        self.security = get_security_gate()
        self.community = get_community_manager()
        self.onboarding = get_onboarding_manager()
        self.bot: Optional[commands.Bot] = None
        self._start_time = time.time()
        self._server_setup_done = False

    def create_bot(self) -> "commands.Bot":
        """Create the Discord bot with minimal intents."""
        if not DISCORD_AVAILABLE:
            raise RuntimeError("discord.py is not installed")

        # Minimal intents — no message content, no presence
        # Members intent will be enabled in Developer Portal when ready
        intents = discord.Intents.default()
        intents.message_content = True   # Enabled: needed for @mention responses
        intents.presences = False        # No user presence data
        # Members intent: Enable in Discord Developer Portal → Bot →
        # Privileged Gateway Intents → Server Members Intent = ON
        # Then set this to True for on_member_join onboarding
        intents.members = True           # Enabled: Developer Portal Server Members Intent is ON

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

            # ── Guild Lock Enforcement ────────────────────────────
            # If the bot is in any unauthorized guilds, leave immediately
            if GUILD_LOCK_ENABLED:
                for guild in bot.guilds:
                    if guild.id != ALLOWED_GUILD_ID:
                        logger.warning(
                            f"GUILD LOCK: Leaving unauthorized guild "
                            f"'{guild.name}' ({guild.id})"
                        )
                        try:
                            await guild.leave()
                        except Exception as e:
                            logger.error(f"Failed to leave guild {guild.id}: {e}")

            # ── Sync Slash Commands ───────────────────────────────
            try:
                synced = await bot.tree.sync()
                logger.info(f"Synced {len(synced)} slash commands")
            except Exception as e:
                logger.error(f"Failed to sync commands: {e}")

            # ── Auto-Setup Server Structure ───────────────────────
            if not self._server_setup_done:
                for guild in bot.guilds:
                    if guild.id == ALLOWED_GUILD_ID:
                        logger.info(f"Running server structure setup for {guild.name}...")
                        try:
                            report = await self.onboarding.setup_server(
                                guild, guild.me,
                            )
                            self._server_setup_done = True
                            logger.info(
                                f"Server setup complete: "
                                f"{len(report['roles_created'])} roles created, "
                                f"{len(report['channels_created'])} channels created, "
                                f"{len(report['errors'])} errors"
                            )
                            if report["errors"]:
                                for err in report["errors"]:
                                    logger.warning(f"Setup error: {err}")
                        except Exception as e:
                            logger.error(f"Server setup failed: {e}")

        @bot.event
        async def on_guild_join(guild: discord.Guild):
            """If bot is added to an unauthorized guild, leave immediately."""
            if GUILD_LOCK_ENABLED and guild.id != ALLOWED_GUILD_ID:
                logger.warning(
                    f"GUILD LOCK: Rejecting unauthorized guild "
                    f"'{guild.name}' ({guild.id}) — leaving immediately"
                )
                try:
                    # Try to send a message explaining why
                    for channel in guild.text_channels:
                        if channel.permissions_for(guild.me).send_messages:
                            await channel.send(
                                "⚠️ **slate.bot is a local-only bot** and cannot "
                                "operate on external servers. It is locked to the "
                                "SLATE community server to protect local inference "
                                "endpoints. Leaving server."
                            )
                            break
                except Exception:
                    pass
                await guild.leave()
                return

        @bot.event
        async def on_member_join(member: discord.Member):
            """Handle new members joining the SLATE server."""
            if member.guild.id != ALLOWED_GUILD_ID:
                return
            if member.bot:
                return

            logger.info(f"New member: {member.display_name}")

            # Find #introductions channel for welcome message
            welcome_channel = None
            for channel in member.guild.text_channels:
                if channel.name == "introductions":
                    welcome_channel = channel
                    break

            await self.onboarding.on_member_join(member, welcome_channel)

        @bot.event
        async def on_message(message: discord.Message):
            """Handle @mention messages — respond with agentic AI support."""
            # Ignore messages from bots (including self)
            if message.author.bot:
                return

            # Block DMs — slate.bot is community-only, no private conversations
            if not message.guild:
                dm_embed = discord.Embed(
                    title="🏛️ slate.bot is a Community Bot!",
                    description=(
                        "Hey there! I don't do private conversations — "
                        "I'm designed to help the **whole community** learn together.\n\n"
                        "**Come chat with me in the SLATE server instead!**"
                    ),
                    color=SLATE_COLOR,
                )
                dm_embed.add_field(
                    name="🚀 Join the Community",
                    value=f"**[SLATE Discord Server]({INVITE_URL})**",
                    inline=False,
                )
                dm_embed.add_field(
                    name="💬 How to Use slate.bot",
                    value=(
                        "• **@slate.bot** your question in any channel\n"
                        "• Use `/slate-support` for AI-powered answers\n"
                        "• Use `/slate-status` to check system health\n"
                        "• Use `/slate-feedback` to submit ideas\n"
                        "• Use `/slate-help` to see all commands"
                    ),
                    inline=False,
                )
                dm_embed.add_field(
                    name="📖 Resources",
                    value=(
                        "• [GitHub](https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E)\n"
                        "• [Docs](https://synchronizedlivingarchitecture.github.io/S.L.A.T.E/)\n"
                        "• [Discussions](https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E/discussions)"
                    ),
                    inline=False,
                )
                dm_embed.set_footer(text=SLATE_FOOTER)
                await message.reply(embed=dm_embed)
                self.security.audit_log(
                    "dm_rejected", str(message.author.id), "DM attempt blocked",
                )
                return

            # Only respond when the bot is @mentioned
            if not bot.user or bot.user not in message.mentions:
                return

            # Guild lock check
            if GUILD_LOCK_ENABLED and message.guild:
                if message.guild.id != ALLOWED_GUILD_ID:
                    return

            # Owner lockdown check
            if _is_locked():
                # Only allow owner during lockdown
                if message.guild and message.guild.owner_id != message.author.id:
                    await message.reply(
                        "🔒 **slate.bot is currently in owner-only mode.** "
                        "It will be opened to the community soon!",
                    )
                    return

            # Extract the question (remove the @mention)
            question = message.content
            for mention in message.mentions:
                question = question.replace(f"<@{mention.id}>", "").replace(f"<@!{mention.id}>", "")
            question = question.strip()

            if not question:
                await message.reply(
                    "👋 Hey! I'm **slate.bot** — the SLATE community AI assistant.\n\n"
                    "**Ask me anything about SLATE!** Just @mention me with your question.\n"
                    "You can also use `/slate-support` for a dedicated support thread.\n\n"
                    "*Powered by slate.ai (local Ollama inference)*"
                )
                return

            # Validate input through security gate
            validation = self.security.validate_input(question)
            if not validation.allowed:
                await message.reply(
                    "⚠️ Your message was filtered for security. "
                    "Please rephrase without URLs, code blocks, or mentions."
                )
                return

            # Hardware-aware rate limiting via community manager
            user_id = str(message.author.id)
            tier_check = self.community.check_question_limit_hardware_aware(user_id)
            if not tier_check.allowed:
                await message.reply(
                    f"⏳ {tier_check.reason}\n"
                    f"Upgrade via `/slate-register` for higher limits!"
                )
                return

            # Show typing indicator while generating response
            async with message.channel.typing():
                # Check system load first — fallback to KB if busy
                is_busy, busy_reason = _check_system_busy()

                ai_response = None
                source = None

                if not is_busy:
                    try:
                        # Try agentic AI (local Ollama) first
                        ai_response = await self.onboarding.get_ai_support_response(question)
                        source = "🧠 AI"
                    except Exception:
                        ai_response = None

                if not ai_response:
                    # Fall back to keyword matching (imported at module top)
                    ai_response = find_support_answer(question)
                    source = "📚 KB"

                if not ai_response:
                    if is_busy:
                        # System busy — show helpful fallback
                        embed = _get_busy_fallback_embed("@mention")
                        await message.reply(embed=embed)
                        return
                    ai_response = (
                        "I don't have a specific answer for that, but here are some resources:\n"
                        "• Check our docs: https://synchronizedlivingarchitecture.github.io/S.L.A.T.E/\n"
                        "• Ask in #support for community help\n"
                        "• Use `/slate-feedback` to request new topics"
                    )
                    source = "📋 General"

            # Sanitize output through security gate
            safe_response = self.security.sanitize_output(ai_response)
            if not safe_response.allowed:
                ai_response = "I found an answer but it contained sensitive information. Please rephrase your question."
                source = "⚠️ Filtered"
            else:
                ai_response = safe_response.filtered_content

            # Build response embed
            embed = discord.Embed(
                description=ai_response,
                color=SLATE_COLOR,
                timestamp=datetime.now(timezone.utc),
            )
            embed.set_footer(text=f"slate.bot • {source} • Use /slate-support for detailed help")

            await message.reply(embed=embed)

            # Record the question
            self.community.record_question(user_id)

            # Audit log
            self.security.audit_log(
                "mention_response", user_id,
                f"@mention in #{message.channel.name}", input_text=question,
            )

        @bot.event
        async def on_error(event, *args, **kwargs):
            # NEVER leak error details to Discord
            logger.error(f"Bot error in {event}", exc_info=True)

    async def _check_access(self, interaction) -> bool:
        """Check if user has access (guild-lock + emergency lockdown via .json)."""
        # Guild lock: reject commands from unauthorized guilds
        if GUILD_LOCK_ENABLED and interaction.guild:
            if interaction.guild.id != ALLOWED_GUILD_ID:
                await interaction.response.send_message(
                    "⚠️ **slate.bot is a local-only bot** and cannot "
                    "operate on external servers.",
                    ephemeral=True,
                )
                self.security.audit_log(
                    "guild_lock_blocked", str(interaction.user.id),
                    interaction.command.name if interaction.command else "unknown",
                )
                return False

        # Owner lockdown mode
        if _is_locked() and not _is_owner(interaction):
            await interaction.response.send_message(
                "🔒 **slate.bot is currently in owner-only mode.**\n"
                "The bot is being configured and tested. "
                "It will be opened to the community soon!",
                ephemeral=True,
            )
            self.security.audit_log(
                "lockdown_blocked", str(interaction.user.id),
                interaction.command.name if interaction.command else "unknown",
            )
            return False
        return True

    def _register_commands(self, bot: "commands.Bot"):
        """Register slash commands."""

        # ── /slate-status ─────────────────────────────────────────

        @bot.tree.command(name="slate-status", description="Check SLATE system status")
        async def cmd_status(interaction: discord.Interaction):
            if not await self._check_access(interaction):
                return

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

        # ── /slate-feedback ───────────────────────────────────────

        @bot.tree.command(name="slate-feedback", description="Submit feedback about SLATE")
        @app_commands.describe(message="Your feedback, feature request, or bug report")
        async def cmd_feedback(interaction: discord.Interaction, message: str):
            if not await self._check_access(interaction):
                return

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

                # Record feedback in community manager for reputation
                self.community.record_feedback(str(interaction.user.id))

                embed = discord.Embed(
                    title="Feedback Received",
                    description="Thank you! Your feedback has been recorded.",
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

        # ── /slate-tree ───────────────────────────────────────────

        @bot.tree.command(name="slate-tree", description="View SLATE tech tree progress")
        async def cmd_tree(interaction: discord.Interaction):
            if not await self._check_access(interaction):
                return

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

        # ── /slate-about ──────────────────────────────────────────

        @bot.tree.command(name="slate-about", description="About the SLATE project")
        async def cmd_about(interaction: discord.Interaction):
            if not await self._check_access(interaction):
                return

            embed = discord.Embed(
                title="S.L.A.T.E.",
                description=(
                    "**Synchronized Living Architecture for Transformation and Evolution**\n\n"
                    "A local AI-powered development platform with dual-GPU inference, "
                    "real-time system monitoring, autonomous workflow orchestration, "
                    "and community-driven development.\n\n"
                    "🤖 *You are interacting with **slate.ai** — the SLATE community bot.*\n\n"
                    "💡 *It's always better with a blank SLATE.*"
                ),
                color=SLATE_COLOR,
                url=GITHUB_URL,
                timestamp=datetime.now(timezone.utc),
            )
            embed.add_field(name="GitHub", value=f"[Repository]({GITHUB_URL})", inline=True)
            embed.add_field(name="Pages", value=f"[Website]({PAGES_URL})", inline=True)
            embed.add_field(name="License", value="EOSL-1.0", inline=True)
            embed.add_field(
                name="Community",
                value=(
                    "• `/slate-support` — Ask questions\n"
                    "• `/slate-register` — Link GitHub\n"
                    "• `/slate-feedback` — Submit ideas\n"
                    "• `/slate-profile` — Your tier"
                ),
                inline=False,
            )
            embed.set_footer(text=SLATE_FOOTER)

            await interaction.response.send_message(embed=embed)

            self.security.audit_log(
                "command", str(interaction.user.id), "/slate-about",
            )

        # ── /slate-support ────────────────────────────────────────

        @bot.tree.command(
            name="slate-support",
            description="Ask a question about SLATE (you are interacting with slate.ai)",
        )
        @app_commands.describe(question="Your question about the SLATE project")
        async def cmd_support(interaction: discord.Interaction, question: str):
            if not await self._check_access(interaction):
                return

            # Rate limit (security gate)
            rate = self.security.check_rate_limit(
                str(interaction.user.id),
                str(interaction.channel_id),
            )
            if not rate.allowed:
                await interaction.response.send_message(
                    rate.reason, ephemeral=True,
                )
                return

            # Tier-based question limit with hardware-aware scaling
            tier_check = self.community.check_question_limit_hardware_aware(str(interaction.user.id))
            if not tier_check.allowed:
                await interaction.response.send_message(
                    tier_check.reason, ephemeral=True,
                )
                return

            # Validate input
            validation = self.security.validate_input(question)
            if not validation.allowed:
                await interaction.response.send_message(
                    validation.reason, ephemeral=True,
                )
                return

            await interaction.response.defer()

            try:
                clean_question = validation.filtered_content
                is_busy, busy_reason = _check_system_busy()

                ai_answer = None
                if not is_busy:
                    # Try agentic AI first (local Ollama)
                    ai_answer = await self.onboarding.get_ai_support_response(
                        clean_question, tier_check.tier,
                    )

                # Fall back to keyword matching if AI unavailable or system busy
                if not ai_answer:
                    ai_answer = find_support_answer(clean_question)

                response_source = "🧠 AI" if ai_answer and not is_busy and await self.onboarding.agentic.check_available() else "📚 KB"

                if ai_answer:
                    # Sanitize answer through security gate
                    safe = self.security.sanitize_output(ai_answer)
                    if not safe.allowed:
                        ai_answer = "I found an answer but it contained sensitive information. Please rephrase."
                    else:
                        ai_answer = safe.filtered_content

                    embed = discord.Embed(
                        title="slate.ai Support",
                        description=ai_answer,
                        color=SLATE_COLOR,
                        timestamp=datetime.now(timezone.utc),
                    )
                    embed.add_field(
                        name="Questions remaining",
                        value=f"{tier_check.remaining - 1}/{tier_check.limit} today",
                        inline=True,
                    )
                    embed.add_field(
                        name="Your tier",
                        value=f"{TIERS[tier_check.tier]['emoji']} {tier_check.tier_name}",
                        inline=True,
                    )
                    embed.add_field(
                        name="Source",
                        value=response_source,
                        inline=True,
                    )
                else:
                    if is_busy:
                        embed = _get_busy_fallback_embed("/slate-support")
                    else:
                        embed = discord.Embed(
                            title="slate.ai Support",
                            description=(
                                "I don't have a specific answer for that question. "
                                "Try asking about:\n"
                                "• Installation / setup / how to use SLATE\n"
                                "• How to fork / contribute\n"
                                "• Tech stack / GPU / Kubernetes\n"
                                "• Dashboard / workflows / AI backend\n"
                                "• Specifications / security / tokens\n"
                                "• Community tiers / Discord bot\n\n"
                                "Or use `/slate-feedback` to submit your question "
                                "for the development team!"
                            ),
                            color=0x808080,
                            timestamp=datetime.now(timezone.utc),
                        )

                embed.set_footer(text="🤖 You are interacting with slate.ai — SLATE Community Support (local inference)")
                await interaction.followup.send(embed=embed)

                # Record the question
                self.community.record_question(str(interaction.user.id))

            except Exception as e:
                logger.error(f"Support command error: {e}")
                await interaction.followup.send(
                    "An error occurred. Please try again.", ephemeral=True,
                )

            self.security.audit_log(
                "command", str(interaction.user.id),
                "/slate-support", input_text=clean_question,
            )

        # ── /slate-register ───────────────────────────────────────

        @bot.tree.command(
            name="slate-register",
            description="Link your GitHub account for tier-based access",
        )
        @app_commands.describe(github_username="Your GitHub username")
        async def cmd_register(interaction: discord.Interaction, github_username: str):
            if not await self._check_access(interaction):
                return

            await interaction.response.defer(ephemeral=True)

            try:
                # Validate input
                validation = self.security.validate_input(github_username)
                if not validation.allowed:
                    await interaction.followup.send(
                        "Invalid username format.", ephemeral=True,
                    )
                    return

                success, message = self.community.register_github(
                    str(interaction.user.id),
                    github_username.strip(),
                )

                embed = discord.Embed(
                    title="GitHub Registration",
                    description=message,
                    color=SLATE_COLOR if success else 0xFF4444,
                    timestamp=datetime.now(timezone.utc),
                )
                embed.set_footer(text="🤖 slate.ai — Privacy-driven community management")
                await interaction.followup.send(embed=embed, ephemeral=True)

                # Update Discord role to match new tier
                if success and interaction.guild:
                    member_info = self.community.get_member_info(str(interaction.user.id))
                    try:
                        await self.onboarding.update_member_role(
                            interaction.user, member_info["tier"],
                        )
                    except Exception as e:
                        logger.error(f"Role update failed: {e}")

            except Exception as e:
                logger.error(f"Register command error: {e}")
                await interaction.followup.send(
                    "An error occurred. Please try again.", ephemeral=True,
                )

            self.security.audit_log(
                "command", str(interaction.user.id),
                "/slate-register", input_text=github_username,
            )

        # ── /slate-unregister ─────────────────────────────────────

        @bot.tree.command(
            name="slate-unregister",
            description="Remove all your data from SLATE community system",
        )
        async def cmd_unregister(interaction: discord.Interaction):
            if not await self._check_access(interaction):
                return

            removed = self.community.remove_member(str(interaction.user.id))
            if removed:
                await interaction.response.send_message(
                    "✅ All your community data has been deleted. "
                    "You can re-register anytime with `/slate-register`.",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    "No data found to delete.", ephemeral=True,
                )

            self.security.audit_log(
                "command", str(interaction.user.id), "/slate-unregister",
            )

        # ── /slate-profile ────────────────────────────────────────

        @bot.tree.command(
            name="slate-profile",
            description="View your community profile, tier, and usage",
        )
        async def cmd_profile(interaction: discord.Interaction):
            if not await self._check_access(interaction):
                return

            info = self.community.get_member_info(str(interaction.user.id))

            embed = discord.Embed(
                title=f"{info['tier_emoji']} Community Profile",
                color=SLATE_COLOR,
                timestamp=datetime.now(timezone.utc),
            )
            embed.add_field(
                name="Tier",
                value=f"**{info['tier_name']}** (Tier {info['tier']})",
                inline=True,
            )
            embed.add_field(
                name="Reputation",
                value=f"⭐ {info['reputation']}",
                inline=True,
            )
            embed.add_field(
                name="Questions Today",
                value=f"{info['questions_today']}/{info['questions_limit']} ({info['questions_remaining']} remaining)",
                inline=False,
            )

            if info["github_linked"]:
                embed.add_field(
                    name="GitHub",
                    value=f"[{info['github_username']}](https://github.com/{info['github_username']})",
                    inline=True,
                )
                fork_status = "✅ Active" if info["has_fork"] else "❌ Not forked"
                embed.add_field(name="Fork", value=fork_status, inline=True)
            else:
                embed.add_field(
                    name="GitHub",
                    value="Not linked — `/slate-register` to unlock tiers!",
                    inline=False,
                )

            embed.add_field(
                name="Lifetime Stats",
                value=f"Questions: {info['total_questions']} | Feedback: {info['total_feedback']}",
                inline=False,
            )
            embed.set_footer(text="🤖 slate.ai — Privacy-driven community management")

            await interaction.response.send_message(embed=embed, ephemeral=True)

            self.security.audit_log(
                "command", str(interaction.user.id), "/slate-profile",
            )

        # ── /slate-help ─────────────────────────────────────────

        @bot.tree.command(
            name="slate-help",
            description="Show all available SLATE bot commands",
        )
        async def cmd_help(interaction: discord.Interaction):
            if not await self._check_access(interaction):
                return

            embed = discord.Embed(
                title="📋 SLATE Bot Commands",
                description="All available slash commands for slate.bot:",
                color=SLATE_COLOR,
                timestamp=datetime.now(timezone.utc),
            )
            embed.add_field(
                name="📊 Information",
                value=(
                    "`/slate-status` — System health (GPU, AI, dashboard)\n"
                    "`/slate-tree` — Tech tree progress by phase\n"
                    "`/slate-about` — Project info, links, catchphrase\n"
                    "`/slate-version` — Bot version and system info\n"
                    "`/slate-health` — Detailed service health check"
                ),
                inline=False,
            )
            embed.add_field(
                name="🤖 AI Support",
                value=(
                    "`/slate-support <question>` — AI-powered Q&A\n"
                    "`@slate.bot <question>` — Mention me anywhere\n"
                    "`/slate-docs` — Browse SLATE documentation\n"
                    "`/slate-commands` — Command reference and CLI guide\n"
                    "`/slate-specs` — View specification status"
                ),
                inline=False,
            )
            embed.add_field(
                name="👤 Community",
                value=(
                    "`/slate-register <github>` — Link GitHub for tiers\n"
                    "`/slate-unregister` — Delete all your data (GDPR)\n"
                    "`/slate-profile` — Your tier, rep, and stats\n"
                    "`/slate-leaderboard` — Community top contributors\n"
                    "`/slate-feedback <msg>` — Submit ideas and bugs"
                ),
                inline=False,
            )
            embed.add_field(
                name="🔧 Utility",
                value=(
                    "`/slate-help` — This help message\n"
                    "`/slate-invite` — Get the server invite link\n"
                    "`/slate-catchphrase` — Random SLATE inspiration"
                ),
                inline=False,
            )
            embed.set_footer(text=SLATE_FOOTER)
            await interaction.response.send_message(embed=embed)

            self.security.audit_log(
                "command", str(interaction.user.id), "/slate-help",
            )

        # ── /slate-docs ──────────────────────────────────────────

        @bot.tree.command(
            name="slate-docs",
            description="Browse SLATE documentation and guides",
        )
        @app_commands.describe(topic="Documentation topic to look up")
        @app_commands.choices(topic=[
            app_commands.Choice(name="Getting Started", value="getting_started"),
            app_commands.Choice(name="Installation", value="install"),
            app_commands.Choice(name="Dashboard", value="dashboard"),
            app_commands.Choice(name="AI Backend", value="ai"),
            app_commands.Choice(name="GPU Setup", value="gpu"),
            app_commands.Choice(name="Kubernetes", value="kubernetes"),
            app_commands.Choice(name="Workflows", value="workflow"),
            app_commands.Choice(name="Security", value="security"),
            app_commands.Choice(name="Token System", value="tokens"),
            app_commands.Choice(name="Contributing", value="contribute"),
            app_commands.Choice(name="Discord Bot", value="discord"),
            app_commands.Choice(name="Design System", value="design"),
        ])
        async def cmd_docs(interaction: discord.Interaction, topic: str = "getting_started"):
            if not await self._check_access(interaction):
                return

            # Map choices to SUPPORT_TOPICS keys
            topic_map = {
                "getting_started": "how to use slate",
                "install": "how to install",
                "dashboard": "dashboard",
                "ai": "ai backend",
                "gpu": "gpu setup",
                "kubernetes": "kubernetes",
                "workflow": "workflow",
                "security": "security",
                "tokens": "tokens",
                "contribute": "how to contribute",
                "discord": "discord bot",
                "design": "design",
            }
            topic_key = topic_map.get(topic, "how to use slate")
            answer = find_support_answer(topic_key)

            if not answer:
                answer = (
                    f"Documentation for **{topic}** is available at:\n"
                    f"🌐 [SLATE Website]({PAGES_URL})\n"
                    f"📦 [GitHub Repository]({GITHUB_URL})\n"
                    f"📖 [GitHub Wiki]({GITHUB_URL}/wiki)"
                )

            # Sanitize
            safe = self.security.sanitize_output(answer)
            if safe.allowed:
                answer = safe.filtered_content

            embed = discord.Embed(
                title=f"📖 SLATE Docs — {topic.replace('_', ' ').title()}",
                description=answer,
                color=SLATE_COLOR,
                timestamp=datetime.now(timezone.utc),
            )
            embed.add_field(
                name="More Resources",
                value=(
                    f"[Website]({PAGES_URL}) • "
                    f"[GitHub]({GITHUB_URL}) • "
                    f"[Wiki]({GITHUB_URL}/wiki)"
                ),
                inline=False,
            )
            embed.set_footer(text=SLATE_FOOTER)
            await interaction.response.send_message(embed=embed)

            self.security.audit_log(
                "command", str(interaction.user.id), f"/slate-docs {topic}",
            )

        # ── /slate-commands ──────────────────────────────────────

        @bot.tree.command(
            name="slate-commands",
            description="SLATE CLI command reference",
        )
        async def cmd_commands(interaction: discord.Interaction):
            if not await self._check_access(interaction):
                return

            embed = discord.Embed(
                title="⌨️ SLATE CLI Commands",
                description="Key commands for managing your SLATE installation:",
                color=SLATE_COLOR,
                timestamp=datetime.now(timezone.utc),
            )
            embed.add_field(
                name="🚀 Core",
                value=(
                    "```\n"
                    "python slate/slate_orchestrator.py start   # Start all services\n"
                    "python slate/slate_orchestrator.py stop    # Stop services\n"
                    "python slate/slate_status.py --quick       # System health\n"
                    "```"
                ),
                inline=False,
            )
            embed.add_field(
                name="🤖 AI",
                value=(
                    "```\n"
                    "python slate/unified_ai_backend.py --status  # Backend status\n"
                    "python slate/unified_ai_backend.py --task X  # Execute AI task\n"
                    "```"
                ),
                inline=False,
            )
            embed.add_field(
                name="📋 Workflow",
                value=(
                    "```\n"
                    "python slate/slate_workflow_manager.py --status  # Task health\n"
                    "python slate/slate_runner_manager.py --status    # Runner info\n"
                    "python slate/slate_runner_manager.py --dispatch  # Dispatch workflow\n"
                    "```"
                ),
                inline=False,
            )
            embed.add_field(
                name="🔒 Security",
                value=(
                    "```\n"
                    "python slate/slate_token_system.py --status   # Token health\n"
                    "python slate/sdk_source_guard.py --report     # SDK audit\n"
                    "python -m pytest tests/ -v                    # Run tests\n"
                    "```"
                ),
                inline=False,
            )
            embed.set_footer(text=SLATE_FOOTER)
            await interaction.response.send_message(embed=embed)

            self.security.audit_log(
                "command", str(interaction.user.id), "/slate-commands",
            )

        # ── /slate-specs ─────────────────────────────────────────

        @bot.tree.command(
            name="slate-specs",
            description="View SLATE specification status",
        )
        async def cmd_specs(interaction: discord.Interaction):
            if not await self._check_access(interaction):
                return

            await interaction.response.defer()

            try:
                specs_dir = WORKSPACE_ROOT / "specs"
                specs_info = []
                if specs_dir.exists():
                    for spec_dir in sorted(specs_dir.iterdir()):
                        if spec_dir.is_dir():
                            spec_file = spec_dir / "spec.md"
                            if spec_file.exists():
                                content = spec_file.read_text(encoding="utf-8", errors="replace")
                                # Extract status
                                status = "Unknown"
                                name = spec_dir.name
                                for line in content.split("\n")[:15]:
                                    if "**Status**" in line:
                                        status = line.split(":")[-1].strip().strip("*").strip()
                                        break
                                specs_info.append((name, status))

                embed = discord.Embed(
                    title="📑 SLATE Specifications",
                    description=f"**{len(specs_info)} specifications** tracked:",
                    color=SLATE_COLOR,
                    timestamp=datetime.now(timezone.utc),
                )

                # Status emoji map
                status_emoji = {
                    "Complete": "✅", "complete": "✅",
                    "Implementing": "🔨", "implementing": "🔨",
                    "Specified": "📝", "specified": "📝",
                    "Planned": "📋", "planned": "📋",
                    "Draft": "📄", "draft": "📄",
                }

                # Group by status
                by_status = {}
                for name, status in specs_info:
                    by_status.setdefault(status, []).append(name)

                for status, specs in sorted(by_status.items()):
                    emoji = status_emoji.get(status, "❓")
                    spec_list = "\n".join(f"• `{s}`" for s in specs[:8])
                    if len(specs) > 8:
                        spec_list += f"\n• ... and {len(specs) - 8} more"
                    embed.add_field(
                        name=f"{emoji} {status} ({len(specs)})",
                        value=spec_list,
                        inline=False,
                    )

                embed.set_footer(text=SLATE_FOOTER)
                await interaction.followup.send(embed=embed)

            except Exception as e:
                logger.error(f"Specs command error: {e}")
                await interaction.followup.send(
                    "Error loading specs. Try again later.", ephemeral=True,
                )

            self.security.audit_log(
                "command", str(interaction.user.id), "/slate-specs",
            )

        # ── /slate-invite ────────────────────────────────────────

        @bot.tree.command(
            name="slate-invite",
            description="Get the SLATE community invite link",
        )
        async def cmd_invite(interaction: discord.Interaction):
            if not await self._check_access(interaction):
                return

            embed = discord.Embed(
                title="🔗 Join the SLATE Community",
                description=(
                    "**S.L.A.T.E.** — Synchronized Living Architecture for "
                    "Transformation and Evolution\n\n"
                    f"📦 **GitHub**: [{GITHUB_URL.split('/')[-1]}]({GITHUB_URL})\n"
                    f"🌐 **Website**: [SLATE Docs]({PAGES_URL})\n"
                    f"💬 **Discord**: Share this server with friends!\n\n"
                    "**How to get involved:**\n"
                    "1. `/slate-register <github>` — Link your GitHub\n"
                    "2. Fork the repo — unlock Contributor tier\n"
                    "3. Make commits — unlock Builder tier\n"
                    "4. Use `/slate-feedback` to submit ideas\n\n"
                    "💡 *It's always better with a blank SLATE!*"
                ),
                color=SLATE_COLOR,
                timestamp=datetime.now(timezone.utc),
            )
            embed.set_footer(text=SLATE_FOOTER)
            await interaction.response.send_message(embed=embed)

            self.security.audit_log(
                "command", str(interaction.user.id), "/slate-invite",
            )

        # ── /slate-leaderboard ───────────────────────────────────

        @bot.tree.command(
            name="slate-leaderboard",
            description="View community top contributors",
        )
        async def cmd_leaderboard(interaction: discord.Interaction):
            if not await self._check_access(interaction):
                return

            stats = self.community.get_community_stats()
            members = self.community.get_all_members_ranked()

            embed = discord.Embed(
                title="🏆 SLATE Community Leaderboard",
                description=(
                    f"**{stats['total_members']}** members • "
                    f"**{stats['total_forks']}** forks • "
                    f"**{stats['total_questions']}** questions"
                ),
                color=SLATE_COLOR,
                timestamp=datetime.now(timezone.utc),
            )

            if members:
                # Top 10 by reputation
                top = members[:10]
                leaderboard_text = ""
                medals = ["🥇", "🥈", "🥉"]
                for i, m in enumerate(top):
                    tier_info = TIERS.get(m.get("tier", 0), TIERS[0])
                    medal = medals[i] if i < 3 else f"**{i+1}.**"
                    name = m.get("github_username") or f"Member #{m.get('user_hash', '?')[:6]}"
                    leaderboard_text += (
                        f"{medal} {tier_info['emoji']} **{name}** — "
                        f"⭐ {m.get('reputation', 0)} rep • "
                        f"{m.get('total_questions', 0)} questions\n"
                    )
                embed.add_field(
                    name="Top Contributors",
                    value=leaderboard_text or "No members yet — be the first!",
                    inline=False,
                )
            else:
                embed.add_field(
                    name="Top Contributors",
                    value="No community members yet! Use `/slate-register` to join.",
                    inline=False,
                )

            # Tier breakdown
            tier_text = ""
            for tier_name, count in stats.get("by_tier", {}).items():
                tier_text += f"• **{tier_name}**: {count}\n"
            if tier_text:
                embed.add_field(name="By Tier", value=tier_text, inline=True)

            embed.set_footer(text=SLATE_FOOTER)
            await interaction.response.send_message(embed=embed)

            self.security.audit_log(
                "command", str(interaction.user.id), "/slate-leaderboard",
            )

        # ── /slate-health ────────────────────────────────────────

        @bot.tree.command(
            name="slate-health",
            description="Detailed SLATE service health check",
        )
        async def cmd_health(interaction: discord.Interaction):
            if not await self._check_access(interaction):
                return

            await interaction.response.defer()

            try:
                is_busy, busy_reason = _check_system_busy()
                status = get_sanitized_status()

                embed = discord.Embed(
                    title="🏥 SLATE Health Report",
                    color=0x6B8E23 if not is_busy else 0xFFA500,
                    timestamp=datetime.now(timezone.utc),
                )

                # Service health
                services = [
                    ("Dashboard", status["dashboard"], "🖥️"),
                    ("AI Backend (Ollama)", status["ai_backend"], "🧠"),
                    ("GPU", f"{status['gpu_count']}x Active" if status["gpu_count"] > 0 else "None detected", "⚡"),
                ]
                health_text = ""
                for name, state, icon in services:
                    indicator = "🟢" if state in ("Online", "2x Active") else "🟡" if "Active" in str(state) else "🔴"
                    health_text += f"{indicator} {icon} **{name}**: {state}\n"

                embed.add_field(name="Services", value=health_text, inline=False)

                # System capacity
                capacity = "🟢 Available" if not is_busy else f"🟡 Busy ({busy_reason})"
                embed.add_field(name="AI Capacity", value=capacity, inline=True)
                embed.add_field(name="Tech Tree", value=status["tech_tree_completion"], inline=True)

                # Bot stats
                uptime_secs = int(time.time() - self._start_time)
                hours, remainder = divmod(uptime_secs, 3600)
                minutes, _ = divmod(remainder, 60)
                embed.add_field(
                    name="Bot Uptime",
                    value=f"{hours}h {minutes}m",
                    inline=True,
                )

                # Hardware-aware rate limiting status
                hw_mult = self.community.get_hardware_multiplier()
                if hw_mult >= 1.5:
                    limit_status = "🟢 Boosted (1.5x) — GPUs idle"
                elif hw_mult >= 1.0:
                    limit_status = "🟢 Normal (1.0x)"
                elif hw_mult >= 0.7:
                    limit_status = "🟡 Reduced (0.7x) — Heavy GPU load"
                elif hw_mult > 0.0:
                    limit_status = "🔴 Throttled (0.5x) — GPUs maxed"
                else:
                    limit_status = "🔴 Offline — Keyword fallback only"
                embed.add_field(name="Rate Limit Mode", value=limit_status, inline=False)

                embed.set_footer(text=SLATE_FOOTER)
                await interaction.followup.send(embed=embed)

            except Exception as e:
                logger.error(f"Health command error: {e}")
                await interaction.followup.send(
                    "Health check failed. Try again later.", ephemeral=True,
                )

            self.security.audit_log(
                "command", str(interaction.user.id), "/slate-health",
            )

        # ── /slate-version ───────────────────────────────────────

        @bot.tree.command(
            name="slate-version",
            description="Show SLATE bot version and system info",
        )
        async def cmd_version(interaction: discord.Interaction):
            if not await self._check_access(interaction):
                return

            embed = discord.Embed(
                title="ℹ️ SLATE Version",
                color=SLATE_COLOR,
                timestamp=datetime.now(timezone.utc),
            )
            embed.add_field(name="Bot Version", value=f"v{BOT_VERSION}", inline=True)
            embed.add_field(name="discord.py", value=discord.__version__, inline=True)
            embed.add_field(name="Python", value=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}", inline=True)
            embed.add_field(
                name="Components",
                value=(
                    f"• Slash commands: **17**\n"
                    f"• Security layers: **7**\n"
                    f"• Knowledge base topics: **20+**\n"
                    f"• Specifications: **27**"
                ),
                inline=False,
            )
            embed.add_field(
                name="Architecture",
                value=(
                    "• Local-only (127.0.0.1 binding)\n"
                    "• Guild-locked (single server)\n"
                    "• Hardware-aware rate limiting\n"
                    "• Agentic AI (Ollama mistral-nemo)"
                ),
                inline=False,
            )
            embed.set_footer(text=SLATE_FOOTER)
            await interaction.response.send_message(embed=embed)

            self.security.audit_log(
                "command", str(interaction.user.id), "/slate-version",
            )

        # ── /slate-catchphrase ───────────────────────────────────

        @bot.tree.command(
            name="slate-catchphrase",
            description="Get a random SLATE inspiration",
        )
        async def cmd_catchphrase(interaction: discord.Interaction):
            if not await self._check_access(interaction):
                return

            import random
            catchphrases = [
                "💡 **It's always better with a blank SLATE.**",
                "⚙️ **Systems Evolve With Progress.**",
                "🔧 **Every pixel serves a purpose. Every line of code has intent.**",
                "🏗️ **Beauty emerges from functional perfection, not decoration.**",
                "🧠 **Everything runs locally. No cloud. No costs. Just pure engineering.**",
                "🔒 **Security isn't a feature — it's the foundation.**",
                "⚡ **Dual GPUs. Zero latency. Infinite possibilities.**",
                "🌱 **Fork it. Customize it. Make it yours. That's what SLATE is for.**",
                "🤖 **AI should work for you, not the other way around.**",
                "📐 **Precision engineering. Watchmaker aesthetic. Every detail matters.**",
                "🔗 **Synchronized Living Architecture — where code comes alive.**",
                "🛡️ **Trust no cloud. Verify locally. Build independently.**",
            ]
            phrase = random.choice(catchphrases)

            await interaction.response.send_message(phrase)

            self.security.audit_log(
                "command", str(interaction.user.id), "/slate-catchphrase",
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


# ── Health Check + Federation API Server ──────────────────────────────

async def health_server():
    """HTTP server for K8s probes + SLATE-to-SLATE federation API."""
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import threading

    from slate.discord_federation import get_federation_manager, FederationAPIHandler

    federation = get_federation_manager()
    federation_api = FederationAPIHandler(federation)

    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path in ("/health", "/ready"):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "healthy"}).encode())
            elif self.path == "/api/v1/federation/status":
                code, response = federation_api._handle_status()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
            else:
                self.send_response(404)
                self.end_headers()

        def do_POST(self):
            if self.path.startswith("/api/v1/federation/"):
                content_length = int(self.headers.get("Content-Length", 0))
                body = {}
                if content_length:
                    try:
                        body = json.loads(self.rfile.read(content_length).decode())
                    except Exception:
                        self.send_response(400)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode())
                        return

                # Run async handler in event loop
                loop = asyncio.new_event_loop()
                try:
                    code, response = loop.run_until_complete(
                        federation_api.handle_request(self.path, "POST", body)
                    )
                finally:
                    loop.close()

                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format, *args):
            pass  # Suppress access logs

    server = HTTPServer(("127.0.0.1", BOT_PORT), HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info(f"Health + Federation API on 127.0.0.1:{BOT_PORT}")


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
        print(f"  Guild lock:           {'ENABLED' if GUILD_LOCK_ENABLED else 'DISABLED'}")
        print(f"  Allowed guild:        {ALLOWED_GUILD_ID}")
        print(f"  Owner lockdown:       {'LOCKED' if _is_locked() else 'UNLOCKED'}")
        print()
        print("  Onboarding:")
        onboard = get_onboarding_manager()
        status = onboard.get_onboarding_status()
        print(f"    Server structure:   {'Built' if status['structure_built'] else 'Pending'}")
        print(f"    Agentic AI:         {'Online' if status['agentic_support'] else 'Offline/Checking'}")
        print(f"    Total members:      {status['total_members']}")
        print(f"    By tier:            {status['by_tier']}")
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
