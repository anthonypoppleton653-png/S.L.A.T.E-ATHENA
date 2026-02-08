# S.L.A.T.E. Agent Instructions
# Modified: 2026-02-07T22:00:00Z | Author: COPILOT | Change: Add document evolution rules, participant enforcement, spec-kit mandate

## Overview
SLATE (Synchronized Living Architecture for Transformation and Evolution) is a local-first
AI agent orchestration framework. Version 2.4.0. All operations LOCAL ONLY (127.0.0.1).

## MANDATORY PROTOCOL  All Agents Must Follow

**Every agent session MUST begin by running SLATE protocols before performing work.**
This ensures system consistency and prevents regressions.

### Session Start Protocol (REQUIRED)
```bash
python slate/slate_status.py --quick          # 1. System health
python slate/slate_runtime.py --check-all     # 2. Verify all 7 integrations
python slate/slate_workflow_manager.py --status # 3. Check task queue
```

### Pre-Commit Protocol (REQUIRED)
```bash
python slate/slate_workflow_manager.py --enforce  # Block if tasks are stale
python slate/slate_workflow_manager.py --cleanup  # Archive deprecated tasks
```

## Agent System

### Agent Routing
Agents are routed by task pattern from `slate.config.yaml`:

| Pattern | Agent | Role | GPU |
|---------|-------|------|-----|
| implement, code, build, fix | ALPHA | Coding | Yes |
| test, validate, verify, coverage | BETA | Testing | Yes |
| analyze, plan, research, document | GAMMA | Planning | No |
| claude, mcp, sdk, integration | DELTA | External Bridge | No |
| diagnose, investigate, troubleshoot, interactive, explain | COPILOT_CHAT | Chat Participant | No |
| complex, multi-step | COPILOT | Full Orchestration | Yes |

### @slate Agent (COPILOT_CHAT)
The `@slate` agent is the primary copilot chat participant for the SLATE system.
It is registered as the **COPILOT_CHAT** agent in the agent registry, enabling
bidirectional task flow between the autonomous loop and the interactive chat interface.
It has access to all SLATE protocol commands and manages runner, workflows, and system health.

#### Bridge Architecture
```
Autonomous Loop ──▶ copilot_agent_bridge.py ──▶ .slate_copilot_bridge.json
                                                       │
@slate Participant ◀── slate_agentBridge tool ◀────────┘
       │
       ▼
.slate_copilot_bridge_results.json ──▶ Autonomous Loop picks up results
```

#### Available Tools
- **slate-status**: System health check (`python slate/slate_status.py --quick`)
- **slate-runtime**: Integration/dependency check (`python slate/slate_runtime.py --check-all`)
- **slate-hardware**: GPU detection & optimization (`python slate/slate_hardware_optimizer.py`)
- **slate-runner**: Runner management (`python slate/slate_runner_manager.py --status`)
- **slate-orchestrator**: Service lifecycle (`python slate/slate_orchestrator.py status`)
- **slate-workflow**: Task management (`python slate/slate_workflow_manager.py --status`)
- **slate-benchmark**: Performance benchmarks (`python slate/slate_benchmark.py`)
- **slate-chromadb**: Vector store operations (`python slate/slate_chromadb.py --status`)
- **slate-ci**: CI/CD workflow dispatch and monitoring via GitHub API

## Format Rules
All code edits MUST include a timestamp + author comment:
```python
# Modified: YYYY-MM-DDTHH:MM:SSZ | Author: COPILOT | Change: description
```

## Built-In Safeguards (All Agents Must Respect)

SLATE enforces these protections automatically:

1) **ActionGuard** - Blocks dangerous patterns
   - `rm -rf`, `format`, `del /s` (destructive commands)
   - `0.0.0.0` bindings (network exposure)
   - `eval()`, `exec()` (dynamic execution)
   - External paid API calls

2) **SDK Source Guard** - Trusted publishers only
   - Microsoft, NVIDIA, Meta, Google, Hugging Face
   - Unknown PyPI packages blocked

3) **PII Scanner** - Before GitHub sync
   - API keys, tokens, credentials detected
   - Personal info blocked from public boards

4) **Resource Limits**
   - Max concurrent tasks enforced
   - Stale tasks (>4h) flagged
   - GPU memory monitored

## Protocol Commands
```bash
# System status
python slate/slate_status.py --quick          # Quick health check
python slate/slate_status.py --json           # Machine-readable status

# Runtime integration check
python slate/slate_runtime.py --check-all     # All 7 integrations (Python, GPU, PyTorch, Transformers, Ollama, ChromaDB, venv)
python slate/slate_runtime.py --json          # JSON output

# Hardware & GPU optimization
python slate/slate_hardware_optimizer.py       # Detect GPUs
python slate/slate_hardware_optimizer.py --optimize       # Apply optimizations
python slate/slate_hardware_optimizer.py --install-pytorch # Install correct PyTorch

# Runner management
python slate/slate_runner_manager.py --detect  # Detect runner
python slate/slate_runner_manager.py --status  # Runner status
python slate/slate_runner_manager.py --dispatch "ci.yml"  # Dispatch workflow

# Orchestrator (all services)
python slate/slate_orchestrator.py start       # Start all services
python slate/slate_orchestrator.py stop        # Stop all services
python slate/slate_orchestrator.py status      # Service status

# Workflow manager
python slate/slate_workflow_manager.py --status   # Task status
python slate/slate_workflow_manager.py --cleanup   # Clean stale tasks
python slate/slate_workflow_manager.py --enforce   # Enforce completion

# ChromaDB vector store
python slate/slate_chromadb.py --status        # ChromaDB status & collections
python slate/slate_chromadb.py --index         # Index codebase into ChromaDB
python slate/slate_chromadb.py --search "query" # Semantic search
python slate/slate_chromadb.py --reset         # Reset all collections

# Benchmarks
python slate/slate_benchmark.py                # Run benchmarks
```

### Kubernetes Deployment
```bash
# Modified: 2026-02-09T04:30:00Z | Author: COPILOT | Change: Add K8s commands to AGENTS.md
python slate/slate_k8s_deploy.py --status            # K8s cluster overview
python slate/slate_k8s_deploy.py --deploy             # Deploy all manifests
python slate/slate_k8s_deploy.py --deploy-kustomize local  # Deploy with overlay
python slate/slate_k8s_deploy.py --health             # Health check
python slate/slate_k8s_deploy.py --logs <component>   # View component logs
python slate/slate_k8s_deploy.py --port-forward       # Port forwarding
python slate/slate_k8s_deploy.py --teardown           # Remove from cluster
```

## Project Structure
```
slate/              # Core SDK modules (30+ Python files)
  slate_status.py           # System health checker
  slate_runtime.py          # Integration & dependency checker (7 integrations)
  slate_hardware_optimizer.py  # GPU detection & PyTorch optimization
  slate_gpu_manager.py      # Dual-GPU load balancing for Ollama
  slate_runner_manager.py   # GitHub Actions runner management
  slate_orchestrator.py     # Unified service orchestrator
  slate_workflow_manager.py # Task lifecycle & PR workflows
  slate_workflow_analyzer.py # Meta-workflow analysis & deprecation detection
  slate_benchmark.py        # Performance benchmarks
  slate_fork_manager.py     # Fork contribution workflow
  slate_chromadb.py         # ChromaDB vector store integration
  ml_orchestrator.py        # ML inference orchestrator (Ollama + PyTorch)
  slate_model_trainer.py    # Custom SLATE model builder
  slate_unified_autonomous.py   # Unified autonomous task loop
  integrated_autonomous_loop.py # Self-healing autonomous brain
  copilot_slate_runner.py   # Copilot  autonomous bridge
  slate_project_board.py    # GitHub Projects V2 integration
  mcp_server.py             # MCP server for Claude Code
  action_guard.py           # Security enforcement (ActionGuard)
  sdk_source_guard.py       # SDK source validation
  pii_scanner.py            # PII detection
  slate_terminal_monitor.py # Terminal activity tracking
  install_tracker.py        # Installation tracking
  # Modified: 2026-02-09T04:30:00Z | Author: COPILOT | Change: Add K8s deploy to project structure
  slate_k8s_deploy.py       # Kubernetes deployment manager

agents/             # API servers & agent modules
  runner_api.py             # RunnerAPI class for CI integration
  slate_dashboard_server.py # FastAPI dashboard (127.0.0.1:8080)
  install_api.py            # Installation API

models/             # Ollama Modelfiles for SLATE custom models
  Modelfile.slate-coder     # 12B code generation (mistral-nemo base)
  Modelfile.slate-fast      # 3B classification/summary (llama3.2 base)
  Modelfile.slate-planner   # 7B planning/analysis (mistral base)

plugins/            # VS Code & Claude extensions
  slate-copilot/            # @slate chat participant (TypeScript)
  slate-sdk/                # Claude Code plugin

skills/             # Copilot Chat skill definitions
  slate-status/             # Status checking skill
  slate-runner/             # Runner management skill
  slate-orchestrator/       # Service orchestration skill
  slate-workflow/           # Workflow management skill
  slate-help/               # Help & documentation skill
```

## Self-Hosted Runner
- **Name**: slate-runner
- **Labels**: `[self-hosted, Windows, X64, slate, gpu, cuda, gpu-2, blackwell]`
- **Work folder**: `slate_work`
- **GPUs**: 2x NVIDIA GeForce RTX 5070 Ti (Blackwell, compute 12.0, 16GB each)
- **Pre-job hook**: Sets `CUDA_VISIBLE_DEVICES=0,1`, SLATE env vars, Python PATH
- **Python**: `<workspace>\.venv\Scripts\python.exe` (3.11.9)
- **No `actions/setup-python`**: All jobs use `GITHUB_PATH` to prepend venv
- **SLATE Custom Models**: slate-coder (12B), slate-fast (3B), slate-planner (7B)

## Workflow Conventions
- All jobs: `runs-on: [self-hosted, slate]`
- Default shell: `powershell`
- Python setup step: `"$env:GITHUB_WORKSPACE\.venv\Scripts" | Out-File -Append $env:GITHUB_PATH`
- YAML paths: Always single-quoted (avoid backslash escape issues)
- Workflows: ci.yml, slate.yml, pr.yml, nightly.yml, cd.yml, docs.yml, fork-validation.yml, contributor-pr.yml, agentic.yml, docker.yml, release.yml, k8s.yml

## Security Rules
- ALL network bindings: `127.0.0.1` ONLY  never `0.0.0.0`
- No external telemetry (ChromaDB telemetry disabled)
- No `curl.exe` (freezes on this system  use `urllib.request`)
- Protected files in forks: `.github/workflows/*`, `CODEOWNERS`, action guards
- Blocked patterns: `eval(`, `exec(os`, `rm -rf /`, `base64.b64decode`

## Terminal Rules
- Use `isBackground=true` for long-running commands (servers, watchers, runner)
- Never use `curl.exe`  use Python `urllib.request` or PowerShell `Invoke-RestMethod`
- Python executable: `./.venv/Scripts/python.exe` (Windows) or `./.venv/bin/python` (Linux/macOS)
- Always use `encoding='utf-8'` when opening files in Python on Windows
- Git credential: `git credential fill` with `protocol=https` / `host=github.com`

## GitHub API Access
```python
# Get token from git credential manager
import subprocess
result = subprocess.run(['git', 'credential', 'fill'],
    input='protocol=https\nhost=github.com\n',
    capture_output=True, text=True)
token = [l.split('=',1)[1] for l in result.stdout.splitlines()
         if l.startswith('password=')][0]
```
Repository API base: `https://api.github.com/repos/SynchronizedLivingArchitecture/S.L.A.T.E`

## Document Evolution Rules (ENFORCED)

All protocol files (`AGENTS.md`, `copilot-instructions.md`, `slate.config.yaml`) are
**append-only living documents**:

1. **ADDITIVE ONLY** — New rules are APPENDED. Never overwrite or remove existing behaviors.
2. **Preserve All Existing Rules** — Every existing section remains intact.
3. **Timestamp Every Change** — Each edit includes `# Modified:` with ISO timestamp.
4. **No Silent Overwrites** — Add NEW sections that augment originals. Never delete.
5. **Deprecation Protocol** — Add `# DEPRECATED: YYYY-MM-DD | Reason:` above retired sections.
6. **Version Accumulation** — The document grows over time. This is the complete behavioral history.

## Chat Participant Enforcement (MANDATORY)

All agents MUST use VS Code chat participants as their PRIMARY execution interface.

### Available Participants

| Participant | Purpose | When to Use |
|-------------|---------|-------------|
| `@slate` | SLATE system ops, runner, CI, GPU, specs, agents | System management, health, deployments |
| `@vscode` | Editor operations, files, settings | File ops, editor config, extensions |

### Enforcement Rules

1. **Subagents MUST use `@slate`** — Always prefer `@slate` over raw terminal commands.
2. **Spec work MUST use `slate_specKit`** — Never process specs manually.
3. **System operations MUST go through `@slate`** — Health, runner, CI, GPU — use the participant.
4. **Editor operations SHOULD use `@vscode`** — File management, settings, extensions.
5. **Multi-participant chaining** — Complex tasks chain: `@slate /status` → `@slate /specs` → `@vscode`.
6. **Never bypass participants** — If a tool exists for the operation, USE IT.

### Execution Priority

```
1. Participant tool (e.g., slate_workflow, slate_specKit)
2. Participant command (e.g., @slate /status)
3. Subagent delegation (runSubagent with 'slate')
4. Terminal (ONLY as last resort fallback)
```

### Spec-Kit Mandate

All specification processing, roadmap analysis, and wiki generation MUST go through:
- `slate_specKit` tool (via @slate participant)
- `@slate /specs` command
- `python slate/slate_spec_kit.py` (only as terminal fallback)

Never manually parse specs, manually write wiki pages, or skip the spec-kit pipeline.

## Container & Kubernetes Management (STANDARD PRACTICE)
# Modified: 2026-02-08T19:00:00Z | Author: COPILOT | Change: Add container/K8s extension enforcement as standard practice

SLATE runs as a **local cloud** using Kubernetes for system stability. The Docker image
built from `Dockerfile` is the **release/stable runtime** — the containerized version of
all SLATE runtimes. Local development improves the codebase, then builds the release image
that K8s deploys and manages.

### Release Image Architecture

```
Local Codebase (E:\11132025)
       │
       ▼  docker build -t slate:local .
   ┌──────────────────────────────────┐
   │  Dockerfile (Release Image)      │
   │  CUDA 12.8 + Python 3.11        │
   │  Full SLATE runtime:            │
   │   - Core + Dashboard            │
   │   - Agent Router + Workers      │
   │   - Autonomous Loop             │
   │   - Copilot Bridge              │
   │   - Workflow Manager             │
   │   - ML Pipeline                  │
   │   - GPU Manager                  │
   │   - Semantic Kernel              │
   │   - Security Guards              │
   │   - Models + Skills              │
   └──────────────────────────────────┘
       │
       ▼  kubectl apply -k k8s/overlays/local/
   ┌──────────────────────────────────┐
   │  Kubernetes (Local Cloud)        │
   │   namespace: slate               │
   │   7 deployments, 9+ pods        │
   │   HPAs, PDBs, NetworkPolicies   │
   │   CronJobs (ML, indexing)       │
   └──────────────────────────────────┘
```

### Required VS Code Extensions

Container and Kubernetes management MUST use the following VS Code extensions:

| Extension | ID | Purpose |
|-----------|-----|---------|
| Docker | `ms-azuretools.vscode-docker` | Build, manage, inspect containers and images |
| Container Tools | `ms-azuretools.vscode-containers` | Container lifecycle, compose, language model tools |
| Dev Containers | `ms-vscode-remote.remote-containers` | Develop inside containers |
| Kubernetes | `ms-kubernetes-tools.vscode-kubernetes-tools` | K8s cluster management, pod inspection, log viewing |
| Helm Intellisense | `tim-koehler.helm-intellisense` | Helm chart editing with autocomplete |
| YAML | `redhat.vscode-yaml` | K8s schema validation for manifests |

### Enforcement Rules

1. **Image builds** — Use Docker extension (right-click Dockerfile → Build Image) or `docker build -t slate:local .`
2. **Container management** — Use Docker extension sidebar for start/stop/inspect/logs
3. **K8s cluster management** — Use Kubernetes extension sidebar to browse pods, deployments, services
4. **Pod logs** — Use Kubernetes extension (right-click pod → Logs) instead of `kubectl logs`
5. **K8s apply/delete** — Use Kubernetes extension (right-click YAML → Apply) or `kubectl apply -k k8s/overlays/local/`
6. **Helm deploys** — Use Kubernetes extension or `helm install slate ./helm -f helm/values.yaml`
7. **Port forwarding** — Use Kubernetes extension (right-click service → Port Forward)
8. **NEVER bypass extensions** — If the extension supports the operation, USE IT over raw CLI

### Development Workflow (Local Cloud)

```
1. Edit code locally (slate/, agents/, etc.)
2. Build release image:  docker build -t slate:local .
3. Deploy to K8s:        kubectl apply -k k8s/overlays/local/
4. Verify in VS Code:    Kubernetes sidebar → slate namespace → pods
5. View logs:            Right-click pod → Logs
6. Port forward:         Right-click service → Port Forward
7. Iterate:              Repeat from step 1
```

### K8s Namespace: `slate`

All SLATE workloads run in the `slate` namespace. The Kubernetes extension defaults
to this namespace via workspace settings.

### Docker Compose (Alternative to K8s)

For simpler scenarios, Docker Compose is still available:
- **Dev:**  `docker-compose -f docker-compose.dev.yml up`
- **Prod:** `docker-compose -f docker-compose.prod.yml up -d`

But K8s is the **standard** for release deployments.
