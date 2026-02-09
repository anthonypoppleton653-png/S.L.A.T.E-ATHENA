#!/usr/bin/env python3
"""
SLATE Discord Integration
===========================

Provides Discord webhook-based notifications and slash command stubs for
SLATE system events. Uses webhook URLs (no bot token required) for
zero-dependency notification delivery.

Architecture:
  SLATE Events -> Notification System -> Discord Webhooks

  Workflow completion -> #slate-builds
  Service health     -> #slate-status
  Tech tree progress -> #slate-progress
  Error alerts       -> #slate-alerts

Webhook Mode (current):
  - No discord.py dependency needed
  - Uses standard urllib for HTTP POST
  - Embeds with SLATE brand colors and formatting
  - Rate-limited to prevent Discord API throttling

Bot Mode (future):
  - Requires discord.py/py-cord
  - Slash commands: /slate-status, /slate-tree, /slate-deploy
  - Real-time service health monitoring
  - Interactive tech tree visualization
"""
# Modified: 2026-02-09T22:00:00Z | Author: Claude Opus 4.6 | Change: Create Discord integration module

import json
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
CONFIG_DIR = WORKSPACE_ROOT / ".slate_identity"
DISCORD_CONFIG = CONFIG_DIR / "discord_config.json"

# SLATE brand colors for Discord embeds
EMBED_COLORS = {
    "primary": 0xB85A3C,    # Warm rust
    "success": 0x4CAF50,    # Green
    "warning": 0xFF9800,    # Orange
    "error":   0xF44336,    # Red
    "info":    0x2196F3,    # Blue
    "neutral": 0x5D5D74,    # Secondary gray-purple
}

# Rate limiting
_last_send: dict[str, float] = {}
RATE_LIMIT_SECONDS = 5  # Min seconds between messages per channel


# ── Data Classes ───────────────────────────────────────────────────────

@dataclass
class DiscordEmbed:
    """Discord webhook embed message."""
    title: str
    description: str = ""
    color: int = EMBED_COLORS["primary"]
    fields: list = field(default_factory=list)
    footer: str = ""
    timestamp: str = ""
    url: str = ""
    thumbnail_url: str = ""

    def to_dict(self) -> dict:
        embed = {
            "title": self.title,
            "color": self.color,
        }
        if self.description:
            embed["description"] = self.description
        if self.fields:
            embed["fields"] = self.fields
        if self.footer:
            embed["footer"] = {"text": self.footer}
        if self.timestamp:
            embed["timestamp"] = self.timestamp
        else:
            embed["timestamp"] = datetime.now(timezone.utc).isoformat()
        if self.url:
            embed["url"] = self.url
        if self.thumbnail_url:
            embed["thumbnail"] = {"url": self.thumbnail_url}
        return embed

    def add_field(self, name: str, value: str, inline: bool = True):
        """Add a field to the embed."""
        self.fields.append({"name": name, "value": value, "inline": inline})


@dataclass
class DiscordConfig:
    """Discord webhook configuration."""
    webhooks: dict = field(default_factory=dict)  # channel_name -> webhook_url
    enabled: bool = False
    application_id: str = ""
    application_name: str = ""
    server_name: str = ""
    port: int = 8086
    notification_channels: dict = field(default_factory=dict)  # event_type -> channel_name

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "application_id": self.application_id,
            "application_name": self.application_name,
            "server_name": self.server_name,
            "port": self.port,
            "webhooks": {k: "***configured***" for k in self.webhooks},  # Never expose URLs
            "notification_channels": self.notification_channels,
        }


@dataclass
class SendResult:
    """Result of a webhook send operation."""
    success: bool
    channel: str
    status_code: int = 0
    error: str = ""
    rate_limited: bool = False


# ── Discord Client ─────────────────────────────────────────────────────

class SlateDiscord:
    """SLATE Discord integration via webhooks."""

    def __init__(self):
        self.config = self._load_config()

    def _load_config(self) -> DiscordConfig:
        """Load Discord configuration."""
        config = DiscordConfig()

        # Load from config file
        if DISCORD_CONFIG.exists():
            try:
                data = json.loads(DISCORD_CONFIG.read_text(encoding="utf-8"))
                config.enabled = data.get("enabled", False)
                config.application_id = data.get("application_id", "")
                config.application_name = data.get("application_name", "")
                config.server_name = data.get("server_name", "")
                config.port = data.get("port", 8086)
                config.webhooks = data.get("webhooks", {})
                config.notification_channels = data.get("notification_channels", {})
            except Exception:
                pass

        # Override application ID from environment
        env_app_id = os.environ.get("DISCORD_APP_ID", "")
        if env_app_id:
            config.application_id = env_app_id
        env_port = os.environ.get("DISCORD_PORT", "")
        if env_port:
            config.port = int(env_port)

        # Override from environment variables
        for key, value in os.environ.items():
            if key.startswith("SLATE_DISCORD_WEBHOOK_"):
                channel = key[len("SLATE_DISCORD_WEBHOOK_"):].lower()
                config.webhooks[channel] = value
                config.enabled = True

        # Default channel routing
        if not config.notification_channels:
            config.notification_channels = {
                "build": "builds",
                "deploy": "builds",
                "health": "status",
                "error": "alerts",
                "progress": "progress",
                "workflow": "builds",
                "tech_tree": "progress",
            }

        return config

    def save_config(self):
        """Save config (without webhook URLs for security)."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "enabled": self.config.enabled,
            "server_name": self.config.server_name,
            "notification_channels": self.config.notification_channels,
            # Webhooks stored separately or via env vars
        }
        DISCORD_CONFIG.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _get_webhook_url(self, channel: str) -> Optional[str]:
        """Get webhook URL for a channel."""
        return self.config.webhooks.get(channel)

    def _check_rate_limit(self, channel: str) -> bool:
        """Check if we're rate-limited for this channel."""
        now = time.time()
        last = _last_send.get(channel, 0)
        if now - last < RATE_LIMIT_SECONDS:
            return True
        _last_send[channel] = now
        return False

    def send_embed(self, channel: str, embed: DiscordEmbed, username: str = "SLATE") -> SendResult:
        """Send an embed to a Discord channel via webhook."""
        if not self.config.enabled:
            return SendResult(success=False, channel=channel, error="Discord notifications disabled")

        webhook_url = self._get_webhook_url(channel)
        if not webhook_url:
            return SendResult(success=False, channel=channel, error=f"No webhook configured for #{channel}")

        if self._check_rate_limit(channel):
            return SendResult(success=False, channel=channel, rate_limited=True, error="Rate limited")

        payload = {
            "username": username,
            "embeds": [embed.to_dict()],
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                webhook_url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return SendResult(success=True, channel=channel, status_code=resp.status)
        except urllib.error.HTTPError as e:
            return SendResult(success=False, channel=channel, status_code=e.code, error=str(e))
        except Exception as e:
            return SendResult(success=False, channel=channel, error=str(e))

    # ── Notification Helpers ───────────────────────────────────────────

    def notify_build(self, workflow: str, status: str, duration_s: float = 0, url: str = "") -> SendResult:
        """Send build notification."""
        color = EMBED_COLORS["success"] if status == "success" else EMBED_COLORS["error"]
        icon = "[OK]" if status == "success" else "[!!]"
        embed = DiscordEmbed(
            title=f"{icon} Build: {workflow}",
            description=f"Status: **{status.upper()}**",
            color=color,
            url=url,
        )
        if duration_s:
            embed.add_field("Duration", f"{duration_s:.1f}s")
        embed.footer = "SLATE CI/CD"

        channel = self.config.notification_channels.get("build", "builds")
        return self.send_embed(channel, embed)

    def notify_health(self, service: str, status: str, details: str = "") -> SendResult:
        """Send service health notification."""
        color = EMBED_COLORS["success"] if status == "healthy" else EMBED_COLORS["error"]
        embed = DiscordEmbed(
            title=f"Service Health: {service}",
            description=f"Status: **{status}**",
            color=color,
        )
        if details:
            embed.add_field("Details", details, inline=False)
        embed.footer = "SLATE Health Monitor"

        channel = self.config.notification_channels.get("health", "status")
        return self.send_embed(channel, embed)

    def notify_progress(self, node: str, status: str, completion: float = 0) -> SendResult:
        """Send tech tree progress notification."""
        embed = DiscordEmbed(
            title=f"Tech Tree: {node}",
            description=f"Status: **{status}**",
            color=EMBED_COLORS["info"],
        )
        if completion:
            bar_filled = int(completion / 5)  # 20 chars max
            bar_empty = 20 - bar_filled
            bar = "+" * bar_filled + "-" * bar_empty
            embed.add_field("Progress", f"`[{bar}]` {completion:.1f}%", inline=False)
        embed.footer = "SLATE Tech Tree"

        channel = self.config.notification_channels.get("progress", "progress")
        return self.send_embed(channel, embed)

    def notify_error(self, source: str, error: str, severity: str = "error") -> SendResult:
        """Send error notification."""
        color = EMBED_COLORS["error"] if severity == "error" else EMBED_COLORS["warning"]
        embed = DiscordEmbed(
            title=f"Alert: {source}",
            description=f"```\n{error[:1500]}\n```",
            color=color,
        )
        embed.add_field("Severity", severity.upper())
        embed.footer = "SLATE Alert System"

        channel = self.config.notification_channels.get("error", "alerts")
        return self.send_embed(channel, embed)

    # ── Status ─────────────────────────────────────────────────────────

    def get_status(self) -> dict:
        """Get Discord integration status."""
        return {
            "enabled": self.config.enabled,
            "server_name": self.config.server_name,
            "channels_configured": len(self.config.webhooks),
            "channel_names": list(self.config.webhooks.keys()),
            "routing": self.config.notification_channels,
        }

    def print_status(self):
        """Print Discord integration status."""
        status = self.get_status()
        print()
        print("============================================================")
        print("  SLATE Discord Integration")
        print("============================================================")
        print()
        print(f"  Enabled:  {'Yes' if status['enabled'] else 'No'}")
        if status["server_name"]:
            print(f"  Server:   {status['server_name']}")
        print(f"  Channels: {status['channels_configured']} configured")
        if status["channel_names"]:
            for ch in status["channel_names"]:
                print(f"    #{ch}")
        print()
        print("  Event Routing:")
        for event, channel in status["routing"].items():
            print(f"    {event:15s} -> #{channel}")
        print()

        if not status["enabled"]:
            print("  To enable, set webhook URLs:")
            print("    SLATE_DISCORD_WEBHOOK_BUILDS=https://discord.com/api/webhooks/...")
            print("    SLATE_DISCORD_WEBHOOK_STATUS=https://discord.com/api/webhooks/...")
            print("    SLATE_DISCORD_WEBHOOK_ALERTS=https://discord.com/api/webhooks/...")
            print("    SLATE_DISCORD_WEBHOOK_PROGRESS=https://discord.com/api/webhooks/...")
            print()

        print("============================================================")
        print()


# ── Module-Level Helpers ───────────────────────────────────────────────

_discord: Optional[SlateDiscord] = None


def get_discord() -> SlateDiscord:
    """Get or create the Discord singleton."""
    global _discord
    if _discord is None:
        _discord = SlateDiscord()
    return _discord


# ── CLI ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="SLATE Discord Integration")
    parser.add_argument("--status", action="store_true", help="Show Discord status")
    parser.add_argument("--test", type=str, help="Send test notification to channel")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()
    discord = get_discord()

    if args.test:
        embed = DiscordEmbed(
            title="SLATE Test Notification",
            description="This is a test message from the SLATE Discord integration.",
            color=EMBED_COLORS["info"],
        )
        embed.add_field("System", "SLATE v2.4.0")
        embed.add_field("Tech Tree", "93.2%")
        embed.footer = "SLATE Notification System"

        result = discord.send_embed(args.test, embed)
        if result.success:
            print(f"Sent test message to #{args.test} (HTTP {result.status_code})")
        else:
            print(f"Failed: {result.error}")

    elif args.json:
        print(json.dumps(discord.get_status(), indent=2))

    else:
        discord.print_status()
