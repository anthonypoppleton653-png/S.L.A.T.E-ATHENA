# S.L.A.T.E. Development Guidelines
<!-- Modified: 2026-02-08T05:00:00Z | Author: Claude Opus 4.5 | Change: Add evolving system ethos and schematic background -->

**S.L.A.T.E.** = Synchronized Living Architecture for Transformation and Evolution

**Constitution**: `.specify/memory/constitution.md` — Supersedes all other practices
Last updated: 2026-02-08

## Core Ethos: Systems Evolve With Progress

**SLATE systems are living systems that reflect their current state and evolve as progress is made.**

This principle applies to all SLATE components:

| Component | How It Evolves |
|-----------|----------------|
| **VS Code Theme** | SLATE Dark theme with evolving schematic background |
| **Schematic Background** | Reflects tech tree progress, active services, and spec completion |
| **Dashboard** | Real-time system architecture visualization |
| **Tech Tree** | Visual progression of completed and in-progress features |
| **Specs** | Lifecycle from draft → complete, visible in all visualizations |

### Schematic Background System

The SLATE VS Code extension provides an **evolving schematic background** that:

1. **Reflects Current State**: Shows active services, GPU count, AI backends
2. **Shows Progress**: Tech tree completion percentage, specs completed
3. **Auto-Updates**: Refreshes when tech tree or specs change
4. **Grows More Visible**: Background opacity increases as system matures

```powershell
# VS Code Commands
> SLATE: Apply SLATE Dark Theme       # Apply theme + background
> SLATE: Refresh Schematic Background # Force refresh
> SLATE: Toggle Schematic Background  # Enable/disable
```

The background is generated from real system state:
- `/.slate_tech_tree/tech_tree.json` - Tech tree progress
- `/specs/**/spec.md` - Specification status
- Service status (dashboard, ollama, runner, etc.)
- GPU configuration

**All SLATE visualizations should follow this ethos** — they are not static documentation but living representations of system state.

## Active Technologies
- Python 3.11+ (backend), Vanilla JavaScript + D3.js v7 (frontend)
- FastAPI (dashboard server on port 8080)
- D3.js v7 (bundled locally, tech tree visualization)
- **Ollama** (local LLM inference, mistral-nemo on dual RTX 5070 Ti) - localhost:11434
- **Foundry Local** (ONNX-optimized local inference) - localhost:5272
- ChromaDB (local vector store for RAG memory)

## Claude Code Plugin

SLATE is distributed as a **Claude Code plugin** with commands, skills, and MCP tools. Plugins load dynamically without restart.

### Installation

**Option 1: Local Workspace (Recommended)**
```bash
# Plugin auto-loads when working in SLATE workspace
# The .claude-plugin/ directory is detected automatically
cd /path/to/S.L.A.T.E
claude  # Plugin loads at project scope
```

**Option 2: From GitHub Marketplace**
```bash
# Add SLATE marketplace (one-time setup)
/plugin marketplace add SynchronizedLivingArchitecture/S.L.A.T.E

# Install SLATE plugin
/plugin install slate@slate-marketplace
```

**Option 3: Development Mode**
```bash
claude --plugin-dir /path/to/S.L.A.T.E
```

### Plugin Scope Rules

**IMPORTANT**: Local and marketplace plugins have different scopes:

| Plugin Type | Scope | How It Loads |
|-------------|-------|--------------|
| Local (`.claude-plugin/` exists) | Project | Auto-loads when `cd` into workspace |
| Marketplace (`/plugin install`) | User | Must explicitly enable |

**Do NOT mix scopes.** If you have a local `.claude-plugin/` directory, don't also try to enable it as a marketplace plugin - this causes the scope mismatch error.

### For Local Development (This Repo)

```bash
# Just cd into the workspace - plugin auto-loads
cd /path/to/S.L.A.T.E
claude  # Plugin loads automatically at project scope
```

No configuration needed - the `.claude-plugin/plugin.json` is detected automatically.

### For External Users (Installing from GitHub)

```bash
# Add marketplace and install
/plugin marketplace add SynchronizedLivingArchitecture/S.L.A.T.E
/plugin install slate@slate-marketplace

# Manage at user scope
/plugin list
/plugin enable slate@slate-marketplace --scope user
/plugin disable slate@slate-marketplace --scope user
```

### Plugin Structure

```
.claude-plugin/
├── plugin.json       # Plugin manifest (name, version, component paths)
└── marketplace.json  # Distribution catalog for /plugin install
.claude/commands/     # Slash commands
skills/               # Agent skills (skills/*/SKILL.md)
.mcp.json             # MCP server configuration
```

### Commands

Commands are available as `/slate:<command>` or `/slate-<command>`:

| Command | Description |
|---------|-------------|
| `/slate:status` | Check system and service status |
| `/slate:workflow` | Manage task workflow queue |
| `/slate:runner` | Manage GitHub Actions runner |
| `/slate:gpu` | Manage dual-GPU load balancing |
| `/slate:help` | Show all available commands |

### MCP Tools

MCP tools are auto-configured via `.mcp.json`:

| Tool | Description |
|------|-------------|
| `slate_status` | Check all services and GPU status |
| `slate_workflow` | Manage task queue |
| `slate_orchestrator` | Start/stop services |
| `slate_runner` | Manage GitHub runner |
| `slate_ai` | Execute AI tasks via local LLMs |
| `slate_gpu` | Manage dual-GPU load balancing |

## SLATE Operator Behavior (Permission Bypass Mode)

SLATE provides a **locked-in behavior profile** that enables permission bypass while maintaining security through ActionGuard.

### Behavior Configuration

```yaml
Profile: slate-operator
Security: ActionGuard (Python-side validation)
Permissions: Bypass with ActionGuard protection
Runtime: K8s > Docker (container-first)
```

### Files

| File | Purpose |
|------|---------|
| `.claude/settings.json` | Main configuration with behavior reference |
| `.claude/settings.local.json` | Permission overrides (bypass all) |
| `.claude/behaviors/slate-operator.md` | Behavior profile definition |
| `.claude/behaviors/slate-protocols.md` | Operational protocols (P001-P010) |
| `.claude/hooks.json` | ActionGuard hook integration |

### Key Protocols

| Protocol | Trigger | Description |
|----------|---------|-------------|
| P001-INIT | Session start | Check runtime, load instructions |
| P002-EXECUTE | Task request | DIAGNOSE → ACT → VERIFY pattern |
| P003-WORKFLOW | Queue ops | Task management, stale cleanup |
| P005-SECURITY | Bash commands | ActionGuard validation |
| P009-K8S | K8s deploy | Kustomize/Helm deployment |

### Permission Bypass

With SLATE Operator behavior, Claude Code operates without confirmation prompts because:

1. **ActionGuard validates all commands** before execution (Python-side)
2. **SDK Source Guard** ensures trusted package publishers
3. **PII Scanner** blocks credential exposure
4. **Container isolation** runs commands in K8s/Docker, not host
5. **K8s RBAC** provides minimal service account permissions

### Activation

The behavior activates automatically when:
- Working in SLATE workspace
- `settings.json` has `"behavior": { "profile": "slate-operator" }`
- `settings.local.json` has permission bypass rules

## Built-In Safeguards

SLATE includes multiple protection layers for safe AI automation.

### ActionGuard
Blocks dangerous patterns: `rm -rf`, `0.0.0.0` bindings, `eval()`/`exec()`, external API calls.

### SDK Source Guard
Only trusted publishers: Microsoft, NVIDIA, Meta, Google, Hugging Face.

### PII Scanner
Scans for API keys, tokens, credentials before GitHub sync.

### Resource Limits
- Max concurrent tasks enforced
- Stale task detection (>4h in-progress)
- GPU memory monitoring per-runner

## MCP Tools

| Tool | Description |
|------|-------------|
| `slate_status` | Check all services and GPU status |
| `slate_workflow` | Manage task queue |
| `slate_orchestrator` | Start/stop services |
| `slate_runner` | Manage GitHub runner |
| `slate_ai` | Execute AI tasks via local LLMs |
| `slate_runtime` | Check runtime integrations |
| `slate_hardware` | Detect and optimize GPU hardware |
| `slate_gpu` | Manage dual-GPU load balancing |
| `slate_claude_code` | Validate Claude Code configuration |
| `slate_spec_kit` | Process specs, run AI analysis, generate wiki |

### Structure

```text
.claude/commands/     # Claude Code slash commands
  slate.md            # /slate command
  slate-status.md     # /slate-status command
  slate-workflow.md   # /slate-workflow command
  slate-runner.md     # /slate-runner command
  slate-discussions.md  # /slate-discussions command
  slate-multirunner.md  # /slate-multirunner command
  slate-gpu.md        # /slate-gpu command
  slate-claude.md     # /slate-claude command
  slate-spec-kit.md   # /slate-spec-kit command
  slate-help.md       # /slate-help command
slate/mcp_server.py           # MCP server implementation
slate/slate_spec_kit.py       # Spec-Kit wiki integration
slate/claude_code_validator.py  # Claude Code settings validator
slate/claude_code_manager.py    # Claude Code configuration manager
```

### Claude Code Validation

SLATE validates Claude Code integration with multiple checks:

```powershell
# Validate Claude Code configuration
.\.venv\Scripts\python.exe slate/claude_code_manager.py --validate

# Generate full validation report
.\.venv\Scripts\python.exe slate/claude_code_manager.py --report

# Show Agent SDK options
.\.venv\Scripts\python.exe slate/claude_code_manager.py --agent-options

# Test MCP server
.\.venv\Scripts\python.exe slate/claude_code_manager.py --test-mcp slate
```

### Claude Agent SDK Integration

SLATE provides recommended Agent SDK options for programmatic use:

```python
from slate.claude_code_manager import get_manager

manager = get_manager()
options = manager.get_agent_options(
    allowed_tools=["Read", "Write", "Edit", "Bash"],
    permission_mode="acceptEdits",
    model="claude-sonnet-4-5-20250929"
)
```

Hook integration with ActionGuard:

```python
# PreToolUse hooks validate through ActionGuard
result = manager.execute_hooks(
    event="PreToolUse",
    tool_name="Bash",
    tool_input={"command": "python script.py"},
    session_id="my-session"
)
if result.permission_decision == "deny":
    print(f"Blocked: {result.reason}")
```

## Local AI Providers (FREE - No Cloud Costs)

| Provider | Port | Models | Status |
|----------|------|--------|--------|
| Ollama | 11434 | mistral-nemo, llama3.2, phi, llama2, mistral | Active |
| Foundry Local | 5272 | Phi-3, Mistral-7B (ONNX) | Active |

```powershell
# Check provider status
.\.venv\Scripts\python.exe slate/foundry_local.py --check

# List all local models
.\.venv\Scripts\python.exe slate/foundry_local.py --models

# Generate with auto-provider selection
.\.venv\Scripts\python.exe slate/foundry_local.py --generate "your prompt"

# Download Foundry Local models (run in PowerShell)
foundry model download microsoft/Phi-3.5-mini-instruct-onnx
```

**Security**: ActionGuard blocks ALL paid cloud APIs (OpenAI, Anthropic, etc.). Only localhost AI services are allowed.

## Unified AI Backend

SLATE routes all AI tasks through `unified_ai_backend.py` which prioritizes FREE local backends:

```
Task Type          -> Best Backend     (Cost)
─────────────────────────────────────────────
code_generation    -> ollama_local     (FREE)
code_review        -> ollama_local     (FREE)
test_generation    -> ollama_local     (FREE)
bug_fix            -> ollama_local     (FREE)
refactoring        -> ollama_local     (FREE)
documentation      -> ollama_local     (FREE)
analysis           -> ollama_local     (FREE)
research           -> ollama_local     (FREE)
planning           -> speckit          (FREE)
```

```powershell
# Check all backend status
.\.venv\Scripts\python.exe slate/unified_ai_backend.py --status

# Execute task with auto-routing
.\.venv\Scripts\python.exe slate/unified_ai_backend.py --task "your task"
```

**Key Files**:
- `slate/unified_ai_backend.py` - Central routing (Ollama, Foundry, Copilot, Claude)
- `slate/foundry_local.py` - Foundry Local + Ollama unified client
- `slate/inference_instructions.py` - ML-based code generation guidance
- `slate/action_guard.py` - Security (blocks paid APIs)

## AI Orchestrator (Automated Maintenance)

SLATE includes an AI orchestrator that automatically maintains the codebase using local Ollama models.

### Capabilities

| Feature | Schedule | Description |
|---------|----------|-------------|
| Quick Analysis | Every 4 hours | Analyze recently changed files |
| Full Analysis | Daily 2am | Complete codebase analysis |
| Documentation | Daily | Auto-generate/update docs |
| GitHub Monitor | Daily | Analyze workflows and integrations |
| Model Training | Weekly Sunday | Train custom SLATE model |

### Commands

```powershell
# Check AI orchestrator status
.\.venv\Scripts\python.exe slate/slate_ai_orchestrator.py --status

# Warmup AI models
.\.venv\Scripts\python.exe slate/slate_ai_orchestrator.py --warmup

# Analyze recently changed files
.\.venv\Scripts\python.exe slate/slate_ai_orchestrator.py --analyze-recent

# Full codebase analysis
.\.venv\Scripts\python.exe slate/slate_ai_orchestrator.py --analyze-codebase

# Update documentation
.\.venv\Scripts\python.exe slate/slate_ai_orchestrator.py --update-docs

# Monitor GitHub integrations
.\.venv\Scripts\python.exe slate/slate_ai_orchestrator.py --monitor-github

# Collect training data
.\.venv\Scripts\python.exe slate/slate_ai_orchestrator.py --collect-training

# Train custom model
.\.venv\Scripts\python.exe slate/slate_ai_orchestrator.py --train
```

### Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ai-maintenance.yml` | Every 4h, 2am, push | Codebase analysis and doc updates |
| `ai-training.yml` | Weekly Sunday 5am | Model training and customization |
| `fork-intelligence.yml` | Every 6h | AI-powered fork analysis |

### Custom Model

SLATE can train a custom model (`slate-custom`) tuned for the codebase:
- Based on `mistral-nemo`
- Trained on SLATE code patterns
- Understands project architecture
- Updated weekly with new code

## Secure AI Training Pipeline

The training pipeline ingests the ENTIRE git repository while ensuring secrets are NEVER included.

### Security Protocol

| Protection | Description |
|------------|-------------|
| Secret Filtering | API keys, tokens, passwords, credentials are redacted |
| PII Scanner | Email, phone, SSN, addresses are filtered |
| File Exclusion | .env, .pem, credentials.json are excluded |
| Commit Sanitization | Author emails are redacted (except known safe domains) |
| Local Only | Trained models are NEVER distributed |

### Training Pipeline Commands

```powershell
# Collect training data (with secret filtering)
.\.venv\Scripts\python.exe slate/slate_training_pipeline.py --collect

# Validate training data is secret-free
.\.venv\Scripts\python.exe slate/slate_training_pipeline.py --validate

# Train custom model locally
.\.venv\Scripts\python.exe slate/slate_training_pipeline.py --train

# Show pipeline status
.\.venv\Scripts\python.exe slate/slate_training_pipeline.py --status
```

## AI Task Scheduler

Intelligently schedules AI tasks across dual GPUs for maximum efficiency.

### Features

- Priority-based task queue
- GPU-aware task placement
- Model warmup optimization (keeps hot models loaded)
- Batch processing for similar task types
- Dependency-aware sequencing

### Scheduler Commands

```powershell
# View scheduler status and GPU state
.\.venv\Scripts\python.exe slate/slate_ai_scheduler.py --status

# View task queue
.\.venv\Scripts\python.exe slate/slate_ai_scheduler.py --queue

# Add task to queue
.\.venv\Scripts\python.exe slate/slate_ai_scheduler.py --add "code_review:Review recent changes"

# Run scheduled tasks
.\.venv\Scripts\python.exe slate/slate_ai_scheduler.py --run --max-tasks 10

# Generate optimal schedule
.\.venv\Scripts\python.exe slate/slate_ai_scheduler.py --schedule
```

## Workflow Coordinator

Coordinates AI-powered GitHub Actions workflows for intelligent sequencing.

### Commands

```powershell
# View coordinator status
.\.venv\Scripts\python.exe slate/slate_workflow_coordinator.py --status

# Generate execution plan
.\.venv\Scripts\python.exe slate/slate_workflow_coordinator.py --plan

# Dispatch scheduled workflows
.\.venv\Scripts\python.exe slate/slate_workflow_coordinator.py --dispatch

# Analyze workflow efficiency
.\.venv\Scripts\python.exe slate/slate_workflow_coordinator.py --optimize
```

### Optimal Workflow Sequence

```
Phase 1: Training     → ai-training.yml (model updates first)
Phase 2: Maintenance  → ai-maintenance.yml, fork-intelligence.yml (parallel)
Phase 3: Agentic      → agentic.yml (task execution with updated models)
Phase 4: Validation   → ci.yml, nightly.yml (parallel)
Phase 5: Services     → service-management.yml (always last)
```

## Kubernetes Deployment (Containerized Local Cloud)

SLATE runs as a complete containerized local cloud in Kubernetes. The entire system is deployed as microservices with full integration.

### Quick Deploy

```powershell
# Deploy SLATE to Kubernetes
.\k8s\deploy.ps1 -Environment local

# Check status
.\k8s\status.ps1

# Access dashboard
kubectl port-forward -n slate svc/slate-dashboard-svc 8080:8080
# Open: http://localhost:8080
```

### K8s Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Ingress (slate.local)                        │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
    ┌──────────────────────────┼──────────────────────────────────┐
    │                          │                                  │
    ▼                          ▼                                  ▼
┌─────────────┐     ┌─────────────────┐     ┌──────────────────────┐
│  Dashboard  │     │  Agent Router   │     │  Autonomous Loop     │
│  (HPA 2-6)  │     │    (2 pods)     │     │   (1 pod + GPU)      │
└──────┬──────┘     └────────┬────────┘     └──────────┬───────────┘
       │                     │                         │
       └─────────────────────┼─────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
   ┌──────────┐       ┌──────────┐       ┌──────────────┐
   │  Ollama  │       │ ChromaDB │       │ GitHub Runner│
   │  (GPU)   │       │ (Vector) │       │   (GPU)      │
   └──────────┘       └──────────┘       └──────────────┘
```

### Services & Ports

| Service | K8s Service | Port | Purpose |
|---------|-------------|------|---------|
| Dashboard | `slate-dashboard-svc` | 8080 | Full UI + WebSocket + K8s API |
| Ollama | `ollama-svc` | 11434 | Local LLM inference |
| ChromaDB | `chromadb-svc` | 8000 | Vector store for RAG |
| Agent Router | `slate-agent-router-svc` | 8081 | Task routing |
| Autonomous | `slate-autonomous-svc` | 8082 | Self-healing loop |
| Copilot Bridge | `slate-copilot-bridge-svc` | 8083 | VS Code integration |
| Workflow | `slate-workflow-svc` | 8084 | Task lifecycle |
| Metrics | `slate-metrics-svc` | 9090 | Prometheus scrape |

### K8s Integration API

When running in Kubernetes, the dashboard exposes K8s-aware endpoints:

```powershell
# Check K8s service health
curl http://localhost:8080/api/k8s/status

# List all SLATE services
curl http://localhost:8080/api/k8s/services

# Check specific service
curl http://localhost:8080/api/k8s/health/ollama

# Get pod info
curl http://localhost:8080/api/k8s/pod
```

### Deployment Methods

```powershell
# Kustomize (recommended)
kubectl apply -k k8s/

# Environment-specific
kubectl apply -k k8s/overlays/local/   # Minikube/kind
kubectl apply -k k8s/overlays/dev/     # Development
kubectl apply -k k8s/overlays/prod/    # Production

# Helm
helm install slate ./helm -n slate --create-namespace
helm upgrade slate ./helm -n slate -f custom-values.yaml
```

### Key Files

| File | Purpose |
|------|---------|
| `k8s/slate-dashboard.yaml` | Full dashboard deployment with WebSocket |
| `k8s/agentic-system.yaml` | Agent router, autonomous loop, bridges |
| `k8s/ml-pipeline.yaml` | Training CronJobs, model preloading |
| `k8s/runners.yaml` | GitHub Actions runners |
| `slate/k8s_integration.py` | K8s-aware service discovery |
| `helm/values.yaml` | Helm configuration |

## Project Structure

```text
slate/             # Core SLATE engine modules
agents/            # Dashboard server and legacy agent code (deprecated)
slate_core/        # Shared infrastructure (locks, memory, GPU scheduler)
specs/             # Active specifications
src/               # Source code (backend/frontend)
tests/             # Test suite
skills/            # Claude Code skill definitions
commands/          # Claude Code command help
hooks/             # Claude Code automation hooks
.claude-plugin/    # Claude Code plugin manifest
.specify/          # Constitution, memory, feedback
.slate_tech_tree/  # Tech tree state (tech_tree.json)
.slate_changes/    # Detected code changes and snapshots
.slate_nemo/       # Nemo knowledge base and training sessions
.slate_errors/     # Error logs with context
.slate_index/      # ChromaDB vector index
.slate_prompts/    # Ingested prompts and intent learning data
```

## Commands

```powershell
# Start SLATE (dashboard + runner + workflow monitor)
.\.venv\Scripts\python.exe slate/slate_orchestrator.py start

# Check all services status
.\.venv\Scripts\python.exe slate/slate_orchestrator.py status

# Stop all SLATE services
.\.venv\Scripts\python.exe slate/slate_orchestrator.py stop

# Quick system status (auto-detects GPU, services)
.\.venv\Scripts\python.exe slate/slate_status.py --quick

# Workflow health (stale tasks, abandoned, duplicates)
.\.venv\Scripts\python.exe slate/slate_workflow_manager.py --status

# Run tests
.\.venv\Scripts\python.exe -m pytest tests/ -v

# Lint
ruff check .
```

## Code Style

- Python: Type hints required. Google-style docstrings. Use `Annotated` for tool parameters.
- Imports: Add `WORKSPACE_ROOT` to `sys.path` when importing cross-module.
- Task files: Always use `slate_core/file_lock.py` for `current_tasks.json` (prevents race conditions).

## UI & Design System (Watchmaker Aesthetic)

All UI and image design follows the **Watchmaker Design Philosophy** (spec 012):

### Core Principles
| Principle | Description |
|-----------|-------------|
| **Precision** | Every pixel serves a purpose. 4px grid alignment. No arbitrary elements. |
| **Mechanism** | Users see the system working — animated gears, flow lines, visible connections. |
| **Depth** | Information in discoverable layers (Surface → Mechanism → Components → Internals → Core). |
| **Function** | Every UI element serves a specific purpose, like watch complications. |
| **Craft** | Beauty emerges from functional perfection, not decoration. |

### Visual Components
- **Gear Icons**: Rotating when active, indicating processing
- **Status Jewels**: Colored gems (green=active, amber=pending, red=error)
- **Flow Lines**: Animated stroke-dasharray showing data paths
- **3D Cards**: Depth on hover with perspective transforms
- **Schematic Layout**: Blueprint-style organization with visible connections

### Design Tokens (LOCKED)
```css
/* Primary: Anthropic-inspired warm rust */
--slate-primary: #B85A3C;
/* Blueprint: Technical precision */
--blueprint-bg: #0D1B2A;
--blueprint-grid: #1B3A4B;
/* Typography: System fonts only */
--font-display: 'Segoe UI', 'Inter', system-ui, sans-serif;
--font-mono: 'Consolas', 'JetBrains Mono', monospace;
/* Grid: Precision alignment */
--grid-unit: 4px;
```

### 3D Dashboard Structure
```
Z=-200: Background gears (decorative, subtle rotation)
Z=-100: Blueprint grid
Z=-50:  Connection lines (animated data flows)
Z=0:    Primary UI components
Z=50:   Floating elements (tooltips, modals)
Z=100:  Overlays (notifications)
```

### Schematic-Based Organization
All information structures use schematic/blueprint layout:
- **Hierarchy**: Tree views with nested containers
- **Circuit**: Nodes connected by flow lines
- **Dataflow**: Input → Processing → Output pipelines

See: `specs/007-slate-design-system/`, `specs/012-watchmaker-3d-dashboard/`

## Security Architecture — LOCAL ONLY

- **All servers bind to `127.0.0.1` only** — never `0.0.0.0`
- No external network calls unless explicitly requested by user
- ActionGuard (`slate/action_guard.py`) validates all actions
- Content Security Policy enforced — no external CDN/fonts
- Rate limiting active on dashboard API endpoints

### SDK Source Guard (Trusted Publishers Only)

SDKSourceGuard (`slate/sdk_source_guard.py`) enforces that ALL packages come from trusted primary sources:

| Trusted Source | Examples |
|----------------|----------|
| Microsoft | azure-*, onnxruntime |
| NVIDIA | nvidia-cuda-*, triton |
| Anthropic | anthropic SDK |
| Meta/Facebook | torch, torchvision |
| Google | tensorflow, jax |
| Hugging Face | transformers, datasets |
| Python Foundation | pip, setuptools |

```powershell
# Check SDK security status
.\.venv\Scripts\python.exe slate/sdk_source_guard.py --report

# Validate a specific package
.\.venv\Scripts\python.exe slate/sdk_source_guard.py --validate "some-package"

# Check all requirements.txt packages
.\.venv\Scripts\python.exe slate/sdk_source_guard.py --check-requirements
```

**Blocked Sources:**
- Unknown PyPI publishers
- Untrusted GitHub organizations
- Known typosquatting packages
- Suspicious naming patterns

## Task Execution System

SLATE uses GitHub Actions with a self-hosted runner for all task execution. The deprecated agent system (ALPHA, BETA, GAMMA, DELTA) has been replaced by workflow-based execution.

Tasks in `current_tasks.json` are processed by GitHub Actions workflows.
Use `assigned_to: "workflow"` for workflow-based execution.

## Task Management

- Task queue: `current_tasks.json` (use FileLock for atomic access)
- Priorities: `DO_THIS_NOW.txt` for immediate priorities
- Tech tree: `.slate_tech_tree/tech_tree.json` directs development focus
- Spec lifecycle: `draft → specified → planned → tasked → implementing → complete`

## GitHub Project Boards

SLATE uses GitHub Projects V2 for task tracking and workflow management. The KANBAN board is the primary source for workflow execution.

### Project Board Mapping

| # | Board | Purpose |
|---|-------|---------|
| 5 | **KANBAN** | Primary workflow source - active tasks |
| 7 | **BUG TRACKING** | Bug-related issues and fixes |
| 8 | **ITERATIVE DEV** | Pull requests and iterations |
| 10 | **ROADMAP** | Completed features and enhancements |
| 4 | **PLANNING** | Planning and design tasks |
| 6 | **FUTURE RELEASE** | Future version items |

### Project Board Commands

```powershell
# Check all project boards status
.\.venv\Scripts\python.exe slate/slate_project_board.py --status

# Update all boards from current_tasks.json
.\.venv\Scripts\python.exe slate/slate_project_board.py --update-all

# Sync KANBAN to local tasks
.\.venv\Scripts\python.exe slate/slate_project_board.py --sync

# Push pending tasks to KANBAN
.\.venv\Scripts\python.exe slate/slate_project_board.py --push
```

### Auto-Categorization

Tasks are automatically routed to boards by keywords:
- **BUG TRACKING**: bug, fix, crash, error, broken
- **ROADMAP**: feat, add, new, implement, create
- **PLANNING**: plan, design, architect, research
- **KANBAN**: default for active work

### Workflow Automation

The `project-automation.yml` workflow:
- Runs every 30 minutes (scheduled)
- Auto-adds issues/PRs to boards based on labels
- PII scanning before public board exposure
- Bidirectional sync with `current_tasks.json`

## GitHub Discussions

SLATE integrates GitHub Discussions for community engagement and feature ideation.

### Discussion Categories

| Category | Routing | Action |
|----------|---------|--------|
| Announcements | None | Informational only |
| Ideas | ROADMAP board | Creates tracking issue |
| Q&A | Metrics tracking | Monitors response time |
| Show and Tell | Engagement log | Community showcase |
| General | Engagement log | Community discussion |

### Discussion Commands

```powershell
# Check discussion system status
.\.venv\Scripts\python.exe slate/slate_discussion_manager.py --status

# List unanswered Q&A discussions
.\.venv\Scripts\python.exe slate/slate_discussion_manager.py --unanswered

# Sync actionable discussions to task queue
.\.venv\Scripts\python.exe slate/slate_discussion_manager.py --sync-tasks

# Generate engagement metrics
.\.venv\Scripts\python.exe slate/slate_discussion_manager.py --metrics
```

### Discussion Automation

The `discussion-automation.yml` workflow:
- Triggers on discussion events (create, edit, label, answer)
- Hourly scheduled processing for metrics
- PII scanning before processing
- Routes Ideas/Bugs to issue tracker
- Tracks Q&A response times

## Test-Driven Development (Constitution Mandate)

All code changes must be accompanied by tests. Target 50%+ coverage for `slate/` and `slate_core/`.

```text
1. WRITE TEST → failing test defining expected behavior
2. RUN TEST → verify it fails (red)
3. IMPLEMENT → minimum code to pass
4. RUN TEST → verify it passes (green)
5. REFACTOR → clean up while keeping tests green
```

## Dual-Repository System

SLATE uses a dual-repo model for development and distribution:

```
SLATE (origin)         = Main repository (the product)
       ↑
       │ contribute-to-main.yml
       │
SLATE-BETA (beta)      = Developer fork (where development happens)
```

### Git Remote Configuration

```powershell
# Check remotes
git remote -v
# Should show:
# origin  https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E.git
# beta    https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E-BETA.git
```

### Development Workflow (BETA → SLATE)

1. **Develop on BETA branch**
   ```powershell
   git checkout -b feature/my-feature
   # Make changes, commit
   ```

2. **Sync BETA with SLATE main** (get latest)
   ```powershell
   git fetch origin
   git merge origin/main
   ```

3. **Push to BETA**
   ```powershell
   git push beta HEAD:main
   ```

4. **Contribute to SLATE main**
   - Run the `contribute-to-main.yml` workflow on BETA
   - OR push directly if you have access:
   ```powershell
   git push origin HEAD:main
   ```

### Required Setup

1. **MAIN_REPO_TOKEN** secret on BETA repo
   - Settings → Secrets → Actions → Add `MAIN_REPO_TOKEN`
   - Use a PAT with `repo` and `workflow` scope

2. **GitHub CLI with workflow scope**
   ```powershell
   gh auth login --scopes workflow
   ```

## Fork Contributions

SLATE uses a secure fork validation system for external contributions:

1. Fork the repository from https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E.
2. Create a local SLATE installation with your own git
3. Run `python slate/slate_fork_manager.py --init` to set up
4. Make changes following SLATE prerequisites
5. Submit PR - it will be validated by fork-validation workflow

**Required checks before PR merge:**
- Security Gate (no workflow modifications)
- SDK Source Guard (trusted publishers only)
- SLATE Prerequisites (core modules valid)
- ActionGuard Audit (no security bypasses)
- Malicious Code Scan (no obfuscated code)

## GitHub Integration

Repository: https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E.

- Branch protection on `main` requires reviews and passing checks
- CODEOWNERS enforces review requirements for critical paths
- All PRs must pass SLATE compatibility checklist

## GitHub Pages

SLATE has a public feature page deployed via GitHub Pages.

| Resource | URL |
|----------|-----|
| **Website** | https://synchronizedlivingarchitecture.github.io/S.L.A.T.E/ |
| **Source** | `docs/pages/` |
| **Workflow** | `pages.yml` |

### Pages Structure

```text
docs/pages/
├── index.html      # Main landing/feature page
├── 404.html        # Custom 404 page
└── assets/
    └── slate-logo-v2.svg
```

The pages match the SLATE dashboard theme (glassmorphism, organic earth tones, Segoe UI).

### Deployment

Pages deploy automatically on push to `main` when files in `docs/pages/` change:
- Uses GitHub Actions `deploy-pages@v4`
- Notifies SLATE system on successful deployment
- Status tracked in `.slate_identity/pages_status.json`

## GitHub Workflow System

SLATE uses GitHub as a **task execution platform**. The GitHub ecosystem manages the entire project lifecycle: issues → tasks → workflow execution → PR completion.

### Workflow Architecture

```
GitHub Issues/Tasks → current_tasks.json → Workflow Dispatch → Self-hosted Runner
        ↓                     ↓                   ↓                    ↓
    Tracking              Task Queue          CI/CD Jobs          AI Execution
                                                  ↓                    ↓
                                              Validation     →    PR/Commit
```

### Workflow Files

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ci.yml` | Push/PR | Smoke tests, lint, unit tests, security |
| `slate.yml` | Core path changes | Tech tree, task queue, validation |
| `nightly.yml` | Daily 4am UTC | Full test suite, dependency audit |
| `cd.yml` | Tags/main | Build EXE, create releases |
| `fork-validation.yml` | Fork PRs | Security gate |
| `pages.yml` | docs/pages/** changes | Deploy GitHub Pages feature site |

### Auto-Configured Runner

SLATE **auto-detects** and configures the GitHub Actions runner. No manual setup required:

```powershell
# Auto-detect runner, GPUs, and GitHub state
.\.venv\Scripts\python.exe slate/slate_runner_manager.py --status

# Auto-configure hooks, environment, and labels
.\.venv\Scripts\python.exe slate/slate_runner_manager.py --setup

# Dispatch a workflow for execution
.\.venv\Scripts\python.exe slate/slate_runner_manager.py --dispatch "ci.yml"
```

The runner manager automatically:
- **Detects** GPU configuration (count, architecture, CUDA capability)
- **Creates** pre-job hooks for environment setup
- **Generates** labels (self-hosted, slate, gpu, cuda, blackwell, multi-gpu)
- **Configures** SLATE workspace paths and venv

### Workflow Management

```powershell
# Analyze task workflow health
.\.venv\Scripts\python.exe slate/slate_workflow_manager.py --status

# Auto-cleanup stale/abandoned/duplicate tasks
.\.venv\Scripts\python.exe slate/slate_workflow_manager.py --cleanup

# Check if workflow can accept new tasks
.\.venv\Scripts\python.exe slate/slate_workflow_manager.py --enforce
```

Automatic rules:
- **Stale** (in-progress > 4h) → auto-reset to pending
- **Abandoned** (pending > 24h) → flagged for review
- **Duplicates** → auto-archived
- **Max concurrent** → 5 tasks before blocking

## System Auto-Detection

SLATE auto-detects all components on startup:

```powershell
# Full system auto-detection
.\.venv\Scripts\python.exe slate/slate_status.py --quick

# Runtime integration check
.\.venv\Scripts\python.exe slate/slate_runtime.py --check-all

# JSON for automation pipelines
.\.venv\Scripts\python.exe slate/slate_status.py --json
```

### Auto-Detected Components

| Component | Detection Method | Auto-Config |
|-----------|------------------|-------------|
| Python | Version check | Validates 3.11+ |
| GPU | nvidia-smi | Compute cap, memory, architecture |
| PyTorch | Import + CUDA | Version, device count |
| Ollama | Service query | Model list |
| GitHub Runner | .runner file | Labels, hooks, service |
| venv | Path check | Activation |

## System Services

| Service | Port | Auto-Checked By |
|---------|------|-----------------|
| Dashboard | 8080 | `slate/slate_status.py` |
| Ollama | 11434 | `slate/slate_status.py` |
| Foundry Local | 5272 | `slate/slate_status.py` |
| GitHub Runner | N/A | `slate/slate_runner_manager.py` |

## Quick Reference

```powershell
# Full system status (auto-detects everything)
.\.venv\Scripts\python.exe slate/slate_status.py --quick

# Workflow health
.\.venv\Scripts\python.exe slate/slate_workflow_manager.py --status

# Runner status and auto-config
.\.venv\Scripts\python.exe slate/slate_runner_manager.py --status

# Run tests
.\.venv\Scripts\python.exe -m pytest tests/ -v

# Start dashboard
.\.venv\Scripts\python.exe agents/slate_dashboard_server.py
```
