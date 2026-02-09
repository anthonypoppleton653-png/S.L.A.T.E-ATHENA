# Spec 027: Discord Community Bot Integration

- **Spec ID**: 027-discord-community-bot
- **Status**: Implementing
- **Created**: 2026-02-09
- **Author**: Claude Opus 4.6
- **Dependencies**: 007-slate-design-system, 022-slate-brand-identity, 025-slate-user-permissions-onboarding, 026-slate-ethics-security
- **Spec-Kit**: Yes

---

## 1. Overview

This specification defines the **complete Discord community bot integration** for S.L.A.T.E. — covering bot identity, theme consistency, slash commands, @mention interaction, agentic AI support, hardware-aware rate limiting, SLATE-to-SLATE federation, server structure, and community knowledge base.

The bot (**slate.bot**, powered by **slate.ai**) is the public face of the SLATE community and demonstrates the platform's core capabilities: local AI inference, autonomous community management, and privacy-first design.

### Design Philosophy

> **"It's always better with a blank SLATE."**
>
> The Discord bot is a living proof-of-concept. Every interaction demonstrates what SLATE can do — local AI inference, real-time system monitoring, tier-based engagement, and zero-cost community management. The bot IS the product demo.

---

## 2. Bot Identity & Brand

### 2.1 Identity

| Property | Value |
|----------|-------|
| **Bot Username** | `slate.bot` |
| **AI Identity** | `slate.ai` |
| **Application Name** | `SLATE.GIT` |
| **Application ID** | `1470475063386964153` |
| **Server** | `slate.git` (ID: `1469890015780933786`) |
| **Catchphrase** | *It's always better with a blank SLATE* |
| **Ethos** | *Systems Evolve With Progress* |

### 2.2 Watchmaker Theme Integration

All bot embeds and visual elements follow the Watchmaker Design Philosophy (spec 007, 012):

```
Color Palette (from design-tokens.json):
  Primary:       #B85A3C (warm rust) — embed accent, role colors
  Blueprint BG:  #0D1B2A — architecture diagrams
  Blueprint Grid: #1B3A4B — secondary elements
  Success:       #6B8E23 (olive green) — positive status
  Secondary:     #5D5D74 — neutral elements
  Error:         #FF4444 — error states

Typography:
  Code blocks use monospace (Consolas/JetBrains Mono)
  Embed titles use sentence case
  Footer: "slate.ai — It's always better with a blank SLATE"
```

### 2.3 Discord Assets

| Asset | Path | Purpose |
|-------|------|---------|
| Banner | `.slate_identity/discord_assets/slate-discord-banner.svg` | Server banner (960x540) |
| Icon | `.slate_identity/discord_assets/slate-discord-icon.svg` | Server/bot icon (512x512) |
| Splash | `.slate_identity/discord_assets/slate-discord-splash.svg` | Invite splash (1920x1080) |

---

## 3. Server Structure

### 3.1 Categories & Channels

The bot auto-creates the following server structure via `discord_onboarding.py`:

```
━━ WELCOME ━━
  #welcome         (read-only, Tier 0+) — 6-embed welcome sequence
  #introductions   (writable, Tier 0+)  — New member introductions
  #rules           (read-only, Tier 0+) — Community guidelines + privacy notice

━━ COMMUNITY ━━
  #general         (writable, Tier 0+)  — General discussion
  #support         (writable, Tier 0+)  — Community help
  #feedback        (writable, Tier 0+)  — Feature requests, bug reports
  #showcase        (writable, Tier 1+)  — Community projects

━━ DEVELOPMENT ━━
  #dev-chat        (writable, Tier 2+)  — Developer discussion
  #dev-logs        (read-only, Tier 1+) — Automated development logs
  #pull-requests   (writable, Tier 2+)  — PR discussion

━━ SLATE SYSTEM ━━
  #slate-status    (read-only, Tier 0+) — Live system health
  #slate-builds    (read-only, Tier 1+) — Build notifications
  #slate-progress  (read-only, Tier 0+) — Tech tree progress
  #slate-alerts    (read-only, Tier 2+) — System alerts

━━ ADMIN ━━
  #bot-admin       (owner-only)         — Bot administration
  #audit-log       (owner-only)         — Interaction audit trail
  #bot-testing     (owner-only)         — Command testing
```

### 3.2 Roles

| Role | Tier | Color | Hoisted | Purpose |
|------|------|-------|---------|---------|
| SLATE Owner | — | `#B85A3C` | Yes | Server owner (manual creation) |
| SLATE Builder | 3 | `#6B8E23` | Yes | Fork + active commits |
| SLATE Contributor | 2 | `#2196F3` | Yes | Forked SLATE |
| SLATE Community | 1 | `#5D5D74` | Yes | GitHub linked |
| SLATE Guest | 0 | `#808080` | No | Default — no GitHub |
| slate.ai | — | `#8B4530` | Yes | Bot identity role (manual creation) |

---

## 4. Slash Commands

### 4.1 Command Reference

| Command | Description | Rate Limit | Access |
|---------|-------------|------------|--------|
| `/slate-status` | Sanitized system health | Security gate | Tier 0+ |
| `/slate-feedback <message>` | Submit feature requests, bugs, ideas | Security gate | Tier 0+ |
| `/slate-tree` | Tech tree progress by phase | Security gate | Tier 0+ |
| `/slate-about` | Project info, links, catchphrase | Security gate | Tier 0+ |
| `/slate-support <question>` | AI-powered Q&A (Ollama + KB fallback) | Hardware-aware | Tier 0+ |
| `/slate-register <github>` | Link GitHub for tier upgrades | Security gate | Tier 0+ |
| `/slate-unregister` | Delete all stored data (GDPR) | Security gate | Tier 0+ |
| `/slate-profile` | View tier, reputation, stats | Security gate | Tier 0+ |
| `/slate-unlock` | Owner: open bot to community | Owner only | Owner |

### 4.2 @Mention Support

Users can `@slate.bot` in any channel for AI-assisted help:

```
User: @slate.bot How do I set up the dashboard?
Bot:  [Embed] AI-powered response with source indicator (🧠 AI / 📚 KB / 📋 General)
```

**@Mention Pipeline:**
```
Message → Bot mention check → Guild lock → Lockdown check →
  Input validation (security gate) → Hardware-aware rate limit →
    Agentic AI (Ollama) → Keyword fallback → General fallback →
      Output sanitization → Embed response → Audit log
```

---

## 5. AI Support System

### 5.1 Agentic Support (Primary)

- **Provider**: Ollama (localhost:11434)
- **Model**: `mistral-nemo`
- **Max Response**: 1500 characters
- **Scope**: SLATE project only (system prompt enforced)
- **Fallback**: Keyword matching → General response

### 5.2 Knowledge Base (Fallback)

The bot maintains a SUPPORT_TOPICS knowledge base with 20+ topics:

| Topic | Keywords | Description |
|-------|----------|-------------|
| What is SLATE | what is, about slate | Project overview |
| Installation | install, setup, getting started | Setup guide |
| Forking | fork | Fork and contribute guide |
| Contributing | contribute, pr, pull request | Contribution workflow |
| Tech Stack | tech, stack, python, fastapi | Technology overview |
| GPU Setup | gpu, cuda, nvidia, rtx | GPU configuration |
| Specs | spec, specification | Spec-driven development |
| Security | security, actionguard, pii | Security architecture |
| Tiers | tier, level, rate limit | Community tier system |
| How to Use | how to use, quick start | Getting started guide |
| Dashboard | dashboard, monitoring, visualization | Dashboard features |
| Commands | command, slash command, help | Bot command reference |
| Kubernetes | k8s, kubectl, container, docker | K8s deployment |
| Workflow | workflow, github actions, runner | CI/CD system |
| AI Backend | ai, ollama, inference, llm | AI provider info |
| Tokens | token, authentication, auth | Token management |
| Training | training, train, pipeline | ML training pipeline |
| Design | design, watchmaker, theme | Design philosophy |
| Discord Bot | bot, discord, slate.bot | Bot features |
| Federation | federation, federate, peer | Bot-to-bot federation |
| Plugin | plugin, mcp, extension | Claude Code plugin |
| Catchphrase | catchphrase, motto, blank slate | Brand identity |

### 5.3 System Prompt

The AI agent operates under strict constraints:
1. ONLY answers SLATE-related questions
2. NEVER reveals system internals (IPs, paths, tokens, GPU serials)
3. NEVER executes code or modifies files
4. Redirects off-topic questions politely
5. Keeps responses under 300 words
6. Always identifies as an AI bot

---

## 6. Hardware-Aware Rate Limiting

### 6.1 Concept

Rate limits dynamically scale based on local inference hardware availability:

```
Hardware Check → GPU utilization (nvidia-smi) → Ollama status → Multiplier
  GPU < 30% utilization  → 1.5x (boost: hardware idle)
  GPU 30-70% utilization → 1.0x (normal)
  GPU 70-90% utilization → 0.7x (reduce: heavy load)
  GPU > 90% utilization  → 0.5x (throttle: maxed out)
  Ollama offline         → 0.0x (keyword fallback only)
```

### 6.2 Effective Limits

| Tier | Base | GPU Idle (1.5x) | Normal (1.0x) | Heavy (0.7x) | Maxed (0.5x) | Offline |
|------|------|-----------------|---------------|---------------|--------------|---------|
| Guest (0) | 3 | 4 | 3 | 2 | 1 | 1 |
| Community (1) | 5 | 7 | 5 | 3 | 2 | 1 |
| Contributor (2) | 10 | 15 | 10 | 7 | 5 | 3 |
| Builder (3) | 20 | 30 | 20 | 14 | 10 | 6 |

### 6.3 Implementation

```python
# In slate_community.py
class CommunityManager:
    def get_hardware_multiplier(self) -> float:
        """Check Ollama + GPU and return 0.0-1.5 multiplier."""
        ...

    def check_question_limit_hardware_aware(self, discord_id: str) -> TierCheck:
        """Combine tier limits with hardware multiplier."""
        ...
```

### 6.4 User Communication

When limits are affected by hardware:
- **Boosted**: No notification (seamless bonus)
- **Reduced**: "Daily limit reached (7 for Contributor tier, reduced due to high GPU load)"
- **Offline**: "AI inference is currently offline. Limited keyword-based answers only."

---

## 7. Security Architecture

### 7.1 Seven-Layer Defense

```
Layer 1: DiscordSecurityGate (discord_security.py)
  → Blocks IPs, file paths, tokens, GPU UUIDs, hostnames, PIDs from ALL output

Layer 2: PII Scanner (pii_scanner.py)
  → Redacts personal data (emails, phone numbers, SSNs)

Layer 3: ActionGuard (action_guard.py)
  → Validates all Discord network calls, blocks mass pings

Layer 4: Input Validation
  → Max 500 chars, no URLs, no code blocks, no @everyone/@here mentions

Layer 5: Rate Limiting
  → Security gate: 1/min per user, 30/min per channel
  → Tier-based: 3-20 questions/day (hardware-scaled)

Layer 6: Hashed User IDs
  → SHA-256, first 16 chars — never store raw Discord IDs

Layer 7: Audit Trail
  → All interactions logged to slate_logs/discord_audit.json
```

### 7.2 Guild Lock

The bot is **code-locked** to server ID `1469890015780933786`:
- `on_guild_join`: Immediately leaves unauthorized guilds
- All slash commands validate guild before executing
- Prevents hijacking of local inference endpoints

### 7.3 Owner Lockdown

Controlled via `.slate_community/bot_lockdown.json`:
```json
{"locked": false, "updated_at": "2026-02-09T22:30:00Z", "updated_by": "owner"}
```
- When locked: only server owner can use commands
- `/slate-unlock` toggles the lock
- Designed for maintenance windows

---

## 8. Community Feedback Pipeline

### 8.1 Flow

```
/slate-feedback or @mention feedback
  → DiscordSecurityGate (sanitize)
  → PII Scanner (redact)
  → Intent classification (Ollama: bug/feature/question/feedback)
  → .slate_discussions/discord_feedback.json (store)
  → ChromaDB community_feedback collection (embed)
  → current_tasks.json (create task, source: "discord", priority: low)
```

### 8.2 Storage

```json
{
  "events": [{
    "id": "df_001",
    "timestamp": "2026-02-09T18:00:00Z",
    "source": "discord",
    "channel": "feedback",
    "author_hash": "sha256_first_16",
    "intent": "feature_request",
    "content": "sanitized feedback text",
    "status": "pending"
  }]
}
```

---

## 9. SLATE-to-SLATE Federation

### 9.1 Concept

Fork operators who run their own SLATE instance can federate their Discord bot with the main SLATE bot for live support queries.

### 9.2 Architecture

```
Fork Bot (peer) → HTTP API → Rate Limiter → Security Gate → Main SLATE Bot
                  /api/v1/federation
                  Port 8086
```

### 9.3 Requirements

- Peer must have a valid SLATE fork (verified via GitHub API)
- Rate limited: 10 queries per peer per minute
- Peer registration stored in `.slate_community/federation/peers.json`
- All federation queries logged to `slate_logs/federation.json`

---

## 10. Onboarding Flow

### 10.1 New Member Join

```
Member joins → on_member_join event
  → Build welcome DM embed (name, quick start, catchphrase)
  → Send to #introductions (if permissions allow)
  → Create Guest tier member record (hashed ID)
```

### 10.2 Welcome Sequence (#welcome)

6 embeds posted on server setup:
1. **ASCII Banner** — SLATE logo
2. **Welcome** — Project overview + catchphrase
3. **Architecture Diagram** — System layout
4. **Getting Started** — 4-step guide
5. **Tier System** — Community tier breakdown
6. **Links** — GitHub, Website, Invite

### 10.3 Rules Sequence (#rules)

2 embeds:
1. **Community Guidelines** — 6 rules (respect, on-topic, no spam, security, AI transparency, constructive)
2. **Privacy Notice** — What we store, what we don't, GDPR deletion

---

## 11. Configuration

### 11.1 Primary Config

Source of truth: `.slate_identity/discord_config.json`

Key sections:
- `bot` — Username, identity, intents, rate limits, slash commands
- `onboarding` — Roles, channels, categories, AI support, artwork
- `community_management` — Storage, GitHub integration, tiers, privacy
- `notification_channels` — Event routing to channels
- `security` — Guild lock, PII scanner, audit log
- `feedback_pipeline` — Storage, ChromaDB collection
- `federation` — Peer communication config

### 11.2 Environment Variables

```
DISCORD_BOT_TOKEN    — Bot token (from Developer Portal, stored in .env)
DISCORD_APP_ID       — Application ID
DISCORD_PORT         — Health/federation API port (8086)
DISCORD_GUILD_ID     — Allowed guild ID
```

---

## 12. Files

| File | Purpose |
|------|---------|
| `slate/slate_discord_bot.py` | Main bot module — 9 slash commands, @mention handler |
| `slate/discord_security.py` | Security isolation gate (7-layer defense) |
| `slate/discord_onboarding.py` | Server structure, welcome embeds, agentic AI |
| `slate/discord_federation.py` | SLATE-to-SLATE bot federation |
| `slate/slate_community.py` | Community management, tiers, rate limiting |
| `slate/slate_discord.py` | Discord webhook configuration |
| `.slate_identity/discord_config.json` | Bot configuration (v4.0) |
| `.slate_community/members.json` | Member database (hashed IDs) |
| `.slate_community/bot_lockdown.json` | Lockdown state |
| `.slate_discussions/discord_feedback.json` | Feedback storage |
| `.slate_identity/design-tokens.json` | Brand tokens (catchphrase, colors) |
| `docker/discord-bot/Dockerfile` | Bot container image |
| `k8s/discord-bot.yaml` | K8s deployment manifest |
| `tests/test_discord_security.py` | Security gate tests |
| `tests/test_discord_bot.py` | Bot command tests |

---

## 13. Verification Checklist

- [x] Bot connects to Discord as slate.bot#9383
- [x] 9 slash commands registered and functional
- [x] @mention responses with AI support
- [x] Guild lock prevents unauthorized server use
- [x] 7-layer security gate blocks all system internals
- [x] Tier-based rate limiting (3-20 questions/day)
- [x] Hardware-aware rate limiting (GPU load scaling)
- [x] Knowledge base with 20+ topics and 80+ keyword triggers
- [x] Server structure auto-creation (6 roles, 5 categories, 17 channels)
- [x] Welcome sequence (6 embeds) posted to #welcome
- [x] Rules and privacy notice posted to #rules
- [x] Catchphrase integrated: "It's always better with a blank SLATE"
- [x] Federation API on port 8086
- [x] Lockdown mode (owner-only toggle)
- [x] GDPR-compliant data deletion via /slate-unregister
- [x] Feedback pipeline → ChromaDB → current_tasks.json
- [x] Watchmaker theme applied to all embeds
- [ ] K8s deployment tested
- [ ] Docker image built and scanned
- [ ] End-to-end federation test with fork peer

---

*spec-kit generated • S.L.A.T.E. — It's always better with a blank SLATE*
