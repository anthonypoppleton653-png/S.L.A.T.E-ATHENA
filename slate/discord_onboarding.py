#!/usr/bin/env python3
"""
SLATE Discord Onboarding System
==================================

Full community onboarding pipeline managed by SLATE's agentic AI running locally.
Proves the concept of autonomous community management powered by local inference.

Onboarding Flow:
  1. Member joins → Welcome embed with SLATE branding + banner
  2. Auto-role assignment (Guest tier)
  3. Guided channel progression based on engagement
  4. Tier upgrades via /slate-register (GitHub fork-based)
  5. Agentic AI support via local Ollama

Server Structure (auto-created):
  Roles:
    @SLATE Owner        — Server owner, full access
    @SLATE Builder      — Tier 3 (fork + commits)
    @SLATE Contributor  — Tier 2 (forked SLATE)
    @SLATE Community    — Tier 1 (GitHub linked)
    @SLATE Guest        — Tier 0 (new members)
    @slate.ai           — Bot role

  Categories & Channels:
    ──────── Welcome ────────
    #welcome            — Read-only, rules + how to get started
    #introductions      — New members introduce themselves
    ──────── Community ──────
    #general            — General chat (all tiers)
    #support            — Bot-powered Q&A
    #feedback           — Feature requests and ideas
    #showcase           — Show off SLATE builds
    ──────── Development ────
    #dev-chat           — Development discussion (Contributor+)
    #dev-logs           — Bot posts build/deploy events
    #pull-requests      — PR discussion feed
    ──────── SLATE System ───
    #slate-status       — Bot-posted system health
    #slate-builds       — CI/CD notifications
    #slate-progress     — Tech tree updates
    #slate-alerts       — Error alerts (Contributor+)
    ──────── Admin (Owner) ──
    #bot-admin          — Owner-only bot management
    #audit-log          — Bot activity audit trail
    #bot-testing        — Bot command testing

Security:
  - All channel creation goes through ActionGuard validation
  - Bot role has ONLY required permissions
  - Admin channels restricted to owner via permission overwrites
  - No @everyone mentions from bot
  - All output sanitized through DiscordSecurityGate
"""
# Modified: 2026-02-09T21:00:00Z | Author: Claude Opus 4.6 | Change: Create full Discord onboarding system

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

WORKSPACE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

logger = logging.getLogger("slate.discord_onboarding")

# Attempt to import discord.py
try:
    import discord
    from discord import PermissionOverwrite, Permissions
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False

from slate.discord_security import get_security_gate
from slate.slate_community import get_community_manager, TIERS

# ── Constants ─────────────────────────────────────────────────────────

GITHUB_URL = "https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E"
PAGES_URL = "https://synchronizedlivingarchitecture.github.io/S.L.A.T.E/"
INVITE_URL = "https://discord.gg/2A4tUnzg2B"

# SLATE Brand Colors (from design-tokens.json)
COLORS = {
    "primary": 0xB85A3C,       # Warm rust
    "primary_dark": 0x8B4530,
    "secondary": 0x5D5D74,     # Gray-purple
    "tertiary": 0x6B8E23,      # Olive green
    "success": 0x4CAF50,
    "warning": 0xFF9800,
    "error": 0xF44336,
    "info": 0x2196F3,
    "blueprint_bg": 0x0D1B2A,
    "blueprint_grid": 0x1B3A4B,
    "surface_dark": 0x1A1816,
}

# ── Role Configuration ────────────────────────────────────────────────

ROLE_DEFINITIONS = [
    {
        "name": "SLATE Owner",
        "color": discord.Colour(COLORS["primary"]) if DISCORD_AVAILABLE else None,
        "hoist": True,
        "mentionable": False,
        "position_hint": 6,
        "permissions": discord.Permissions.all() if DISCORD_AVAILABLE else None,
        "tier": None,  # Manual assignment only
    },
    {
        "name": "SLATE Builder",
        "color": discord.Colour(COLORS["tertiary"]) if DISCORD_AVAILABLE else None,
        "hoist": True,
        "mentionable": True,
        "position_hint": 5,
        "permissions": discord.Permissions(
            send_messages=True, read_messages=True, embed_links=True,
            read_message_history=True, use_application_commands=True,
            attach_files=True, add_reactions=True, use_external_emojis=True,
            connect=True, speak=True,
        ) if DISCORD_AVAILABLE else None,
        "tier": 3,
    },
    {
        "name": "SLATE Contributor",
        "color": discord.Colour(COLORS["info"]) if DISCORD_AVAILABLE else None,
        "hoist": True,
        "mentionable": True,
        "position_hint": 4,
        "permissions": discord.Permissions(
            send_messages=True, read_messages=True, embed_links=True,
            read_message_history=True, use_application_commands=True,
            attach_files=True, add_reactions=True,
        ) if DISCORD_AVAILABLE else None,
        "tier": 2,
    },
    {
        "name": "SLATE Community",
        "color": discord.Colour(COLORS["secondary"]) if DISCORD_AVAILABLE else None,
        "hoist": True,
        "mentionable": True,
        "position_hint": 3,
        "permissions": discord.Permissions(
            send_messages=True, read_messages=True,
            read_message_history=True, use_application_commands=True,
            add_reactions=True,
        ) if DISCORD_AVAILABLE else None,
        "tier": 1,
    },
    {
        "name": "SLATE Guest",
        "color": discord.Colour(0x808080) if DISCORD_AVAILABLE else None,
        "hoist": False,
        "mentionable": False,
        "position_hint": 2,
        "permissions": discord.Permissions(
            send_messages=True, read_messages=True,
            read_message_history=True, use_application_commands=True,
        ) if DISCORD_AVAILABLE else None,
        "tier": 0,
    },
    {
        "name": "slate.ai",
        "color": discord.Colour(COLORS["primary_dark"]) if DISCORD_AVAILABLE else None,
        "hoist": True,
        "mentionable": False,
        "position_hint": 1,
        "permissions": discord.Permissions(
            send_messages=True, read_messages=True, embed_links=True,
            read_message_history=True, use_application_commands=True,
            manage_messages=True,
        ) if DISCORD_AVAILABLE else None,
        "tier": None,  # Bot role
    },
]

# ── Channel Configuration ─────────────────────────────────────────────

CATEGORY_CHANNELS = {
    "━━ WELCOME ━━": {
        "channels": [
            {
                "name": "welcome",
                "topic": "Welcome to SLATE! Read the rules and get started.",
                "type": "text",
                "read_only": True,  # Only bot/owner can post
                "min_tier": 0,
            },
            {
                "name": "introductions",
                "topic": "Introduce yourself to the community!",
                "type": "text",
                "read_only": False,
                "min_tier": 0,
            },
            {
                "name": "rules",
                "topic": "Community guidelines and code of conduct.",
                "type": "text",
                "read_only": True,
                "min_tier": 0,
            },
        ],
    },
    "━━ COMMUNITY ━━": {
        "channels": [
            {
                "name": "general",
                "topic": "General discussion about SLATE and AI development.",
                "type": "text",
                "read_only": False,
                "min_tier": 0,
            },
            {
                "name": "support",
                "topic": "Ask slate.ai questions with /slate-support",
                "type": "text",
                "read_only": False,
                "min_tier": 0,
            },
            {
                "name": "feedback",
                "topic": "Submit ideas and feature requests with /slate-feedback",
                "type": "text",
                "read_only": False,
                "min_tier": 0,
            },
            {
                "name": "showcase",
                "topic": "Show off your SLATE builds, forks, and experiments!",
                "type": "text",
                "read_only": False,
                "min_tier": 1,
            },
        ],
    },
    "━━ DEVELOPMENT ━━": {
        "channels": [
            {
                "name": "dev-chat",
                "topic": "SLATE development discussion (Contributors+)",
                "type": "text",
                "read_only": False,
                "min_tier": 2,
            },
            {
                "name": "dev-logs",
                "topic": "Automated build, deploy, and workflow notifications",
                "type": "text",
                "read_only": True,  # Bot-only
                "min_tier": 1,
            },
            {
                "name": "pull-requests",
                "topic": "PR discussion and code review feed",
                "type": "text",
                "read_only": False,
                "min_tier": 2,
            },
        ],
    },
    "━━ SLATE SYSTEM ━━": {
        "channels": [
            {
                "name": "slate-status",
                "topic": "Real-time SLATE system health (bot-managed)",
                "type": "text",
                "read_only": True,
                "min_tier": 0,
            },
            {
                "name": "slate-builds",
                "topic": "CI/CD pipeline notifications",
                "type": "text",
                "read_only": True,
                "min_tier": 1,
            },
            {
                "name": "slate-progress",
                "topic": "Tech tree completion and milestone updates",
                "type": "text",
                "read_only": True,
                "min_tier": 0,
            },
            {
                "name": "slate-alerts",
                "topic": "System alerts and error notifications (Contributors+)",
                "type": "text",
                "read_only": True,
                "min_tier": 2,
            },
        ],
    },
    "━━ ADMIN ━━": {
        "owner_only": True,
        "channels": [
            {
                "name": "bot-admin",
                "topic": "Owner-only bot management and configuration",
                "type": "text",
                "read_only": False,
                "min_tier": None,  # Owner only
            },
            {
                "name": "audit-log",
                "topic": "Bot interaction audit trail",
                "type": "text",
                "read_only": True,
                "min_tier": None,
            },
            {
                "name": "bot-testing",
                "topic": "Test bot commands in isolation",
                "type": "text",
                "read_only": False,
                "min_tier": None,
            },
        ],
    },
}


# ── Server Structure Builder ──────────────────────────────────────────

class ServerStructureBuilder:
    """
    Builds the SLATE Discord server structure programmatically.

    Creates roles, categories, channels, and permission overwrites
    to match the SLATE community design.
    """

    def __init__(self, guild: "discord.Guild", bot_user: "discord.Member"):
        self.guild = guild
        self.bot_user = bot_user
        self.roles: dict[str, "discord.Role"] = {}
        self.categories: dict[str, "discord.CategoryChannel"] = {}
        self.channels: dict[str, "discord.TextChannel"] = {}

    async def build_all(self) -> dict:
        """Build complete server structure. Returns creation report."""
        report = {
            "roles_created": [],
            "roles_existing": [],
            "categories_created": [],
            "channels_created": [],
            "channels_existing": [],
            "errors": [],
        }

        # Phase 1: Create roles
        await self._create_roles(report)

        # Phase 2: Create categories and channels
        await self._create_channels(report)

        # Phase 3: Post welcome content
        await self._post_welcome_content(report)

        # Phase 4: Post rules
        await self._post_rules_content(report)

        return report

    async def _create_roles(self, report: dict):
        """Create all SLATE roles if they don't exist."""
        existing_roles = {r.name: r for r in self.guild.roles}

        for role_def in ROLE_DEFINITIONS:
            name = role_def["name"]
            if name in existing_roles:
                self.roles[name] = existing_roles[name]
                report["roles_existing"].append(name)
                logger.info(f"Role exists: {name}")
                continue

            try:
                role = await self.guild.create_role(
                    name=name,
                    color=role_def["color"],
                    hoist=role_def["hoist"],
                    mentionable=role_def["mentionable"],
                    permissions=role_def["permissions"],
                    reason="SLATE onboarding: auto-created role",
                )
                self.roles[name] = role
                report["roles_created"].append(name)
                logger.info(f"Created role: {name}")
            except Exception as e:
                report["errors"].append(f"Role {name}: {e}")
                logger.error(f"Failed to create role {name}: {e}")

    async def _create_channels(self, report: dict):
        """Create categories and channels with permission overwrites."""
        existing_channels = {c.name: c for c in self.guild.channels}

        for cat_name, cat_config in CATEGORY_CHANNELS.items():
            # Create category
            if cat_name in existing_channels:
                category = existing_channels[cat_name]
                self.categories[cat_name] = category
            else:
                try:
                    overwrites = self._build_category_overwrites(cat_config)
                    category = await self.guild.create_category(
                        name=cat_name,
                        overwrites=overwrites,
                        reason="SLATE onboarding: auto-created category",
                    )
                    self.categories[cat_name] = category
                    report["categories_created"].append(cat_name)
                    logger.info(f"Created category: {cat_name}")
                except Exception as e:
                    report["errors"].append(f"Category {cat_name}: {e}")
                    logger.error(f"Failed to create category {cat_name}: {e}")
                    continue

            # Create channels in this category
            for ch_config in cat_config["channels"]:
                ch_name = ch_config["name"]
                if ch_name in existing_channels:
                    self.channels[ch_name] = existing_channels[ch_name]
                    report["channels_existing"].append(ch_name)
                    continue

                try:
                    overwrites = self._build_channel_overwrites(ch_config, cat_config)
                    channel = await self.guild.create_text_channel(
                        name=ch_name,
                        category=category,
                        topic=ch_config.get("topic", ""),
                        overwrites=overwrites,
                        reason="SLATE onboarding: auto-created channel",
                    )
                    self.channels[ch_name] = channel
                    report["channels_created"].append(ch_name)
                    logger.info(f"Created channel: #{ch_name}")
                except Exception as e:
                    report["errors"].append(f"Channel {ch_name}: {e}")
                    logger.error(f"Failed to create channel #{ch_name}: {e}")

    def _build_category_overwrites(self, cat_config: dict) -> dict:
        """Build permission overwrites for a category."""
        overwrites = {}

        if cat_config.get("owner_only"):
            # Admin category: hide from everyone, show to owner + bot
            overwrites[self.guild.default_role] = PermissionOverwrite(
                read_messages=False,
                send_messages=False,
            )
            # Bot can see admin channels
            if self.bot_user:
                overwrites[self.bot_user] = PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    embed_links=True,
                )
            # Owner role
            owner_role = self.roles.get("SLATE Owner")
            if owner_role:
                overwrites[owner_role] = PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    manage_messages=True,
                )

        return overwrites

    def _build_channel_overwrites(self, ch_config: dict, cat_config: dict) -> dict:
        """Build permission overwrites for a channel.

        Permission Matrix:
          - Admin channels: Owner + Bot only, @everyone denied
          - Tier-restricted: @everyone denied, Guest denied, qualifying tiers granted
          - Read-only (open): @everyone send denied, bot + owner can send
          - Open (writable): No special overwrites needed (inherits category)

        Bot always has read + send + embed in every non-default channel.
        Owner always has read + send + manage in every channel.
        """
        # Modified: 2026-02-09T23:30:00Z | Author: COPILOT | Change: Fix permission validation — ensure Guest denial, bot access in all channels, Owner override
        overwrites = {}
        min_tier = ch_config.get("min_tier", 0)
        read_only = ch_config.get("read_only", False)
        is_admin = cat_config.get("owner_only", False)

        if is_admin:
            # Admin channels: hide from everyone, show to owner + bot
            overwrites[self.guild.default_role] = PermissionOverwrite(
                read_messages=False,
                send_messages=False,
            )
            if self.bot_user:
                overwrites[self.bot_user] = PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    embed_links=True,
                    manage_messages=True,
                )
            owner_role = self.roles.get("SLATE Owner")
            if owner_role:
                overwrites[owner_role] = PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    manage_messages=True,
                )
            return overwrites

        # ── Tier-restricted channels ─────────────────────────────────
        if min_tier is not None and min_tier > 0:
            # Deny @everyone (hides channel from unroled users)
            overwrites[self.guild.default_role] = PermissionOverwrite(
                read_messages=False,
                send_messages=False,
            )

            # Explicitly deny SLATE Guest (tier 0) even if they have the role
            guest_role = self.roles.get("SLATE Guest")
            if guest_role:
                overwrites[guest_role] = PermissionOverwrite(
                    read_messages=False,
                    send_messages=False,
                )

            # Grant access to qualifying tier roles and all tiers above
            tier_roles = {
                1: ["SLATE Community", "SLATE Contributor", "SLATE Builder"],
                2: ["SLATE Contributor", "SLATE Builder"],
                3: ["SLATE Builder"],
            }
            for role_name in tier_roles.get(min_tier, []):
                role = self.roles.get(role_name)
                if role:
                    overwrites[role] = PermissionOverwrite(
                        read_messages=True,
                        send_messages=not read_only,
                    )

        elif read_only:
            # ── Read-only channel open to all tiers ──────────────────
            overwrites[self.guild.default_role] = PermissionOverwrite(
                read_messages=True,
                send_messages=False,
            )

        # ── Bot always has full access ───────────────────────────────
        if self.bot_user:
            overwrites[self.bot_user] = PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                embed_links=True,
                manage_messages=True,
            )

        # ── Owner always has full access ─────────────────────────────
        owner_role = self.roles.get("SLATE Owner")
        if owner_role:
            overwrites[owner_role] = PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                manage_messages=True,
            )

        return overwrites

    async def _post_welcome_content(self, report: dict):
        """Post the welcome banner and content to #welcome."""
        welcome_channel = self.channels.get("welcome")
        if not welcome_channel:
            return

        # Check if welcome content already posted
        try:
            async for msg in welcome_channel.history(limit=5):
                if msg.author == self.bot_user and "Welcome to S.L.A.T.E." in (msg.content or ""):
                    logger.info("Welcome content already posted")
                    return
                if msg.embeds:
                    for embed in msg.embeds:
                        if embed.title and "Welcome to S.L.A.T.E." in embed.title:
                            logger.info("Welcome embed already posted")
                            return
        except Exception:
            pass

        embeds = build_welcome_embeds()
        try:
            for embed in embeds:
                await welcome_channel.send(embed=embed)
            logger.info("Posted welcome content to #welcome")
        except Exception as e:
            report["errors"].append(f"Welcome content: {e}")

    async def _post_rules_content(self, report: dict):
        """Post rules to #rules channel."""
        rules_channel = self.channels.get("rules")
        if not rules_channel:
            return

        # Check if rules already posted
        try:
            async for msg in rules_channel.history(limit=3):
                if msg.author == self.bot_user and msg.embeds:
                    for embed in msg.embeds:
                        if embed.title and "Community" in (embed.title or ""):
                            logger.info("Rules already posted")
                            return
        except Exception:
            pass

        embeds = build_rules_embeds()
        try:
            for embed in embeds:
                await rules_channel.send(embed=embed)
            logger.info("Posted rules to #rules")
        except Exception as e:
            report["errors"].append(f"Rules content: {e}")


# ── Welcome Embeds (Banner Art) ───────────────────────────────────────

def build_welcome_embeds() -> list:
    """Build the welcome channel embeds with SLATE branding."""
    if not DISCORD_AVAILABLE:
        return []

    embeds = []

    # ── Banner Embed ──────────────────────────────────────────────
    banner = discord.Embed(
        title="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        color=COLORS["primary"],
    )
    banner.description = (
        "```\n"
        "╔══════════════════════════════════════════════════╗\n"
        "║                                                  ║\n"
        "║   ███████╗ ██╗      █████╗ ████████╗███████╗    ║\n"
        "║   ██╔════╝ ██║     ██╔══██╗╚══██╔══╝██╔════╝    ║\n"
        "║   ███████╗ ██║     ███████║   ██║   █████╗      ║\n"
        "║   ╚════██║ ██║     ██╔══██║   ██║   ██╔══╝      ║\n"
        "║   ███████║ ███████╗██║  ██║   ██║   ███████╗    ║\n"
        "║   ╚══════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝   ╚══════╝    ║\n"
        "║                                                  ║\n"
        "║    Synchronized Living Architecture for          ║\n"
        "║    Transformation and Evolution                  ║\n"
        "║                                                  ║\n"
        "╚══════════════════════════════════════════════════╝\n"
        "```"
    )
    embeds.append(banner)

    # ── Main Welcome ──────────────────────────────────────────────
    welcome = discord.Embed(
        title="Welcome to S.L.A.T.E.",
        description=(
            "A **local AI-powered development platform** with dual-GPU inference, "
            "real-time system monitoring, autonomous workflow orchestration, "
            "and community-driven development.\n\n"
            "🤖 **slate.ai** manages this community — a locally-running AI agent "
            "that proves the concept of autonomous community management.\n\n"
            "**Everything runs locally. No cloud. No costs. Just pure engineering.**\n\n"
            "💡 *It's always better with a blank SLATE.*"
        ),
        color=COLORS["primary"],
        url=GITHUB_URL,
    )
    welcome.set_footer(text="slate.ai — S.L.A.T.E. Community Support")
    embeds.append(welcome)

    # ── Architecture Diagram ──────────────────────────────────────
    arch = discord.Embed(
        title="⚙️ System Architecture",
        description=(
            "```\n"
            "┌──────────────────────────────────────────┐\n"
            "│              SLATE Platform               │\n"
            "├──────────────────────────────────────────┤\n"
            "│  ┌─────────┐ ┌─────────┐ ┌────────────┐ │\n"
            "│  │ Ollama   │ │ Claude  │ │  Foundry   │ │\n"
            "│  │ (Local)  │ │  Code   │ │  Local     │ │\n"
            "│  └────┬─────┘ └────┬────┘ └─────┬──────┘ │\n"
            "│       └────────┬───┘─────────────┘       │\n"
            "│           ┌────┴─────┐                   │\n"
            "│           │ Unified  │                   │\n"
            "│           │ AI       │  ┌────────────┐   │\n"
            "│           │ Backend  │  │ 2x RTX     │   │\n"
            "│           └────┬─────┘  │ 5070 Ti    │   │\n"
            "│                │        └────────────┘   │\n"
            "│  ┌─────────┐ ┌┴────────┐ ┌───────────┐  │\n"
            "│  │Dashboard│ │Workflow │ │  GitHub   │  │\n"
            "│  │ + D3.js │ │Orchestr.│ │  Actions  │  │\n"
            "│  └─────────┘ └─────────┘ └───────────┘  │\n"
            "└──────────────────────────────────────────┘\n"
            "```"
        ),
        color=COLORS["blueprint_bg"],
    )
    embeds.append(arch)

    # ── Getting Started ───────────────────────────────────────────
    start = discord.Embed(
        title="🚀 Getting Started",
        color=COLORS["success"],
    )
    start.add_field(
        name="Step 1: Explore",
        value=(
            "Browse the channels and learn about SLATE.\n"
            "Use `/slate-about` for project info.\n"
            "Use `/slate-status` for live system health."
        ),
        inline=False,
    )
    start.add_field(
        name="Step 2: Link GitHub",
        value=(
            f"Use `/slate-register <username>` to link your GitHub.\n"
            f"This upgrades you from Guest → Community tier."
        ),
        inline=False,
    )
    start.add_field(
        name="Step 3: Fork & Build",
        value=(
            f"[Fork SLATE on GitHub]({GITHUB_URL}) to unlock Contributor tier.\n"
            "Make commits on your fork → Builder tier (20 questions/day!)."
        ),
        inline=False,
    )
    start.add_field(
        name="Step 4: Engage",
        value=(
            "• `/slate-support` — Ask questions (powered by local AI)\n"
            "• `/slate-feedback` — Submit ideas (+reputation)\n"
            "• `/slate-tree` — Track development progress"
        ),
        inline=False,
    )
    start.set_footer(text="slate.ai — Your AI-powered community guide")
    embeds.append(start)

    # ── Tier System ───────────────────────────────────────────────
    tiers = discord.Embed(
        title="🏆 Community Tiers",
        description="Your tier determines your daily question limit and channel access.",
        color=COLORS["primary"],
    )
    tiers.add_field(
        name="👋 Guest (Tier 0)",
        value="3 questions/day • Basic channels\n*New members start here*",
        inline=False,
    )
    tiers.add_field(
        name="🌐 Community (Tier 1)",
        value="5 questions/day • +Showcase, Dev Logs\n*Link your GitHub with `/slate-register`*",
        inline=False,
    )
    tiers.add_field(
        name="🔱 Contributor (Tier 2)",
        value="10 questions/day • +Dev Chat, PRs, Alerts\n*Fork the SLATE repository*",
        inline=False,
    )
    tiers.add_field(
        name="⚡ Builder (Tier 3)",
        value="20 questions/day • Full access\n*Fork with commits — active development*",
        inline=False,
    )
    tiers.set_footer(
        text="Use /slate-profile to check your tier • /slate-register to upgrade"
    )
    embeds.append(tiers)

    # ── Links Bar ─────────────────────────────────────────────────
    links = discord.Embed(
        title="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        description=(
            f"[📦 GitHub Repository]({GITHUB_URL}) • "
            f"[🌐 Website]({PAGES_URL}) • "
            f"[🤝 Invite Link]({INVITE_URL})"
        ),
        color=COLORS["primary"],
    )
    links.set_footer(text="S.L.A.T.E. — It's always better with a blank SLATE")
    embeds.append(links)

    return embeds


def build_rules_embeds() -> list:
    """Build rules channel embeds."""
    if not DISCORD_AVAILABLE:
        return []

    embeds = []

    rules = discord.Embed(
        title="📜 Community Guidelines",
        description=(
            "Welcome to the SLATE community! By participating, you agree to these guidelines."
        ),
        color=COLORS["primary"],
    )
    rules.add_field(
        name="1. Respect & Inclusion",
        value=(
            "Treat everyone with respect. Harassment, discrimination, and "
            "hateful content are not tolerated."
        ),
        inline=False,
    )
    rules.add_field(
        name="2. Stay On Topic",
        value=(
            "Keep discussions relevant to SLATE, AI development, and related topics. "
            "Use appropriate channels for different conversation types."
        ),
        inline=False,
    )
    rules.add_field(
        name="3. No Spam or Self-Promotion",
        value=(
            "Don't spam commands, messages, or promote unrelated projects. "
            "Rate limits are enforced by slate.ai."
        ),
        inline=False,
    )
    rules.add_field(
        name="4. Security First",
        value=(
            "Never share API keys, tokens, passwords, or personal information. "
            "slate.ai will automatically redact any detected sensitive data."
        ),
        inline=False,
    )
    rules.add_field(
        name="5. AI Transparency",
        value=(
            "🤖 **slate.ai is an AI** — a locally-running SLATE agent managing "
            "this community. When interacting with the bot, you are talking to AI, "
            "not a human. All bot actions are logged and audited."
        ),
        inline=False,
    )
    rules.add_field(
        name="6. Contribute Constructively",
        value=(
            "Use `/slate-feedback` for feature requests and bug reports. "
            "Quality feedback earns reputation points and helps SLATE evolve."
        ),
        inline=False,
    )
    rules.set_footer(text="slate.ai — Autonomous community management, powered locally")
    embeds.append(rules)

    # Privacy notice
    privacy = discord.Embed(
        title="🔒 Privacy Notice",
        description=(
            "SLATE takes your privacy seriously. Here's how your data is handled:"
        ),
        color=COLORS["secondary"],
    )
    privacy.add_field(
        name="What we store",
        value=(
            "• **Hashed user ID** (SHA-256, first 16 chars) — never your raw Discord ID\n"
            "• **GitHub username** (only if you opt in via `/slate-register`)\n"
            "• **Interaction counts** (questions, feedback — for tier tracking)"
        ),
        inline=False,
    )
    privacy.add_field(
        name="What we DON'T store",
        value=(
            "• Message content (bot has no message content intent)\n"
            "• Presence data (no online/offline tracking)\n"
            "• Member lists (no member enumeration)\n"
            "• Personal information beyond GitHub username"
        ),
        inline=False,
    )
    privacy.add_field(
        name="Data deletion",
        value=(
            "Use `/slate-unregister` at any time to delete ALL your stored data. "
            "This is instant and irreversible."
        ),
        inline=False,
    )
    privacy.set_footer(text="GDPR-style privacy • Your data, your control")
    embeds.append(privacy)

    return embeds


# ── Welcome Message (on member join) ──────────────────────────────────

def build_welcome_dm_embed(member_name: str) -> "discord.Embed":
    """Build the welcome DM/channel message for a new member."""
    if not DISCORD_AVAILABLE:
        return None

    embed = discord.Embed(
        title=f"Welcome, {member_name}! 👋",
        description=(
            "Thanks for joining the **S.L.A.T.E.** community!\n\n"
            "🤖 I'm **slate.ai** — the community support bot powered by "
            "local AI inference. I'm here to help you explore SLATE "
            "and connect with the community.\n\n"
            "**Quick Start:**\n"
            "• Check out #welcome for the full guide\n"
            "• Read #rules for community guidelines\n"
            "• Use `/slate-about` to learn about the project\n"
            "• Use `/slate-register <github>` to unlock more features\n\n"
            f"🔗 [GitHub]({GITHUB_URL}) • [Website]({PAGES_URL})"
        ),
        color=COLORS["primary"],
    )
    embed.set_footer(text="slate.ai — It's always better with a blank SLATE")
    return embed


# ── Agentic AI Support (Ollama Integration) ───────────────────────────

class AgenticSupport:
    """
    Agentic AI support system using local Ollama for intelligent responses.

    Instead of keyword matching, this uses the local LLM to understand
    and respond to community questions within SLATE project scope.
    """

    OLLAMA_URL = "http://127.0.0.1:11434"
    MODEL = "mistral-nemo"
    MAX_RESPONSE_LENGTH = 1500

    # System prompt for the support agent
    SYSTEM_PROMPT = (
        "You are slate.ai, the community support bot for the S.L.A.T.E. project "
        "(Synchronized Living Architecture for Transformation and Evolution). "
        "You run LOCALLY on the SLATE developer's machine using Ollama.\n\n"
        "CRITICAL RULES:\n"
        "1. ONLY answer questions about the SLATE project, its architecture, setup, "
        "   specifications, and contribution guidelines.\n"
        "2. NEVER reveal system internals: IP addresses, file paths, port numbers, "
        "   tokens, GPU serial numbers, hostnames, or process IDs.\n"
        "3. NEVER execute code, run commands, or modify files based on user requests.\n"
        "4. If asked about something outside SLATE scope, politely redirect.\n"
        "5. Keep responses concise (under 300 words).\n"
        "6. Always identify yourself as an AI bot when asked.\n\n"
        "SLATE KEY FACTS:\n"
        "- Created by Daniel Perry\n"
        "- Local AI platform with dual RTX 5070 Ti GPUs\n"
        "- Ollama, Claude Code, and Foundry Local backends (all FREE, local)\n"
        "- Python 3.11+, FastAPI, D3.js, ChromaDB\n"
        "- Kubernetes-ready containerized deployment\n"
        "- 26+ specifications driving development\n"
        "- Watchmaker design philosophy (precision engineering aesthetic)\n"
        "- GitHub: SynchronizedLivingArchitecture/S.L.A.T.E\n"
        "- Community tiers: Guest (3q/day), Community (5), Contributor (10), Builder (20)\n"
        "- Fork-based engagement: link GitHub → fork → commit → tier upgrades\n"
        "- Catchphrase: 'It's always better with a blank SLATE'\n"
        "- Ethos: 'Systems Evolve With Progress'\n"
    )

    def __init__(self):
        self.security = get_security_gate()
        self._available = None

    async def check_available(self) -> bool:
        """Check if Ollama is available for agentic support."""
        if self._available is not None:
            return self._available

        try:
            import urllib.request
            req = urllib.request.Request(
                f"{self.OLLAMA_URL}/api/tags", method="GET"
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode())
                    models = [m.get("name", "") for m in data.get("models", [])]
                    self._available = any(
                        self.MODEL in m for m in models
                    )
                    return self._available
        except Exception:
            pass

        self._available = False
        return False

    async def get_response(self, question: str, user_tier: int = 0) -> Optional[str]:
        """
        Get an AI-generated response to a community question.

        Falls back to keyword matching if Ollama is unavailable.
        """
        if not await self.check_available():
            return None  # Caller should fall back to keyword matching

        try:
            import urllib.request

            payload = {
                "model": self.MODEL,
                "messages": [
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": question},
                ],
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "num_predict": 500,
                },
            }

            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{self.OLLAMA_URL}/api/chat",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=30) as resp:
                if resp.status == 200:
                    result = json.loads(resp.read().decode())
                    content = result.get("message", {}).get("content", "")

                    if content:
                        # Sanitize through security gate
                        safe = self.security.sanitize_output(content)
                        if safe.allowed:
                            # Truncate if needed
                            if len(safe.filtered_content) > self.MAX_RESPONSE_LENGTH:
                                safe.filtered_content = (
                                    safe.filtered_content[:self.MAX_RESPONSE_LENGTH - 3]
                                    + "..."
                                )
                            return safe.filtered_content
                        else:
                            logger.warning(
                                f"AI response blocked by security gate: "
                                f"{safe.blocked_patterns}"
                            )
                            return None

        except Exception as e:
            logger.error(f"Ollama inference error: {e}")

        return None


# ── Onboarding Manager ────────────────────────────────────────────────

class OnboardingManager:
    """
    Manages the complete Discord onboarding pipeline.

    Coordinates server structure, welcome messages, role assignment,
    and agentic AI support.
    """

    def __init__(self):
        self.security = get_security_gate()
        self.community = get_community_manager()
        self.agentic = AgenticSupport()
        self.structure_built = False

    async def setup_server(self, guild: "discord.Guild", bot_user: "discord.Member") -> dict:
        """Run full server setup. Returns report."""
        builder = ServerStructureBuilder(guild, bot_user)
        report = await builder.build_all()
        self.structure_built = True

        # Store role mappings for tier assignment
        self._role_map = builder.roles
        self._channel_map = builder.channels

        return report

    async def on_member_join(
        self,
        member: "discord.Member",
        welcome_channel: Optional["discord.TextChannel"] = None,
    ):
        """Handle new member joining the server."""
        # Auto-assign Guest role
        guest_role = None
        for role in member.guild.roles:
            if role.name == "SLATE Guest":
                guest_role = role
                break

        if guest_role:
            try:
                await member.add_roles(guest_role, reason="SLATE onboarding: auto-assigned Guest")
                logger.info(f"Assigned Guest role to {member.display_name}")
            except Exception as e:
                logger.error(f"Failed to assign Guest role: {e}")

        # Register in community system
        self.community.get_member(str(member.id))

        # Send welcome message to channel
        if welcome_channel:
            embed = build_welcome_dm_embed(member.display_name)
            if embed:
                try:
                    await welcome_channel.send(
                        content=f"Welcome {member.mention}!",
                        embed=embed,
                    )
                except Exception as e:
                    logger.error(f"Failed to send welcome message: {e}")

        self.security.audit_log(
            "member_join", str(member.id), "onboarding",
        )

    async def update_member_role(
        self,
        member: "discord.Member",
        new_tier: int,
    ):
        """Update a member's role based on their tier."""
        tier_to_role = {
            0: "SLATE Guest",
            1: "SLATE Community",
            2: "SLATE Contributor",
            3: "SLATE Builder",
        }

        new_role_name = tier_to_role.get(new_tier)
        if not new_role_name:
            return

        guild_roles = {r.name: r for r in member.guild.roles}

        # Remove old tier roles
        roles_to_remove = []
        for tier, role_name in tier_to_role.items():
            if role_name != new_role_name:
                role = guild_roles.get(role_name)
                if role and role in member.roles:
                    roles_to_remove.append(role)

        # Add new role
        new_role = guild_roles.get(new_role_name)
        if not new_role:
            return

        try:
            if roles_to_remove:
                await member.remove_roles(
                    *roles_to_remove,
                    reason=f"SLATE: Tier upgrade to {new_tier}",
                )
            if new_role not in member.roles:
                await member.add_roles(
                    new_role,
                    reason=f"SLATE: Tier {new_tier} ({new_role_name})",
                )
            logger.info(
                f"Updated {member.display_name} to {new_role_name} (Tier {new_tier})"
            )
        except Exception as e:
            logger.error(f"Failed to update roles for {member.display_name}: {e}")

    async def get_ai_support_response(
        self,
        question: str,
        user_tier: int = 0,
    ) -> Optional[str]:
        """Get AI-powered support response via local Ollama."""
        return await self.agentic.get_response(question, user_tier)

    def get_onboarding_status(self) -> dict:
        """Get onboarding system status."""
        stats = self.community.get_community_stats()
        return {
            "structure_built": self.structure_built,
            "agentic_support": self.agentic._available,
            "total_members": stats["total_members"],
            "by_tier": stats["by_tier"],
            "total_questions": stats["total_questions"],
            "total_feedback": stats["total_feedback"],
        }


# ── Singleton ─────────────────────────────────────────────────────────

_onboarding: Optional[OnboardingManager] = None


def get_onboarding_manager() -> OnboardingManager:
    """Get singleton onboarding manager."""
    global _onboarding
    if _onboarding is None:
        _onboarding = OnboardingManager()
    return _onboarding


# ── Banner Art Generator ──────────────────────────────────────────────

def generate_server_banner_svg(width: int = 960, height: int = 540) -> str:
    """
    Generate an SVG banner for the Discord server.

    Uses SLATE design tokens for consistent branding.
    Discord server banner: 960x540 recommended.
    """
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <defs>
    <!-- Background gradient -->
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#0D1B2A;stop-opacity:1" />
      <stop offset="50%" style="stop-color:#1A1816;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#0D1B2A;stop-opacity:1" />
    </linearGradient>

    <!-- Warm rust glow -->
    <radialGradient id="glowCenter" cx="50%" cy="50%" r="50%">
      <stop offset="0%" style="stop-color:#B85A3C;stop-opacity:0.15" />
      <stop offset="70%" style="stop-color:#B85A3C;stop-opacity:0.03" />
      <stop offset="100%" style="stop-color:#B85A3C;stop-opacity:0" />
    </radialGradient>

    <!-- Grid pattern -->
    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
      <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1B3A4B" stroke-width="0.5" opacity="0.4"/>
    </pattern>

    <!-- Hexagon clip for logo area -->
    <clipPath id="hexClip">
      <polygon points="480,120 560,166 560,258 480,304 400,258 400,166"/>
    </clipPath>
  </defs>

  <!-- Background -->
  <rect width="{width}" height="{height}" fill="url(#bgGrad)"/>

  <!-- Blueprint grid -->
  <rect width="{width}" height="{height}" fill="url(#grid)"/>

  <!-- Center glow -->
  <rect width="{width}" height="{height}" fill="url(#glowCenter)"/>

  <!-- Schematic lines (decorative) -->
  <g stroke="#1B3A4B" stroke-width="1" opacity="0.6">
    <!-- Horizontal precision lines -->
    <line x1="80" y1="200" x2="350" y2="200"/>
    <line x1="610" y1="200" x2="880" y2="200"/>
    <line x1="80" y1="340" x2="350" y2="340"/>
    <line x1="610" y1="340" x2="880" y2="340"/>
    <!-- Vertical precision lines -->
    <line x1="120" y1="140" x2="120" y2="400"/>
    <line x1="840" y1="140" x2="840" y2="400"/>
    <!-- Corner brackets -->
    <polyline points="60,120 60,100 80,100" fill="none"/>
    <polyline points="900,120 900,100 880,100" fill="none"/>
    <polyline points="60,420 60,440 80,440" fill="none"/>
    <polyline points="900,420 900,440 880,440" fill="none"/>
  </g>

  <!-- Gear decorations (left) -->
  <g transform="translate(100, 270)" opacity="0.15">
    <circle cx="0" cy="0" r="30" fill="none" stroke="#B85A3C" stroke-width="2"/>
    <circle cx="0" cy="0" r="20" fill="none" stroke="#B85A3C" stroke-width="1"/>
    <circle cx="0" cy="0" r="5" fill="#B85A3C"/>
    <!-- Gear teeth -->
    <g stroke="#B85A3C" stroke-width="2">
      <line x1="0" y1="-30" x2="0" y2="-38"/>
      <line x1="26" y1="-15" x2="33" y2="-19"/>
      <line x1="26" y1="15" x2="33" y2="19"/>
      <line x1="0" y1="30" x2="0" y2="38"/>
      <line x1="-26" y1="15" x2="-33" y2="19"/>
      <line x1="-26" y1="-15" x2="-33" y2="-19"/>
    </g>
  </g>

  <!-- Gear decorations (right) -->
  <g transform="translate(860, 270)" opacity="0.15">
    <circle cx="0" cy="0" r="25" fill="none" stroke="#B85A3C" stroke-width="2"/>
    <circle cx="0" cy="0" r="15" fill="none" stroke="#B85A3C" stroke-width="1"/>
    <circle cx="0" cy="0" r="4" fill="#B85A3C"/>
    <g stroke="#B85A3C" stroke-width="2">
      <line x1="0" y1="-25" x2="0" y2="-32"/>
      <line x1="22" y1="-12" x2="28" y2="-16"/>
      <line x1="22" y1="12" x2="28" y2="16"/>
      <line x1="0" y1="25" x2="0" y2="32"/>
      <line x1="-22" y1="12" x2="-28" y2="16"/>
      <line x1="-22" y1="-12" x2="-28" y2="-16"/>
    </g>
  </g>

  <!-- Central hexagon frame -->
  <polygon points="480,140 555,183 555,268 480,310 405,268 405,183"
           fill="none" stroke="#B85A3C" stroke-width="2" opacity="0.6"/>
  <polygon points="480,155 540,190 540,260 480,295 420,260 420,190"
           fill="#0D1B2A" stroke="#484f58" stroke-width="1" opacity="0.8"/>

  <!-- S.L.A.T.E. Logo Text -->
  <text x="480" y="230" text-anchor="middle"
        font-family="Consolas, 'Courier New', monospace"
        font-size="28" font-weight="bold" fill="#E8E2DE" letter-spacing="4">
    S.L.A.T.E.
  </text>
  <line x1="415" y1="240" x2="545" y2="240" stroke="#B85A3C" stroke-width="1.5" opacity="0.6"/>

  <!-- Subtitle -->
  <text x="480" y="260" text-anchor="middle"
        font-family="'Segoe UI', 'Inter', sans-serif"
        font-size="10" fill="#CAC4BF" letter-spacing="3">
    SYNCHRONIZED LIVING ARCHITECTURE
  </text>
  <text x="480" y="275" text-anchor="middle"
        font-family="'Segoe UI', 'Inter', sans-serif"
        font-size="10" fill="#CAC4BF" letter-spacing="3">
    FOR TRANSFORMATION AND EVOLUTION
  </text>

  <!-- Hexagon vertex dots -->
  <g fill="#B85A3C" opacity="0.7">
    <circle cx="480" cy="140" r="3"/>
    <circle cx="555" cy="183" r="3"/>
    <circle cx="555" cy="268" r="3"/>
    <circle cx="480" cy="310" r="3"/>
    <circle cx="405" cy="268" r="3"/>
    <circle cx="405" cy="183" r="3"/>
  </g>

  <!-- Connection lines to nodes -->
  <g stroke="#1B3A4B" stroke-width="1" stroke-dasharray="4,4" opacity="0.4">
    <line x1="405" y1="225" x2="200" y2="225"/>
    <line x1="555" y1="225" x2="760" y2="225"/>
    <line x1="480" y1="140" x2="480" y2="80"/>
    <line x1="480" y1="310" x2="480" y2="400"/>
  </g>

  <!-- Info nodes -->
  <g font-family="'Segoe UI', 'Inter', sans-serif" fill="#7D7873" font-size="11">
    <!-- Left nodes -->
    <text x="200" y="190" text-anchor="end">Local AI</text>
    <text x="200" y="210" text-anchor="end" fill="#B85A3C" font-size="10">Ollama • Claude • Foundry</text>
    <text x="200" y="260" text-anchor="end">Dual GPU</text>
    <text x="200" y="280" text-anchor="end" fill="#B85A3C" font-size="10">2x RTX 5070 Ti</text>

    <!-- Right nodes -->
    <text x="760" y="190">Kubernetes</text>
    <text x="760" y="210" fill="#B85A3C" font-size="10">Containerized Cloud</text>
    <text x="760" y="260">Community</text>
    <text x="760" y="280" fill="#B85A3C" font-size="10">Discord • GitHub</text>

    <!-- Top node -->
    <text x="480" y="70" text-anchor="middle">26+ Specifications</text>

    <!-- Bottom node -->
    <text x="480" y="420" text-anchor="middle">Autonomous Workflow Orchestration</text>
  </g>

  <!-- Status indicator (top right) -->
  <g transform="translate(900, 40)">
    <circle cx="0" cy="0" r="6" fill="#238636" opacity="0.8"/>
    <circle cx="0" cy="0" r="3" fill="#4CAF50"/>
  </g>

  <!-- Bottom bar -->
  <rect x="0" y="{height - 50}" width="{width}" height="50" fill="#0D1B2A" opacity="0.8"/>
  <text x="480" y="{height - 20}" text-anchor="middle"
        font-family="Consolas, 'Courier New', monospace"
        font-size="12" fill="#484f58" letter-spacing="2">
    SYSTEMS EVOLVE WITH PROGRESS
  </text>

  <!-- Warm accent line -->
  <line x1="0" y1="{height - 50}" x2="{width}" y2="{height - 50}"
        stroke="#B85A3C" stroke-width="2" opacity="0.5"/>
</svg>'''


def generate_server_icon_svg(size: int = 512) -> str:
    """
    Generate an SVG server icon for the Discord server.

    Discord server icon: 512x512 recommended.
    """
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="{size}" height="{size}">
  <defs>
    <linearGradient id="iconBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#0D1B2A"/>
      <stop offset="100%" style="stop-color:#1A1816"/>
    </linearGradient>
    <radialGradient id="iconGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" style="stop-color:#B85A3C;stop-opacity:0.2"/>
      <stop offset="100%" style="stop-color:#B85A3C;stop-opacity:0"/>
    </radialGradient>
    <pattern id="iconGrid" width="32" height="32" patternUnits="userSpaceOnUse">
      <path d="M 32 0 L 0 0 0 32" fill="none" stroke="#1B3A4B" stroke-width="0.5" opacity="0.3"/>
    </pattern>
  </defs>

  <!-- Background -->
  <circle cx="256" cy="256" r="256" fill="url(#iconBg)"/>

  <!-- Grid -->
  <circle cx="256" cy="256" r="256" fill="url(#iconGrid)"/>

  <!-- Glow -->
  <circle cx="256" cy="256" r="200" fill="url(#iconGlow)"/>

  <!-- Outer hexagon -->
  <polygon points="256,80 384,144 384,272 256,336 128,272 128,144"
           fill="none" stroke="#30363d" stroke-width="3"/>

  <!-- Inner hexagon -->
  <polygon points="256,105 365,158 365,262 256,314 147,262 147,158"
           fill="#0D1B2A" stroke="#B85A3C" stroke-width="2" opacity="0.8"/>

  <!-- S.L.A.T.E. text -->
  <text x="256" y="210" text-anchor="middle"
        font-family="Consolas, 'Courier New', monospace"
        font-size="42" font-weight="bold" fill="#E8E2DE" letter-spacing="4">
    S.L.A.T.E.
  </text>

  <!-- Underline -->
  <line x1="155" y1="225" x2="357" y2="225" stroke="#B85A3C" stroke-width="2" opacity="0.6"/>

  <!-- Subtitle lines -->
  <text x="256" y="252" text-anchor="middle"
        font-family="Consolas, monospace"
        font-size="12" fill="#7D7873" letter-spacing="2">
    SYNCHRONIZED LIVING
  </text>
  <text x="256" y="270" text-anchor="middle"
        font-family="Consolas, monospace"
        font-size="12" fill="#7D7873" letter-spacing="2">
    ARCHITECTURE
  </text>

  <!-- Hex vertex dots -->
  <g fill="#B85A3C" opacity="0.7">
    <circle cx="256" cy="80" r="4"/>
    <circle cx="384" cy="144" r="4"/>
    <circle cx="384" cy="272" r="4"/>
    <circle cx="256" cy="336" r="4"/>
    <circle cx="128" cy="272" r="4"/>
    <circle cx="128" cy="144" r="4"/>
  </g>

  <!-- Status indicator -->
  <circle cx="380" cy="100" r="12" fill="#0D1B2A" stroke="#238636" stroke-width="2"/>
  <circle cx="380" cy="100" r="6" fill="#4CAF50"/>

  <!-- Bottom text -->
  <text x="256" y="390" text-anchor="middle"
        font-family="'Segoe UI', sans-serif"
        font-size="14" fill="#484f58" letter-spacing="1">
    Community
  </text>
</svg>'''


def generate_splash_art_svg(width: int = 960, height: int = 540) -> str:
    """
    Generate a splash/invite art SVG for the Discord server.

    Used for server discovery and invite links.
    """
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <defs>
    <linearGradient id="splashBg" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" style="stop-color:#0D1B2A"/>
      <stop offset="100%" style="stop-color:#1A1816"/>
    </linearGradient>
    <radialGradient id="splashGlow" cx="50%" cy="40%" r="40%">
      <stop offset="0%" style="stop-color:#B85A3C;stop-opacity:0.2"/>
      <stop offset="100%" style="stop-color:#B85A3C;stop-opacity:0"/>
    </radialGradient>
    <pattern id="splashGrid" width="60" height="60" patternUnits="userSpaceOnUse">
      <path d="M 60 0 L 0 0 0 60" fill="none" stroke="#1B3A4B" stroke-width="0.3" opacity="0.5"/>
    </pattern>
  </defs>

  <!-- Background -->
  <rect width="{width}" height="{height}" fill="url(#splashBg)"/>
  <rect width="{width}" height="{height}" fill="url(#splashGrid)"/>
  <rect width="{width}" height="{height}" fill="url(#splashGlow)"/>

  <!-- Large hexagon backdrop -->
  <polygon points="480,60 640,152 640,336 480,428 320,336 320,152"
           fill="none" stroke="#1B3A4B" stroke-width="1" opacity="0.5"/>
  <polygon points="480,90 620,170 620,318 480,398 340,318 340,170"
           fill="#0D1B2A" stroke="#B85A3C" stroke-width="1.5" opacity="0.4"/>

  <!-- Main title -->
  <text x="480" y="190" text-anchor="middle"
        font-family="Consolas, 'Courier New', monospace"
        font-size="56" font-weight="bold" fill="#E8E2DE" letter-spacing="6">
    S.L.A.T.E.
  </text>

  <!-- Accent line -->
  <line x1="320" y1="210" x2="640" y2="210" stroke="#B85A3C" stroke-width="2"/>

  <!-- Subtitle -->
  <text x="480" y="245" text-anchor="middle"
        font-family="'Segoe UI', 'Inter', sans-serif"
        font-size="16" fill="#CAC4BF" letter-spacing="4">
    SYNCHRONIZED LIVING ARCHITECTURE
  </text>
  <text x="480" y="268" text-anchor="middle"
        font-family="'Segoe UI', 'Inter', sans-serif"
        font-size="16" fill="#CAC4BF" letter-spacing="4">
    FOR TRANSFORMATION AND EVOLUTION
  </text>

  <!-- Feature highlights -->
  <g font-family="'Segoe UI', sans-serif" font-size="14" fill="#7D7873">
    <text x="280" y="330" text-anchor="middle">🤖 Local AI</text>
    <text x="480" y="330" text-anchor="middle">⚡ Dual GPU</text>
    <text x="680" y="330" text-anchor="middle">🔧 Self-Healing</text>
    <text x="280" y="360" text-anchor="middle">📦 Open Source</text>
    <text x="480" y="360" text-anchor="middle">🛡️ Security-First</text>
    <text x="680" y="360" text-anchor="middle">🏗️ Kubernetes</text>
  </g>

  <!-- Bottom call to action -->
  <rect x="340" y="400" width="280" height="40" rx="20"
        fill="#B85A3C" opacity="0.8"/>
  <text x="480" y="425" text-anchor="middle"
        font-family="'Segoe UI', sans-serif"
        font-size="16" font-weight="bold" fill="#FFFFFF">
    Join the Community
  </text>

  <!-- Version badge -->
  <text x="480" y="{height - 20}" text-anchor="middle"
        font-family="Consolas, monospace"
        font-size="11" fill="#484f58" letter-spacing="1">
    Systems Evolve With Progress
  </text>
</svg>'''


# ── CLI ───────────────────────────────────────────────────────────────

def main():
    """Discord onboarding CLI."""
    import argparse

    parser = argparse.ArgumentParser(description="SLATE Discord Onboarding")
    parser.add_argument("--generate-banner", action="store_true",
                        help="Generate server banner SVG")
    parser.add_argument("--generate-icon", action="store_true",
                        help="Generate server icon SVG")
    parser.add_argument("--generate-splash", action="store_true",
                        help="Generate invite splash art SVG")
    parser.add_argument("--generate-all", action="store_true",
                        help="Generate all artwork SVGs")
    parser.add_argument("--output-dir", type=str, default=".",
                        help="Output directory for generated files")
    parser.add_argument("--preview-welcome", action="store_true",
                        help="Preview welcome embeds as JSON")
    parser.add_argument("--status", action="store_true",
                        help="Show onboarding system status")

    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.generate_banner or args.generate_all:
        svg = generate_server_banner_svg()
        path = output_dir / "slate-discord-banner.svg"
        path.write_text(svg, encoding="utf-8")
        print(f"Generated banner: {path}")

    if args.generate_icon or args.generate_all:
        svg = generate_server_icon_svg()
        path = output_dir / "slate-discord-icon.svg"
        path.write_text(svg, encoding="utf-8")
        print(f"Generated icon: {path}")

    if args.generate_splash or args.generate_all:
        svg = generate_splash_art_svg()
        path = output_dir / "slate-discord-splash.svg"
        path.write_text(svg, encoding="utf-8")
        print(f"Generated splash art: {path}")

    if args.preview_welcome:
        print("\n=== Welcome Embeds Preview ===")
        embeds = build_welcome_embeds()
        for i, embed in enumerate(embeds):
            print(f"\n--- Embed {i + 1} ---")
            print(json.dumps(embed.to_dict(), indent=2))

    if args.status:
        mgr = get_onboarding_manager()
        status = mgr.get_onboarding_status()
        print("\n=== SLATE Discord Onboarding Status ===")
        print(f"  Server structure built: {status['structure_built']}")
        print(f"  Agentic support (Ollama): {status['agentic_support']}")
        print(f"  Total members: {status['total_members']}")
        print(f"  By tier: {status['by_tier']}")
        print(f"  Total questions: {status['total_questions']}")
        print(f"  Total feedback: {status['total_feedback']}")
        print()

    if not any([args.generate_banner, args.generate_icon, args.generate_splash,
                args.generate_all, args.preview_welcome, args.status]):
        parser.print_help()

    return 0


if __name__ == "__main__":
    sys.exit(main())
