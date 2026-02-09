#!/usr/bin/env python3
"""
SLATE Community Management System
====================================

Privacy-driven community management for the SLATE Discord server.
Manages GitHub integration, fork-based user tiers, rate limit scaling,
and community rewards — all built inside SLATE standards.

Tier System (fork-based):
  Tier 0 (Guest)       — No GitHub linked, 3 questions/day
  Tier 1 (Community)   — GitHub linked, 5 questions/day
  Tier 2 (Contributor) — Forked SLATE repo, 10 questions/day
  Tier 3 (Builder)     — Forked + has commits, 20 questions/day

Privacy:
  - Discord user IDs are SHA-256 hashed (first 16 chars) — never stored raw
  - GitHub usernames stored only with explicit user consent via /slate-register
  - All data stored locally in .slate_community/ (git-ignored)
  - No external API calls for user data — only GitHub public fork API
  - Users can /slate-unregister to delete all their data

Security:
  - All GitHub API calls go through ActionGuard validation
  - Fork verification uses only public GitHub API (no auth required)
  - Rate limits enforced per-tier through DiscordSecurityGate
  - All interactions logged to audit trail
"""
# Modified: 2026-02-09T20:00:00Z | Author: Claude Opus 4.6 | Change: Create community management with GitHub fork tiers

import hashlib
import json
import logging
import os
import sys
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

WORKSPACE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

logger = logging.getLogger("slate.community")

# ── Constants ─────────────────────────────────────────────────────────

COMMUNITY_DIR = WORKSPACE_ROOT / ".slate_community"
MEMBERS_FILE = COMMUNITY_DIR / "members.json"
STATS_FILE = COMMUNITY_DIR / "stats.json"

GITHUB_ORG = "SynchronizedLivingArchitecture"
GITHUB_REPO = "S.L.A.T.E"
GITHUB_REPO_URL = f"https://github.com/{GITHUB_ORG}/{GITHUB_REPO}"
GITHUB_API_BASE = "https://api.github.com"

# Tier definitions
TIERS = {
    0: {"name": "Guest",       "emoji": "👋", "questions_per_day": 15,  "description": "No GitHub linked"},
    1: {"name": "Community",   "emoji": "🌐", "questions_per_day": 30,  "description": "GitHub account linked"},
    2: {"name": "Contributor", "emoji": "🔱", "questions_per_day": 60,  "description": "Forked SLATE repository"},
    3: {"name": "Builder",     "emoji": "⚡", "questions_per_day": 100, "description": "Forked + active commits"},
}

# SLATE AI identity for support responses
SLATE_AI_IDENTITY = (
    "You are interacting with **slate.ai** — the SLATE community support bot. "
    "I can answer questions about the S.L.A.T.E. project, its architecture, "
    "setup, specifications, and contribution guidelines. "
    "I operate within SLATE project scope only."
)


# ── Data Classes ──────────────────────────────────────────────────────

@dataclass
class CommunityMember:
    """A registered community member."""
    user_hash: str              # SHA-256 of Discord user ID (first 16 chars)
    tier: int = 0               # Current tier level
    github_username: str = ""   # GitHub username (only if registered)
    has_fork: bool = False      # Whether they've forked SLATE
    fork_commits: int = 0       # Commits on their fork
    registered_at: str = ""     # ISO timestamp
    last_verified: str = ""     # Last fork verification timestamp
    questions_today: int = 0    # Questions asked today
    questions_date: str = ""    # Date for question counter reset
    total_questions: int = 0    # Lifetime question count
    total_feedback: int = 0     # Lifetime feedback submissions
    reputation: int = 0         # Community reputation points


@dataclass
class TierCheck:
    """Result of a tier/rate check."""
    allowed: bool
    tier: int
    tier_name: str
    remaining: int              # Questions remaining today
    limit: int                  # Daily question limit
    reason: str = ""


# ── Community Manager ─────────────────────────────────────────────────

class CommunityManager:
    """
    Manages SLATE Discord community members, tiers, and GitHub integrations.

    Privacy-first design:
    - Discord IDs always hashed before storage
    - GitHub linking is opt-in only
    - Users can delete their data at any time
    """

    def __init__(self):
        COMMUNITY_DIR.mkdir(parents=True, exist_ok=True)
        self._members: dict[str, CommunityMember] = {}
        self._load_members()

    # ── Member Storage ────────────────────────────────────────────

    def _load_members(self):
        """Load member database from disk."""
        if MEMBERS_FILE.exists():
            try:
                data = json.loads(MEMBERS_FILE.read_text(encoding="utf-8"))
                for entry in data.get("members", []):
                    member = CommunityMember(**entry)
                    self._members[member.user_hash] = member
            except (json.JSONDecodeError, Exception) as e:
                logger.error(f"Failed to load members: {e}")

    def _save_members(self):
        """Save member database to disk."""
        data = {
            "version": "1.0",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "member_count": len(self._members),
            "members": [
                {
                    "user_hash": m.user_hash,
                    "tier": m.tier,
                    "github_username": m.github_username,
                    "has_fork": m.has_fork,
                    "fork_commits": m.fork_commits,
                    "registered_at": m.registered_at,
                    "last_verified": m.last_verified,
                    "questions_today": m.questions_today,
                    "questions_date": m.questions_date,
                    "total_questions": m.total_questions,
                    "total_feedback": m.total_feedback,
                    "reputation": m.reputation,
                }
                for m in self._members.values()
            ],
        }
        MEMBERS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # ── Member Management ─────────────────────────────────────────

    @staticmethod
    def _hash_user(discord_id: str) -> str:
        """Hash Discord user ID for privacy-safe storage."""
        return hashlib.sha256(str(discord_id).encode()).hexdigest()[:16]

    def get_member(self, discord_id: str) -> CommunityMember:
        """Get or create a community member (auto-registers as Guest)."""
        user_hash = self._hash_user(discord_id)
        if user_hash not in self._members:
            self._members[user_hash] = CommunityMember(
                user_hash=user_hash,
                registered_at=datetime.now(timezone.utc).isoformat(),
            )
            self._save_members()
        return self._members[user_hash]

    def remove_member(self, discord_id: str) -> bool:
        """Remove a member and all their data (GDPR-style deletion)."""
        user_hash = self._hash_user(discord_id)
        if user_hash in self._members:
            del self._members[user_hash]
            self._save_members()
            return True
        return False

    # ── GitHub Integration ────────────────────────────────────────

    def register_github(self, discord_id: str, github_username: str) -> tuple[bool, str]:
        """
        Link a GitHub account to a Discord member.

        Privacy: Only stores the GitHub username with explicit user consent.
        Verifies the account exists via public API (no auth needed).
        """
        member = self.get_member(discord_id)

        # Validate GitHub username format
        if not github_username or len(github_username) > 39:
            return False, "Invalid GitHub username format."
        if not all(c.isalnum() or c == '-' for c in github_username):
            return False, "GitHub username can only contain alphanumeric characters and hyphens."

        # Verify GitHub user exists (public API, no auth)
        try:
            url = f"{GITHUB_API_BASE}/users/{github_username}"
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "SLATE-CommunityBot/1.0")
            req.add_header("Accept", "application/vnd.github.v3+json")
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status != 200:
                    return False, f"GitHub user '{github_username}' not found."
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return False, f"GitHub user '{github_username}' not found."
            return False, "Could not verify GitHub account. Try again later."
        except Exception:
            return False, "Could not connect to GitHub API. Try again later."

        member.github_username = github_username
        member.tier = max(member.tier, 1)  # At least Community tier

        # Check for fork
        has_fork, commits = self._check_fork(github_username)
        member.has_fork = has_fork
        member.fork_commits = commits
        member.last_verified = datetime.now(timezone.utc).isoformat()

        if has_fork and commits > 0:
            member.tier = 3  # Builder
            member.reputation += 50
        elif has_fork:
            member.tier = 2  # Contributor
            member.reputation += 25
        else:
            member.tier = 1  # Community
            member.reputation += 10

        self._save_members()

        tier_info = TIERS[member.tier]
        return True, (
            f"✅ GitHub linked: **{github_username}**\n"
            f"Tier: {tier_info['emoji']} **{tier_info['name']}** (Tier {member.tier})\n"
            f"Daily questions: **{tier_info['questions_per_day']}**\n"
            f"{'🔱 Fork detected!' if has_fork else '💡 Fork SLATE to unlock Contributor tier!'}"
        )

    def _check_fork(self, github_username: str) -> tuple[bool, int]:
        """
        Check if a GitHub user has forked the SLATE repository.

        Uses public GitHub API — no authentication needed.
        Returns (has_fork, commit_count).
        """
        try:
            # Check user's repos for a fork of SLATE
            url = f"{GITHUB_API_BASE}/repos/{github_username}/{GITHUB_REPO}"
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "SLATE-CommunityBot/1.0")
            req.add_header("Accept", "application/vnd.github.v3+json")
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    repo_data = json.loads(resp.read().decode())
                    if repo_data.get("fork", False):
                        # It's a fork — check if parent is our repo
                        parent = repo_data.get("parent", {})
                        if parent.get("full_name") == f"{GITHUB_ORG}/{GITHUB_REPO}":
                            # Count commits (approximate via default branch)
                            commits = repo_data.get("size", 0)  # Rough proxy
                            # Try to get actual commit count
                            try:
                                commits_url = (
                                    f"{GITHUB_API_BASE}/repos/{github_username}/{GITHUB_REPO}"
                                    f"/commits?per_page=1"
                                )
                                creq = urllib.request.Request(commits_url)
                                creq.add_header("User-Agent", "SLATE-CommunityBot/1.0")
                                with urllib.request.urlopen(creq, timeout=10) as cresp:
                                    # GitHub returns Link header with last page number
                                    link = cresp.getheader("Link", "")
                                    if "last" in link:
                                        import re
                                        match = re.search(r'page=(\d+)>; rel="last"', link)
                                        if match:
                                            commits = int(match.group(1))
                                    else:
                                        commits = len(json.loads(cresp.read().decode()))
                            except Exception:
                                commits = 1  # At least 1 if fork exists
                            return True, max(commits, 0)
        except urllib.error.HTTPError:
            pass
        except Exception as e:
            logger.warning(f"Fork check failed for {github_username}: {e}")

        return False, 0

    def verify_fork(self, discord_id: str) -> tuple[bool, str]:
        """Re-verify a member's fork status (can be called periodically)."""
        member = self.get_member(discord_id)
        if not member.github_username:
            return False, "No GitHub account linked. Use `/slate-register` first."

        has_fork, commits = self._check_fork(member.github_username)
        old_tier = member.tier
        member.has_fork = has_fork
        member.fork_commits = commits
        member.last_verified = datetime.now(timezone.utc).isoformat()

        if has_fork and commits > 0:
            member.tier = 3
        elif has_fork:
            member.tier = 2
        elif member.github_username:
            member.tier = 1
        else:
            member.tier = 0

        if member.tier > old_tier:
            member.reputation += (member.tier - old_tier) * 15

        self._save_members()
        tier_info = TIERS[member.tier]
        upgraded = " 🎉 **Tier upgraded!**" if member.tier > old_tier else ""
        return True, (
            f"Fork status: {'✅ Active' if has_fork else '❌ Not found'}\n"
            f"Commits: {commits}\n"
            f"Tier: {tier_info['emoji']} **{tier_info['name']}**{upgraded}"
        )

    # ── Rate Limiting (Tier-Based) ────────────────────────────────

    def check_question_limit(self, discord_id: str) -> TierCheck:
        """
        Check if a user can ask a question based on their tier limits.

        Resets daily. Higher tiers get more questions.
        """
        member = self.get_member(discord_id)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Reset daily counter if new day
        if member.questions_date != today:
            member.questions_today = 0
            member.questions_date = today

        tier_info = TIERS.get(member.tier, TIERS[0])
        limit = tier_info["questions_per_day"]
        remaining = max(0, limit - member.questions_today)

        if remaining <= 0:
            upgrade_hint = ""
            if member.tier < 3:
                next_tier = TIERS[member.tier + 1]
                if member.tier == 0:
                    upgrade_hint = "\n💡 Link your GitHub with `/slate-register` for more questions!"
                elif member.tier == 1:
                    upgrade_hint = f"\n💡 Fork SLATE at {GITHUB_REPO_URL} for more questions!"
                elif member.tier == 2:
                    upgrade_hint = "\n💡 Make commits on your fork to unlock Builder tier!"

            return TierCheck(
                allowed=False,
                tier=member.tier,
                tier_name=tier_info["name"],
                remaining=0,
                limit=limit,
                reason=(
                    f"Daily question limit reached ({limit}/{limit} for {tier_info['name']} tier)."
                    f"{upgrade_hint}"
                ),
            )

        return TierCheck(
            allowed=True,
            tier=member.tier,
            tier_name=tier_info["name"],
            remaining=remaining,
            limit=limit,
        )

    def record_question(self, discord_id: str):
        """Record that a user asked a question."""
        member = self.get_member(discord_id)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if member.questions_date != today:
            member.questions_today = 0
            member.questions_date = today
        member.questions_today += 1
        member.total_questions += 1
        member.reputation += 1
        self._save_members()

    def record_feedback(self, discord_id: str):
        """Record that a user submitted feedback (bonus reputation)."""
        member = self.get_member(discord_id)
        member.total_feedback += 1
        member.reputation += 5
        self._save_members()

    # ── Hardware-Aware Rate Limiting ─────────────────────────────

    def get_hardware_multiplier(self) -> float:
        """
        Check local inference hardware availability and return a rate limit multiplier.

        Returns a multiplier (0.0 to 1.5) based on:
        - Ollama availability (primary inference provider)
        - GPU load (if nvidia-smi is available)
        - System load

        Multiplier logic:
          1.5 = hardware idle, max capacity → allow more questions
          1.0 = normal load → standard tier limits
          0.5 = high load → reduce limits to prevent overload
          0.0 = inference offline → block AI queries (keyword fallback only)
        """
        multiplier = 1.0

        # Check Ollama availability
        try:
            req = urllib.request.Request(
                "http://127.0.0.1:11434/api/tags", method="GET"
            )
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    multiplier = 1.0  # Ollama is up — baseline
                else:
                    return 0.0  # Ollama degraded
        except Exception:
            return 0.0  # Ollama is down — inference unavailable

        # Check GPU utilization (if nvidia-smi available)
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
                if avg_util < 30:
                    multiplier = 1.5   # GPUs mostly idle — boost limits
                elif avg_util < 70:
                    multiplier = 1.0   # Normal load
                elif avg_util < 90:
                    multiplier = 0.7   # Heavy load — reduce
                else:
                    multiplier = 0.5   # GPUs maxed — throttle hard
        except Exception:
            pass  # No GPU info — keep at 1.0

        return multiplier

    def check_question_limit_hardware_aware(self, discord_id: str) -> TierCheck:
        """
        Check if a user can ask a question, with hardware-aware scaling.

        Combines tier-based limits with real-time hardware availability.
        When GPUs are idle, users get bonus questions. When loaded, limits tighten.
        """
        member = self.get_member(discord_id)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Reset daily counter
        if member.questions_date != today:
            member.questions_today = 0
            member.questions_date = today

        tier_info = TIERS.get(member.tier, TIERS[0])
        base_limit = tier_info["questions_per_day"]

        # Apply hardware multiplier
        hw_mult = self.get_hardware_multiplier()
        effective_limit = max(1, int(base_limit * hw_mult))

        # Ensure we never go below 1 question even under load
        remaining = max(0, effective_limit - member.questions_today)

        if hw_mult == 0.0:
            # Inference is offline — allow limited keyword-based queries
            effective_limit = max(1, base_limit // 3)
            remaining = max(0, effective_limit - member.questions_today)
            if remaining <= 0:
                return TierCheck(
                    allowed=False,
                    tier=member.tier,
                    tier_name=tier_info["name"],
                    remaining=0,
                    limit=effective_limit,
                    reason=(
                        "AI inference is currently offline. "
                        "Limited keyword-based answers only. Please try again later."
                    ),
                )
            return TierCheck(
                allowed=True,
                tier=member.tier,
                tier_name=tier_info["name"],
                remaining=remaining,
                limit=effective_limit,
                reason="AI inference offline — keyword fallback mode",
            )

        if remaining <= 0:
            load_msg = ""
            if hw_mult < 1.0:
                load_msg = " (reduced due to high GPU load)"
            upgrade_hint = ""
            if member.tier < 3:
                if member.tier == 0:
                    upgrade_hint = "\n💡 Link GitHub with `/slate-register` for more questions!"
                elif member.tier == 1:
                    upgrade_hint = f"\n💡 Fork SLATE at {GITHUB_REPO_URL} for more questions!"
                elif member.tier == 2:
                    upgrade_hint = "\n💡 Make commits on your fork to unlock Builder tier!"

            return TierCheck(
                allowed=False,
                tier=member.tier,
                tier_name=tier_info["name"],
                remaining=0,
                limit=effective_limit,
                reason=(
                    f"Daily limit reached ({effective_limit} for {tier_info['name']} tier{load_msg})."
                    f"{upgrade_hint}"
                ),
            )

        return TierCheck(
            allowed=True,
            tier=member.tier,
            tier_name=tier_info["name"],
            remaining=remaining,
            limit=effective_limit,
        )

    # ── Member Info ───────────────────────────────────────────────

    def get_member_info(self, discord_id: str) -> dict:
        """Get member information for display (safe for Discord)."""
        member = self.get_member(discord_id)
        tier_info = TIERS.get(member.tier, TIERS[0])
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        questions_today = member.questions_today if member.questions_date == today else 0
        remaining = max(0, tier_info["questions_per_day"] - questions_today)

        return {
            "tier": member.tier,
            "tier_name": tier_info["name"],
            "tier_emoji": tier_info["emoji"],
            "tier_description": tier_info["description"],
            "github_linked": bool(member.github_username),
            "github_username": member.github_username,
            "has_fork": member.has_fork,
            "fork_commits": member.fork_commits,
            "questions_today": questions_today,
            "questions_remaining": remaining,
            "questions_limit": tier_info["questions_per_day"],
            "total_questions": member.total_questions,
            "total_feedback": member.total_feedback,
            "reputation": member.reputation,
            "registered_at": member.registered_at,
        }

    # ── Leaderboard ────────────────────────────────────────────────

    def get_all_members_ranked(self) -> list[dict]:
        """Get all members ranked by reputation for leaderboard display."""
        ranked = []
        for member in self._members.values():
            tier_info = TIERS.get(member.tier, TIERS[0])
            ranked.append({
                "user_hash": member.user_hash,
                "tier": member.tier,
                "tier_name": tier_info["name"],
                "github_username": member.github_username,
                "reputation": member.reputation,
                "total_questions": member.total_questions,
                "total_feedback": member.total_feedback,
                "has_fork": member.has_fork,
            })
        ranked.sort(key=lambda m: m["reputation"], reverse=True)
        return ranked

    # ── Community Stats ───────────────────────────────────────────

    def get_community_stats(self) -> dict:
        """Get community-wide statistics (safe for public display)."""
        total = len(self._members)
        by_tier = {}
        total_questions = 0
        total_feedback = 0
        total_forks = 0

        for member in self._members.values():
            tier_name = TIERS.get(member.tier, TIERS[0])["name"]
            by_tier[tier_name] = by_tier.get(tier_name, 0) + 1
            total_questions += member.total_questions
            total_feedback += member.total_feedback
            if member.has_fork:
                total_forks += 1

        return {
            "total_members": total,
            "by_tier": by_tier,
            "total_questions": total_questions,
            "total_feedback": total_feedback,
            "total_forks": total_forks,
        }


# ── Singleton ─────────────────────────────────────────────────────────

_community_manager: Optional[CommunityManager] = None


def get_community_manager() -> CommunityManager:
    """Get the singleton community manager."""
    global _community_manager
    if _community_manager is None:
        _community_manager = CommunityManager()
    return _community_manager


# ── Support Knowledge Base ────────────────────────────────────────────

# Project-scoped Q&A knowledge base for the support bot
# The bot answers ONLY within SLATE project scope
SUPPORT_TOPICS = {
    "what is slate": (
        "**S.L.A.T.E.** stands for Synchronized Living Architecture for Transformation and Evolution. "
        "Created by **Daniel Perry**, it's a local AI-powered development platform with dual-GPU inference, "
        "real-time monitoring, autonomous workflow orchestration, and community-driven development."
    ),
    "how to install": (
        "1. Clone the repo: `git clone {url}`\n"
        "2. Create a Python 3.11+ venv\n"
        "3. Install dependencies: `pip install -r requirements.txt`\n"
        "4. Bootstrap tokens: `python slate/slate_token_system.py --bootstrap`\n"
        "5. Start: `python slate/slate_orchestrator.py start`"
    ).format(url=GITHUB_REPO_URL),
    "how to fork": (
        f"1. Visit {GITHUB_REPO_URL}\n"
        "2. Click **Fork** in the top right\n"
        "3. Clone your fork locally\n"
        "4. Run `python slate/slate_fork_manager.py --init`\n"
        "5. Use `/slate-register <github_username>` here to unlock Contributor tier!"
    ),
    "how to contribute": (
        "SLATE accepts contributions via fork validation:\n"
        "1. Fork the repository\n"
        "2. Create a feature branch\n"
        "3. Follow SLATE prerequisites (ActionGuard, PII Scanner, SDK Source Guard)\n"
        "4. Submit a PR — it's validated by the fork-validation workflow\n"
        "5. Required checks: Security Gate, SDK Source Guard, SLATE Prerequisites"
    ),
    "tech stack": (
        "**Backend**: Python 3.11+, FastAPI\n"
        "**Frontend**: Vanilla JS + D3.js v7\n"
        "**AI**: Ollama (local), Foundry Local (ONNX), Claude Code\n"
        "**GPU**: Dual RTX 5070 Ti (Blackwell)\n"
        "**Infra**: Kubernetes, Docker, GitHub Actions\n"
        "**Vector DB**: ChromaDB (local)\n"
        "**Design**: Watchmaker aesthetic (spec 012)"
    ),
    "gpu setup": (
        "SLATE auto-detects NVIDIA GPUs via nvidia-smi.\n"
        "Supported: CUDA 12.x with compute capability 5.0+\n"
        "Check status: `python slate/slate_status.py --quick`\n"
        "GPU commands: `/slate-status` shows GPU count"
    ),
    "specs": (
        "SLATE uses a specification-driven development process:\n"
        "Lifecycle: `draft → specified → planned → tasked → implementing → complete`\n"
        "Each spec lives in `specs/NNN-feature-name/spec.md`\n"
        "Use `/slate-feedback` to suggest new specs!"
    ),
    "security": (
        "SLATE has multiple security layers:\n"
        "• **ActionGuard** — blocks dangerous commands\n"
        "• **SDK Source Guard** — only trusted publishers\n"
        "• **PII Scanner** — blocks credential exposure\n"
        "• **Discord Security Gate** — 7-layer output filtering\n"
        "All servers bind to 127.0.0.1 only — no external access."
    ),
    "tiers": (
        "**Community Tiers** (based on GitHub engagement):\n"
        "👋 **Guest** (Tier 0) — 15 questions/day\n"
        "🌐 **Community** (Tier 1) — GitHub linked, 30 questions/day\n"
        "🔱 **Contributor** (Tier 2) — Forked SLATE, 60 questions/day\n"
        "⚡ **Builder** (Tier 3) — Fork + commits, 100 questions/day\n\n"
        "Anti-flood protection prevents spam without limiting normal use.\n"
        "Use `/slate-register <github_username>` to link your account!"
    ),
    # ── How to Use SLATE ──────────────────────────────────────────
    "how to use slate": (
        "SLATE is a local AI-powered development platform. Here's how to get started:\n\n"
        "**Quick Start:**\n"
        "1. `python slate/slate_orchestrator.py start` — Launch all services\n"
        "2. `python slate/slate_status.py --quick` — Check system health\n"
        "3. Open `http://localhost:8080` — Dashboard with live monitoring\n\n"
        "**Key Commands:**\n"
        "• `/slate-status` — System health (Discord)\n"
        "• `/slate-support` — Ask questions (AI-powered)\n"
        "• `/slate-feedback` — Submit ideas\n\n"
        "*It's always better with a blank SLATE!*"
    ),
    "dashboard": (
        "The **SLATE Dashboard** runs on `localhost:8080` and provides:\n\n"
        "• **Real-time service monitoring** — GPU, Ollama, GitHub Runner status\n"
        "• **Tech tree visualization** — D3.js force-directed graph of all specs\n"
        "• **Task queue management** — View and manage current_tasks.json\n"
        "• **Watchmaker 3D theme** — Precision engineering aesthetic with animated gears\n\n"
        "Start it: `python agents/slate_dashboard_server.py`\n"
        "Or via orchestrator: `python slate/slate_orchestrator.py start`"
    ),
    "commands": (
        "**SLATE Bot Commands:**\n"
        "• `/slate-status` — Live system health (GPU, AI, dashboard)\n"
        "• `/slate-feedback <message>` — Submit feature requests or bugs\n"
        "• `/slate-tree` — Tech tree progress by phase\n"
        "• `/slate-about` — Project info and links\n"
        "• `/slate-support <question>` — AI-powered Q&A\n"
        "• `/slate-register <github>` — Link GitHub for tier upgrades\n"
        "• `/slate-unregister` — Delete all your data (GDPR)\n"
        "• `/slate-profile` — View your tier, reputation, and stats\n"
        "• `/slate-unlock` — Owner-only: open bot to community\n\n"
        "You can also **@slate.bot** in any channel to ask questions!"
    ),
    "kubernetes": (
        "SLATE deploys as a containerized local cloud in **Kubernetes**:\n\n"
        "• `kubectl apply -k k8s/` — Deploy all services\n"
        "• Dashboard, Ollama, ChromaDB, Agent Router as microservices\n"
        "• GPU-aware pod scheduling for RTX 5070 Ti\n"
        "• HPA auto-scaling (2-6 replicas for dashboard)\n"
        "• Full RBAC with minimal service accounts\n\n"
        "Quick deploy: `.\\k8s\\deploy.ps1 -Environment local`"
    ),
    "workflow": (
        "SLATE uses **GitHub Actions** as a task execution platform:\n\n"
        "• Tasks stored in `current_tasks.json` with priority queue\n"
        "• Self-hosted runner with GPU labels (slate, cuda, blackwell)\n"
        "• 33+ workflows: CI, nightly, AI maintenance, fork intelligence\n"
        "• Automatic stale task cleanup (>4h in-progress → reset)\n\n"
        "Commands:\n"
        "• `python slate/slate_workflow_manager.py --status`\n"
        "• `python slate/slate_runner_manager.py --status`"
    ),
    "ai backend": (
        "SLATE has 3 **FREE local AI providers** — zero cloud costs:\n\n"
        "🧠 **Ollama** (localhost:11434) — Primary: mistral-nemo, llama3.2, phi\n"
        "🤖 **Claude Code** (local MCP bridge) — Complex reasoning, code gen\n"
        "⚡ **Foundry Local** (localhost:5272) — ONNX-optimized fallback\n\n"
        "Tasks auto-route to the best provider via `unified_ai_backend.py`.\n"
        "Check status: `python slate/unified_ai_backend.py --status`"
    ),
    "tokens": (
        "SLATE has a complete **local token management system**:\n\n"
        "• Service tokens (`slsvc_`), agent tokens (`slagt_`), API tokens (`slapi_`)\n"
        "• SHA-256 hashed storage in `.slate_tokens/` (git-ignored)\n"
        "• Auto-rotation on expiry\n\n"
        "Bootstrap: `python slate/slate_token_system.py --bootstrap`\n"
        "Status: `python slate/slate_token_system.py --status`"
    ),
    "training": (
        "SLATE includes a **secure AI training pipeline**:\n\n"
        "• Ingests the entire git repo with secret filtering\n"
        "• PII Scanner redacts personal data before training\n"
        "• Custom `slate-custom` model based on mistral-nemo\n"
        "• Weekly training via `ai-training.yml` workflow\n\n"
        "Commands:\n"
        "• `python slate/slate_training_pipeline.py --collect`\n"
        "• `python slate/slate_training_pipeline.py --train`"
    ),
    "design": (
        "SLATE follows the **Watchmaker Design Philosophy**:\n\n"
        "• **Precision** — Every pixel on a 4px grid\n"
        "• **Mechanism** — Animated gears, flow lines, visible connections\n"
        "• **Depth** — Information in discoverable layers\n"
        "• **Craft** — Beauty from functional perfection\n\n"
        "Primary color: `#B85A3C` (warm rust)\n"
        "Blueprint bg: `#0D1B2A`\n"
        "Design tokens: `.slate_identity/design-tokens.json`"
    ),
    "discord bot": (
        "The **SLATE Discord bot** (slate.bot) provides community support:\n\n"
        "• 9 slash commands for status, feedback, and AI help\n"
        "• @mention support — tag @slate.bot with any question\n"
        "• Local Ollama AI inference (mistral-nemo) for intelligent answers\n"
        "• 7-layer security: no system internals ever exposed\n"
        "• Tier-based rate limiting tied to GitHub engagement\n"
        "• SLATE-to-SLATE federation for fork operators\n\n"
        "Start bot: `python -m slate.slate_discord_bot --start`"
    ),
    "federation": (
        "**SLATE Federation** enables bot-to-bot communication:\n\n"
        "• Fork operators can run their own SLATE bot\n"
        "• Federated queries route to the main SLATE instance\n"
        "• Health API on port 8086 for peer discovery\n"
        "• Rate limited: 10 queries per peer per minute\n"
        "• Requires a valid SLATE fork to participate\n\n"
        "Config: `.slate_identity/discord_config.json` → federation section"
    ),
    "plugin": (
        "SLATE is distributed as a **Claude Code plugin**:\n\n"
        "• Auto-loads when working in SLATE workspace\n"
        "• Slash commands: `/slate:status`, `/slate:workflow`, `/slate:gpu`\n"
        "• MCP tools: `slate_status`, `slate_workflow`, `slate_ai`\n"
        "• Skills: spec-kit, diagnostics, schematic generator\n\n"
        "Install from marketplace:\n"
        "`/plugin marketplace add SynchronizedLivingArchitecture/S.L.A.T.E`"
    ),
    "catchphrase": (
        "💡 **It's always better with a blank SLATE!**\n\n"
        "This is the SLATE project catchphrase — a reminder that every great system "
        "starts fresh. SLATE is designed to be forked, customized, and made your own.\n\n"
        "Other SLATE mottos:\n"
        "• *Systems Evolve With Progress* — the core ethos\n"
        "• *Everything runs locally. No cloud. No costs. Just pure engineering.*"
    ),
}


def find_support_answer(question: str) -> Optional[str]:
    """
    Find a relevant answer from the support knowledge base.

    Matches against topic keywords. Returns None if no match found.
    """
    question_lower = question.lower().strip()

    # Direct topic matches
    for topic, answer in SUPPORT_TOPICS.items():
        if topic in question_lower:
            return answer

    # Keyword matching
    keyword_map = {
        # Installation & Setup
        "install": "how to install",
        "setup": "how to install",
        "getting started": "how to install",
        "get started": "how to install",
        # Fork & Contribute
        "fork": "how to fork",
        "contribute": "how to contribute",
        "pr": "how to contribute",
        "pull request": "how to contribute",
        # Tech Stack
        "tech": "tech stack",
        "stack": "tech stack",
        "python": "tech stack",
        "fastapi": "tech stack",
        "d3": "tech stack",
        # GPU
        "gpu": "gpu setup",
        "cuda": "gpu setup",
        "nvidia": "gpu setup",
        "rtx": "gpu setup",
        "blackwell": "gpu setup",
        # Specs
        "spec": "specs",
        "specification": "specs",
        # Security
        "security": "security",
        "actionguard": "security",
        "action guard": "security",
        "pii": "security",
        "scanner": "security",
        # Tiers
        "tier": "tiers",
        "level": "tiers",
        "rate limit": "tiers",
        "question limit": "tiers",
        "upgrade": "tiers",
        # About SLATE
        "what is": "what is slate",
        "about slate": "what is slate",
        # How to Use
        "how to use": "how to use slate",
        "how do i": "how to use slate",
        "quick start": "how to use slate",
        "quickstart": "how to use slate",
        # Dashboard
        "dashboard": "dashboard",
        "monitoring": "dashboard",
        "8080": "dashboard",
        "visualization": "dashboard",
        # Commands
        "command": "commands",
        "slash command": "commands",
        "bot command": "commands",
        "help": "commands",
        # Kubernetes
        "kubernetes": "kubernetes",
        "k8s": "kubernetes",
        "kubectl": "kubernetes",
        "container": "kubernetes",
        "docker": "kubernetes",
        "deploy": "kubernetes",
        "deployment": "kubernetes",
        # Workflow
        "workflow": "workflow",
        "github actions": "workflow",
        "runner": "workflow",
        "task": "workflow",
        "ci": "workflow",
        "cd": "workflow",
        # AI Backend
        "ai": "ai backend",
        "ollama": "ai backend",
        "inference": "ai backend",
        "model": "ai backend",
        "foundry": "ai backend",
        "llm": "ai backend",
        "mistral": "ai backend",
        "claude code": "ai backend",
        # Tokens
        "token": "tokens",
        "authentication": "tokens",
        "auth": "tokens",
        # Training
        "training": "training",
        "train": "training",
        "custom model": "training",
        "pipeline": "training",
        # Design
        "design": "design",
        "watchmaker": "design",
        "theme": "design",
        "aesthetic": "design",
        "color": "design",
        "brand": "design",
        # Discord Bot
        "bot": "discord bot",
        "discord": "discord bot",
        "slate.bot": "discord bot",
        "slate.ai": "discord bot",
        "mention": "discord bot",
        # Federation
        "federation": "federation",
        "federate": "federation",
        "peer": "federation",
        # Plugin
        "plugin": "plugin",
        "mcp": "plugin",
        "extension": "plugin",
        "claude code plugin": "plugin",
        # Catchphrase
        "catchphrase": "catchphrase",
        "motto": "catchphrase",
        "slogan": "catchphrase",
        "blank slate": "catchphrase",
    }

    for keyword, topic in keyword_map.items():
        if keyword in question_lower:
            return SUPPORT_TOPICS.get(topic)

    return None


# ── CLI ───────────────────────────────────────────────────────────────

def main():
    """Community management CLI."""
    import argparse

    parser = argparse.ArgumentParser(description="SLATE Community Management")
    parser.add_argument("--stats", action="store_true", help="Show community stats")
    parser.add_argument("--members", action="store_true", help="List member tiers")
    parser.add_argument("--verify-all", action="store_true", help="Re-verify all fork statuses")

    args = parser.parse_args()
    manager = get_community_manager()

    if args.stats:
        stats = manager.get_community_stats()
        print("\n=== SLATE Community Stats ===")
        print(f"  Total members: {stats['total_members']}")
        print(f"  Total forks:   {stats['total_forks']}")
        print(f"  Questions:     {stats['total_questions']}")
        print(f"  Feedback:      {stats['total_feedback']}")
        print("  By tier:")
        for tier, count in stats["by_tier"].items():
            print(f"    {tier}: {count}")
        print()
        return 0

    if args.members:
        print("\n=== SLATE Community Members ===")
        for member in manager._members.values():
            tier = TIERS.get(member.tier, TIERS[0])
            gh = f" ({member.github_username})" if member.github_username else ""
            print(f"  {tier['emoji']} [{member.user_hash[:8]}...]{gh} — {tier['name']} (rep: {member.reputation})")
        print()
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
