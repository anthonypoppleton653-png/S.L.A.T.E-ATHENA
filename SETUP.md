# S.L.A.T.E. Setup Guide
<!-- Modified: 2026-02-09T23:45:00Z | Author: COPILOT | Change: Create public SETUP.md for complete installation -->

Complete installation guide for **SLATE** (Synchronized Living Architecture for Transformation and Evolution) — a local-first AI agent orchestration framework.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Full Installation](#full-installation)
4. [Docker Deployment](#docker-deployment)
5. [Kubernetes Deployment](#kubernetes-deployment)
6. [VS Code + Copilot Setup](#vs-code--copilot-setup)
7. [Claude Code Setup](#claude-code-setup)
8. [Discord Community Setup](#discord-community-setup)
9. [Updating SLATE](#updating-slate)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.11+ | Runtime (3.11.9+ recommended) |
| Git | 2.40+ | Source control, upstream updates |
| pip | 23+ | Package management |

### Optional (Recommended)

| Tool | Version | Purpose |
|------|---------|---------|
| Docker Desktop | 24+ | Container deployment (GPU mode requires NVIDIA Container Toolkit) |
| Ollama | 0.5+ | Local LLM inference (GPU-accelerated) |
| VS Code | 1.96+ | Development IDE + @slate chat participant |
| kubectl | 1.28+ | Kubernetes deployment |
| NVIDIA GPU | CUDA 12.0+ | GPU inference (16GB+ VRAM recommended) |

### Validate Prerequisites

```bash
python slate/slate_setup_validator.py
```

This checks all prerequisites and reports a pass/fail summary. Use `--quick` for required checks only.

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E.git
cd S.L.A.T.E

# 2. Run the installer
python install_slate.py --install

# 3. Validate
python slate/slate_setup_validator.py --quick
```

The installer handles virtual environment creation, dependency installation, instruction file setup, and optional component configuration.

---

## Full Installation

### 1. Clone & Enter

```bash
git clone https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E.git
cd S.L.A.T.E
```

Or fork first, then clone your fork:
```bash
# Fork via GitHub UI, then:
git clone https://github.com/YOUR_USERNAME/S.L.A.T.E.git
cd S.L.A.T.E
```

### 2. Run Installer

```bash
python install_slate.py --install
```

The installer performs 26 steps including:
- Python version validation
- Virtual environment creation (`.venv/`)
- Dependency installation from `requirements.txt`
- Instruction file generation (from templates)
- Ollama model setup (if available)
- GPU detection and PyTorch configuration
- VS Code extension build (if VS Code is available)
- Security configuration (ActionGuard, PII scanner)

**Options:**
```bash
python install_slate.py --install --fork-name "YourProject"   # Custom project name
python install_slate.py --install --non-interactive           # No prompts
python install_slate.py --install --beta                      # Include beta features
python install_slate.py --install --no-personalize            # Skip instruction customization
```

### 3. Activate Virtual Environment

```bash
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# Windows (CMD)
.\.venv\Scripts\activate.bat

# Linux / macOS
source .venv/bin/activate
```

### 4. Verify Installation

```bash
python slate/slate_setup_validator.py
python slate/slate_status.py --quick
python slate/slate_runtime.py --check-all
```

---

## Docker Deployment

SLATE provides Docker images for containerized deployment with full GPU support.

### GPU Mode (Recommended)

```bash
# Build the local image
docker build -t slate:local .

# Start all services (SLATE, Ollama, ChromaDB, Grafana)
docker compose up -d

# Check status
docker compose ps
```

**Requirements:** NVIDIA Container Toolkit installed for GPU passthrough.

### CPU Mode (No GPU)

```bash
# Build CPU variant
docker build -t slate:local-cpu -f Dockerfile.cpu .

# Start with CPU profile
docker compose --profile cpu up -d
```

### Services

| Service | Port | Purpose |
|---------|------|---------|
| SLATE Dashboard | `127.0.0.1:8080` | Web UI, health endpoint |
| Agent Router | `127.0.0.1:8081` | Task classification & dispatch |
| Autonomous Loop | `127.0.0.1:8082` | Self-healing task brain |
| Copilot Bridge | `127.0.0.1:8083` | VS Code extension ↔ containers |
| Workflow Manager | `127.0.0.1:8084` | Task lifecycle management |
| Prometheus Metrics | `127.0.0.1:9090` | Metrics collection |
| Ollama | `127.0.0.1:11434` | LLM inference |
| ChromaDB | `127.0.0.1:8000` | Vector store |
| Grafana | `127.0.0.1:3000` | Monitoring dashboards |

> **Security:** All ports bind to `127.0.0.1` — local access only. This is enforced by SLATE security policy.

### Grafana Access

Default credentials: `admin` / `slate` — change after first login.

### Docker Compose Profiles

```bash
docker compose up -d                    # GPU mode (default)
docker compose --profile cpu up -d      # CPU mode (no GPU required)
docker compose --profile monitoring up -d  # With Prometheus
```

---

## Kubernetes Deployment

SLATE includes full Kubernetes manifests with Kustomize overlays for different environments.

### Prerequisites

- `kubectl` configured with cluster access
- Docker (for building images)
- NVIDIA GPU Operator (for GPU nodes) — optional

### Deploy to Local Cluster (Docker Desktop K8s / minikube / k3s)

```bash
# 1. Build the image
docker build -t slate:local .

# 2. Deploy with local overlay
kubectl kustomize k8s/overlays/local/ --load-restrictor LoadRestrictionsNone | kubectl apply -f -

# 3. Check status
kubectl get pods -n slate
kubectl get services -n slate
```

### Deploy to Other Environments

```bash
# Development
kubectl kustomize k8s/overlays/dev/ --load-restrictor LoadRestrictionsNone | kubectl apply -f -

# Staging
kubectl kustomize k8s/overlays/staging/ --load-restrictor LoadRestrictionsNone | kubectl apply -f -

# Production
kubectl kustomize k8s/overlays/prod/ --load-restrictor LoadRestrictionsNone | kubectl apply -f -
```

### Using SLATE K8s Manager

```bash
python slate/slate_k8s_deploy.py --status           # Cluster overview
python slate/slate_k8s_deploy.py --deploy            # Auto-detect & deploy
python slate/slate_k8s_deploy.py --health            # Health check
python slate/slate_k8s_deploy.py --port-forward      # Port forward all services
python slate/slate_k8s_deploy.py --teardown          # Remove everything
```

### K8s Architecture

All resources deploy to the `slate` namespace:

- **9 Deployments:** core, dashboard, agent-router, autonomous-loop, copilot-bridge, workflow-manager, instruction-controller, ollama, chromadb
- **CronJobs:** Codebase indexer (daily), inference benchmarks (weekly), model trainer (weekly), nightly health check, workflow cleanup (4h)
- **HPA:** Auto-scaling on agent-router and ollama
- **PDB:** Pod disruption budgets for high-availability services
- **NetworkPolicies:** Default deny with explicit allow rules
- **Secrets:** Template secrets — populate with your own credentials

### Secrets Management

The included `k8s/secrets.yaml` contains **templates only** (empty `data: {}`). Populate secrets before deploying:

```bash
# GitHub token (for CI integration)
kubectl create secret generic slate-github-credentials \
  --namespace slate \
  --from-literal=GITHUB_TOKEN=ghp_YOUR_TOKEN_HERE

# For GitOps: use Sealed Secrets
kubeseal --format yaml < secret.yaml > sealed-secret.yaml
```

---

## VS Code + Copilot Setup

### 1. Install VS Code Extensions

Required:
- **GitHub Copilot** (`github.copilot`)
- **Python** (`ms-python.python`)

Recommended:
- **Docker** (`ms-azuretools.vscode-docker`)
- **Kubernetes** (`ms-kubernetes-tools.vscode-kubernetes-tools`)
- **YAML** (`redhat.vscode-yaml`)

### 2. Open SLATE Workspace

```bash
code /path/to/S.L.A.T.E
```

### 3. Install @slate Extension

The installer builds the extension automatically. If you need to rebuild:

```bash
cd plugins/slate-copilot
npm install
npm run compile
# Then install the .vsix via VS Code: Extensions → Install from VSIX
```

Or use the install script:
```powershell
.\install_claude_plugin.ps1
```

### 4. Using @slate

In VS Code's Copilot Chat, type `@slate` followed by a command:

```
@slate /status          # System health check
@slate /runner          # Runner management
@slate /workflow        # Task management
@slate /specs           # Spec processing
@slate /benchmark       # Performance benchmarks
```

### Copilot Instructions

The installer generates `.github/copilot-instructions.md` automatically from the template. This configures Copilot to understand the SLATE codebase, enforce security rules, and use SLATE protocol commands.

---

## Claude Code Setup

### 1. Install Claude Code

Follow the [Claude Code installation guide](https://docs.anthropic.com/en/docs/claude-code).

### 2. Configure MCP Server

The installer creates `.claude/settings.json` from the template. If you need to configure manually:

```bash
# Copy template
cp templates/claude-settings.template.json .claude/settings.json

# Edit to replace placeholders:
# {{PYTHON_PATH}} → your .venv python path
# {{WORKSPACE_PATH}} → your workspace root
```

### 3. Using Claude Code with SLATE

Claude Code connects to SLATE via the MCP server (`slate/mcp_server.py`), providing access to all SLATE tools:

- System status & health
- Runner management
- Workflow operations
- GPU management
- Spec processing
- Kubernetes deployment

---

## Discord Community Setup

SLATE includes a full Discord bot for community onboarding with tiered access, security gates, and agentic AI features.

### 1. Create Discord Application

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create New Application → Name it "SLATE Bot"
3. Go to Bot → Enable:
   - Message Content Intent
   - Server Members Intent
   - Presence Intent
4. Copy the bot token

### 2. Configure Bot

```bash
# Set environment variables
export DISCORD_BOT_TOKEN="your-bot-token"
export DISCORD_GUILD_ID="your-server-id"
```

### 3. Run Onboarding Setup

```bash
python slate/discord_onboarding.py --setup
```

This creates:
- Channel structure (welcome, general, dev-hub, etc.)
- Role hierarchy (Guest, Community, Contributor, Builder, Owner)
- Permission matrix (tiered access control)
- Security gates (GitHub account linking, fork verification)

### 4. Community Tiers

| Tier | Role | Access | Requirements | Daily Questions |
|------|------|--------|-------------|-----------------|
| 0 | Guest | Public channels only | Join server | 15 |
| 1 | Community | General discussion | Accept rules | 30 |
| 2 | Contributor | Dev channels, CI access | Link GitHub + fork | 60 |
| 3 | Builder | Full access, admin tools | Merged PR + approval | 100 |

> Rate limits are hardware-aware — users with GPU hardware get a 1.5x multiplier.
> Community data is stored locally in `.slate_community/` (never committed to git).

### 5. Federation (Multi-Server)

SLATE supports multi-server federation for organizations running separate instances:

```bash
# Check federation status
python slate/discord_federation.py --status
```

Federation enables:
- Cross-server user identity (GitHub-linked)
- Shared support knowledge base (20+ built-in topics)
- Hardware-aware rate limiting across federated servers
- Automatic tier promotion based on upstream contributions

### 6. Community Module

The community module (`slate/slate_community.py`) manages member tiers, rate limiting, and the support knowledge base. It runs standalone or via the Discord bot:

```bash
# Check community stats
python slate/slate_community.py --status

# Search the support knowledge base
python slate/slate_community.py --search "gpu setup"
```

---

## Updating SLATE

### Automatic Updates (Recommended)

```bash
python slate/slate_updater.py --update
```

This performs a 9-step update pipeline:
1. Pre-flight checks (clean working tree, internet access)
2. Fetch upstream changes
3. Stash local changes and merge
4. Update Python dependencies
5. Rebuild VS Code extension
6. Rebuild Docker image (if Docker installed)
7. Re-apply K8s manifests (if cluster available)
8. Validate installation
9. Update instruction files

### Check for Updates

```bash
python slate/slate_updater.py --check
```

### Update Channels

```bash
python slate/slate_updater.py --channel main     # Latest development
python slate/slate_updater.py --channel stable    # Stable releases (default)
python slate/slate_updater.py --channel beta      # Pre-release features
```

### Options

```bash
python slate/slate_updater.py --update --no-docker   # Skip Docker rebuild
python slate/slate_updater.py --update --no-k8s      # Skip K8s re-deploy
python slate/slate_updater.py --update --dry-run      # Preview changes only
```

### Status

```bash
python slate/slate_updater.py --status
```

---

## Troubleshooting

### Common Issues

#### Python version too old
```
Error: Python 3.11+ required
```
Install Python 3.11+ from https://python.org. On Ubuntu: `sudo apt install python3.11 python3.11-venv`.

#### Ollama not found
```
Warning: Ollama not installed
```
Install from https://ollama.com. SLATE will work without Ollama but GPU inference features require it.

#### Docker GPU not available
```
Error: nvidia runtime not found
```
Install NVIDIA Container Toolkit:
```bash
# Ubuntu/Debian
sudo apt install nvidia-container-toolkit
sudo systemctl restart docker
```

#### K8s cluster not accessible
```
Warning: kubectl cluster-info failed
```
For local development, enable Kubernetes in Docker Desktop settings, or install minikube/k3s.

#### VS Code extension not loading
Rebuild the extension:
```bash
cd plugins/slate-copilot
npm install
npm run compile
```
Then install the `.vsix` file via VS Code.

### Diagnostic Commands

```bash
# Full system validation
python slate/slate_setup_validator.py

# System health
python slate/slate_status.py --quick

# Runtime integrations
python slate/slate_runtime.py --check-all

# GPU status
python slate/slate_hardware_optimizer.py

# Docker status
docker compose ps

# K8s status
python slate/slate_k8s_deploy.py --status
```

### Getting Help

- **Issues:** [GitHub Issues](https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E/issues)
- **Discussions:** [GitHub Discussions](https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E/discussions)
- **Discord:** Join the community server for real-time help

---

## Security

SLATE enforces strict security by design:

- **Local Only:** All network bindings use `127.0.0.1` — never `0.0.0.0`
- **ActionGuard:** Blocks destructive commands, unsafe bindings, dynamic execution
- **PII Scanner:** Prevents credentials and personal data from reaching Git
- **SDK Source Guard:** Only trusted package publishers (Microsoft, NVIDIA, Meta, Google, Hugging Face)
- **K8s RBAC:** Minimal service account permissions
- **Container Isolation:** Production workloads run in containers, not on the host

See [SECURITY.md](SECURITY.md) for the full security policy.

---

## License

SLATE is licensed under the [Ethical Open Source License 1.0 (EOSL-1.0)](LICENSE).
