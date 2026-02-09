# S.L.A.T.E. Docker Image — RELEASE / STABLE (GPU Variant)
# Modified: 2026-02-09T01:32:00Z | Author: Antigravity | Change: Multi-stage build, layer optimization, security hardening
# AI Note: When modifying, add a comment with the current date, time, and a 'Gemini' marker.
# Base: NVIDIA CUDA 12.8 Runtime on Ubuntu 22.04 (matches local Blackwell GPU stack)
#
# Build:  docker build -t slate:local -t ghcr.io/synchronizedlivingarchitecture/slate:latest-gpu .
# Push:   docker push ghcr.io/synchronizedlivingarchitecture/slate:latest-gpu
# K8s:    kubectl apply -k k8s/overlays/local/
#
# Runtimes included:
#   - SLATE Core (orchestrator, dashboard, status)
#   - Agent Router + Agent Workers (ALPHA/BETA/GAMMA/DELTA/COPILOT/ANTIGRAVITY)
#   - Autonomous Loop (self-healing task brain)
#   - Copilot Bridge (VS Code <-> K8s)
#   - Workflow Manager (task lifecycle, PR workflows)
#   - ML Pipeline (model training, codebase indexing, benchmarks)
#   - GPU Manager (dual-GPU load balancing)
#   - ChromaDB client (vector store for RAG)
#   - Semantic Kernel (AI orchestration)
#   - Security guards (ActionGuard, PII scanner, SDK source guard)
#   - GitHub Actions runner integration
#   - Spec Kit (spec processing, wiki generation)

# ═══════════════════════════════════════════════════════════════════════════════
# Stage 1: Builder — install dependencies (large, cached, discardable)
# ═══════════════════════════════════════════════════════════════════════════════
FROM nvidia/cuda:12.8.0-runtime-ubuntu22.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3.11 /usr/bin/python \
    && ln -sf /usr/bin/python3.11 /usr/bin/python3

WORKDIR /build

# Copy requirements first for layer caching
COPY requirements.txt .

# Install Python dependencies: PyTorch CUDA first, then the rest
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128 \
    && pip install --no-cache-dir -r requirements.txt

# ═══════════════════════════════════════════════════════════════════════════════
# Stage 2: Runtime — slim final image
# ═══════════════════════════════════════════════════════════════════════════════
FROM nvidia/cuda:12.8.0-runtime-ubuntu22.04

LABEL org.opencontainers.image.source="https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E"
LABEL org.opencontainers.image.description="SLATE - Synchronized Living Architecture for Transformation and Evolution (Release GPU)"
LABEL org.opencontainers.image.licenses="EOSL-1.0"
LABEL org.opencontainers.image.version="2.4.0"
LABEL slate.image.type="release"
LABEL slate.agent.primary="Antigravity"

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install Python runtime only (no dev headers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3-pip \
    git \
    tini \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3.11 /usr/bin/python \
    && ln -sf /usr/bin/python3.11 /usr/bin/python3

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/dist-packages /usr/local/lib/python3.11/dist-packages
COPY --from=builder /usr/local/bin /usr/local/bin

WORKDIR /slate

# Copy complete SLATE codebase
COPY slate/ ./slate/
COPY agents/ ./agents/
COPY slate_core/ ./slate_core/
COPY slate_web/ ./slate_web/
COPY models/ ./models/
COPY skills/ ./skills/
COPY plugins/ ./plugins/
COPY vendor/ ./vendor/
COPY docs/ ./docs/
COPY specs/ ./specs/
COPY .agent/ ./.agent/
COPY pyproject.toml .
COPY current_tasks.json .
COPY AGENTS.md .
COPY .github/copilot-instructions.md ./.github/copilot-instructions.md

# Copy K8s & Helm configs (for self-management inside cluster)
COPY k8s/ ./k8s/
COPY helm/ ./helm/

# Set Python path
ENV PYTHONPATH="/slate"
ENV SLATE_MODE=prod
ENV SLATE_DOCKER=1
ENV SLATE_K8S=true
ENV SLATE_VERSION=2.4.0
ENV SLATE_AGENT_NAME=Antigravity

# Create non-root user for security
RUN useradd -m -s /bin/bash -u 1000 slate \
    && chown -R slate:slate /slate
USER slate

# Expose service ports
EXPOSE 8080 8081 8082 8083 8084 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/api/health', timeout=5)" || exit 1

# Use tini as init system for proper signal handling
ENTRYPOINT ["tini", "--"]
CMD ["python", "slate/slate_orchestrator.py", "start", "--mode", "prod"]
