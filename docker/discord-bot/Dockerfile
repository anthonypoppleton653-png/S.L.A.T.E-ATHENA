# SLATE Discord Bot — Secure Container Image
# Modified: 2026-02-09T18:30:00Z | Author: Claude Opus 4.6
#
# Security:
#   - Multi-stage build (no build deps in runtime)
#   - Non-root user (UID 1000)
#   - No secrets baked into image
#   - Tokens injected at runtime via env vars
#   - Health check on 127.0.0.1:8086

# ── Build Stage ───────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install \
    discord.py>=2.3.0 \
    aiohttp

# ── Runtime Stage ─────────────────────────────────────────────────────
FROM python:3.11-slim

LABEL org.opencontainers.image.source="https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E"
LABEL org.opencontainers.image.description="SLATE Discord Bot — Secure community integration"
LABEL org.opencontainers.image.licenses="EOSL-1.0"

# Non-root user
RUN groupadd -r slate && useradd -r -g slate -u 1000 slate

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /install /usr/local

# Copy SLATE modules needed by bot
COPY slate/discord_security.py slate/
COPY slate/slate_discord_bot.py slate/
COPY slate/slate_discord.py slate/
COPY slate/pii_scanner.py slate/
COPY slate/action_guard.py slate/

# Create required directories
RUN mkdir -p slate_logs .slate_discussions .slate_tech_tree \
    && chown -R slate:slate /app

USER slate

EXPOSE 8086

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8086/health')" || exit 1

ENTRYPOINT ["python", "-m", "slate.slate_discord_bot", "--start"]
