# SLATE Discord Bot — Secure Container Image
# Modified: 2026-02-09T22:00:00Z | Author: Claude Opus 4.6 | Change: Add all bot modules, plugin, data dirs, tini init
#
# Security:
#   - Multi-stage build (no build deps in runtime)
#   - Non-root user (UID 1000)
#   - No secrets baked into image
#   - Tokens injected at runtime via env vars
#   - Health check on 127.0.0.1:8086
#
# Build:  docker build -t slate-discord-bot:local -f docker/discord-bot/Dockerfile .
# Run:    docker run --env-file .env slate-discord-bot:local
# K8s:    Deployed via k8s/discord-bot.yaml

# ── Build Stage ───────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install bot dependencies (discord.py + aiohttp for federation API)
RUN pip install --no-cache-dir --prefix=/install \
    "discord.py>=2.3.0" \
    aiohttp

# ── Runtime Stage ─────────────────────────────────────────────────────
FROM python:3.11-slim

LABEL org.opencontainers.image.source="https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E"
LABEL org.opencontainers.image.description="SLATE Discord Bot — Secure community integration"
LABEL org.opencontainers.image.licenses="EOSL-1.0"
LABEL org.opencontainers.image.version="3.0.0"
LABEL slate.image.type="discord-bot"

# Install tini for proper signal handling
RUN apt-get update && apt-get install -y --no-install-recommends tini \
    && rm -rf /var/lib/apt/lists/*

# Non-root user
RUN groupadd -r slate && useradd -r -g slate -u 1000 -m slate

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /install /usr/local

# ── SLATE Bot Modules ────────────────────────────────────────────────
# Package init (required for python -m slate.slate_discord_bot)
COPY slate/__init__.py slate/

# Core bot module + slash commands
COPY slate/slate_discord_bot.py slate/

# Security isolation gate (7-layer defense)
COPY slate/discord_security.py slate/

# Community management (tiers, rate limits, knowledge base)
COPY slate/slate_community.py slate/

# Onboarding system (roles, welcome, agentic AI support)
COPY slate/discord_onboarding.py slate/

# Federation API (cross-instance status sharing)
COPY slate/discord_federation.py slate/

# Discord webhook config (embeds, colors)
COPY slate/slate_discord.py slate/

# PII scanner (blocks personal data from output)
COPY slate/pii_scanner.py slate/

# ActionGuard (validates all actions, blocks dangerous patterns)
COPY slate/action_guard.py slate/

# ── Claude Code Plugin (embedded in container) ───────────────────────
COPY .claude-plugin/ .claude-plugin/
COPY .claude/commands/ .claude/commands/
COPY skills/ skills/

# ── Data Files (read-only defaults) ─────────────────────────────────
# Tech tree (read by /slate-tree command)
COPY .slate_tech_tree/tech_tree.json .slate_tech_tree/tech_tree.json

# ── Runtime Directories (writable at runtime) ────────────────────────
RUN mkdir -p slate_logs .slate_discussions .slate_community \
    && chown -R slate:slate /app

# ── Environment ──────────────────────────────────────────────────────
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV SLATE_MODE=prod
ENV SLATE_DOCKER=1
ENV SLATE_VERSION=3.0.0

USER slate

EXPOSE 8086

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8086/health')" || exit 1

ENTRYPOINT ["tini", "--"]
CMD ["python", "-m", "slate.slate_discord_bot", "--start"]
