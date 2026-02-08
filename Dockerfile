# S.L.A.T.E. Docker Image — RELEASE / STABLE (GPU Variant)
# Modified: 2026-02-08T19:00:00Z | Author: COPILOT | Change: Full release image with all SLATE runtimes containerized
# Base: NVIDIA CUDA 12.8 Runtime on Ubuntu 22.04 (matches local Blackwell GPU stack)
#
# This is the RELEASE image — the stable runtime that Kubernetes deploys.
# Local development improves the codebase, then builds this image as the
# containerized "release" that runs as a local cloud via K8s.
#
# Build:  docker build -t slate:local -t ghcr.io/synchronizedlivingarchitecture/slate:latest-gpu .
# Push:   docker push ghcr.io/synchronizedlivingarchitecture/slate:latest-gpu
# K8s:    kubectl apply -k k8s/overlays/local/
#
# Runtimes included:
#   - SLATE Core (orchestrator, dashboard, status)
#   - Agent Router + Agent Workers (ALPHA/BETA/GAMMA/DELTA/COPILOT)
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

FROM nvidia/cuda:12.8.0-runtime-ubuntu22.04

LABEL org.opencontainers.image.source="https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E"
LABEL org.opencontainers.image.description="SLATE - Synchronized Living Architecture for Transformation and Evolution (Release GPU)"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.version="2.4.0"
LABEL slate.image.type="release"

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install Python 3.11 and system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3.11 /usr/bin/python \
    && ln -sf /usr/bin/python3.11 /usr/bin/python3

# Set working directory
WORKDIR /slate

# Copy requirements first for layer caching
COPY requirements.txt .

# Install Python dependencies (full runtime — all SLATE integrations)
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy complete SLATE codebase — every runtime module
COPY slate/ ./slate/
COPY agents/ ./agents/
COPY slate_core/ ./slate_core/
COPY slate_web/ ./slate_web/
COPY models/ ./models/
COPY skills/ ./skills/
COPY plugins/ ./plugins/
COPY pyproject.toml .
COPY current_tasks.json .
COPY AGENTS.md .
COPY .github/copilot-instructions.md ./.github/copilot-instructions.md

# Copy K8s & Helm configs (for self-management inside cluster)
COPY k8s/ ./k8s/
COPY helm/ ./helm/

# Set Python path — includes workspace mount point for live code
ENV PYTHONPATH="/slate:${PYTHONPATH}"
ENV SLATE_MODE=prod
ENV SLATE_DOCKER=1
ENV SLATE_K8S=true
ENV SLATE_VERSION=2.4.0

# Create non-root user for security
RUN useradd -m -s /bin/bash slate \
    && chown -R slate:slate /slate
USER slate

# Expose service ports
EXPOSE 8080  
# 8080 = Dashboard/Core API
EXPOSE 8081  
# 8081 = Agent Router API
EXPOSE 8082  
# 8082 = Autonomous Loop API
EXPOSE 8083  
# 8083 = Copilot Bridge API
EXPOSE 8084  
# 8084 = Workflow Manager API
EXPOSE 9090  
# 9090 = Prometheus Metrics

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/api/health', timeout=5)" || exit 1

# Default entrypoint: start SLATE orchestrator
ENTRYPOINT ["python", "slate/slate_orchestrator.py"]
CMD ["start", "--mode", "prod"]
