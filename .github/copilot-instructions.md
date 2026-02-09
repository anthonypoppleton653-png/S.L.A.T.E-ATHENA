# S.L.A.T.E. Copilot Instructions
# Modified: 2026-02-10T04:30:00Z | Author: Claude Opus 4.5 | Change: Add SLATE Operator Behavior with permission bypass and ActionGuard security

## SLATE Operator Behavior — LOCKED PROFILE

**This workspace runs with SLATE Operator Behavior enabled.**

Claude Code operates in **permission bypass mode** with security enforced by ActionGuard (Python-side).
This is NOT a reduction in security — it's a shift from Claude-side confirmation to Python-side validation.

### Behavior Configuration

```yaml
Profile: slate-operator
Version: 1.0.0
Security: ActionGuard (slate/action_guard.py)
Permissions: Bypass with ActionGuard protection
Runtime: K8s > Docker (container-first)
```

### Configuration Files

| File | Purpose |
|------|---------|
| `.claude/settings.json` | Main config with behavior profile and MCP servers |
| `.claude/settings.local.json` | Permission bypass rules (`Bash(*)`, `Read(*)`, etc.) |
| `.claude/behaviors/slate-operator.md` | Behavior profile definition |
| `.claude/behaviors/slate-protocols.md` | 10 operational protocols (P001-P010) |
| `.claude/hooks.json` | ActionGuard hook integration |

### Permission Bypass (Enabled)

All tool calls are pre-approved:
- `Bash(*)` — Validated by ActionGuard before execution
- `Read(*)`, `Write(*)`, `Edit(*)` — File operations within workspace
- `Glob(*)`, `Grep(*)` — Search operations
- `mcp__slate__*(*)` — All SLATE MCP tools

### Security Model

Despite bypass mode, security is maintained through:
1. **ActionGuard** — Python-side command validation (blocks `rm -rf`, `0.0.0.0`, `eval()`)
2. **PreToolUse Hooks** — Validate Bash/Write before execution
3. **SDK Source Guard** — Only trusted package publishers
4. **Container Isolation** — Commands run in K8s/Docker, not host
5. **K8s RBAC** — Minimal service account permissions

### Operational Protocols (P001-P010)

| Protocol | Trigger | Description |
|----------|---------|-------------|
| **P001-INIT** | Session start | System health check, load instructions |
| **P002-EXECUTE** | Task request | DIAGNOSE → ACT → VERIFY pattern |
| **P003-WORKFLOW** | Queue ops | Task management, stale cleanup |
| **P004-GPU** | GPU ops | Dual-GPU load balancing |
| **P005-SECURITY** | Bash commands | ActionGuard validation |
| **P006-RECOVERY** | Failures | Error recovery and fallback |
| **P007-CODE** | File ops | Read/write/edit operations |
| **P008-GIT** | Git ops | Git operations with safety rules |
| **P009-K8S** | K8s ops | Kubernetes deployment |
| **P010-AUTONOMOUS** | Background | Autonomous task processing |

### MCP Tools (Bypass Enabled)

```json
{
  "permissions": {
    "allow": [
      "mcp__slate__slate_status(*)",
      "mcp__slate__slate_workflow(*)",
      "mcp__slate__slate_orchestrator(*)",
      "mcp__slate__slate_runner(*)",
      "mcp__slate__slate_ai(*)",
      "mcp__slate__slate_runtime(*)",
      "mcp__slate__slate_hardware(*)",
      "mcp__slate__slate_benchmark(*)",
      "mcp__slate__slate_gpu(*)",
      "mcp__slate__slate_claude_code(*)",
      "mcp__slate__slate_spec_kit(*)",
      "mcp__slate__slate_schematic(*)"
    ]
  }
}
```

### Activation

The behavior activates automatically when:
- Working in SLATE workspace (`e:\11132025`)
- `SLATE_BEHAVIOR=operator` environment variable is set
- `.claude/settings.json` has `"behavior": { "profile": "slate-operator" }`

---

## Workspace

**This workspace is a S.L.A.T.E. installation.**
All paths are relative to the workspace root — no hardcoded directories.

- **Repo**: `SynchronizedLivingArchitecture/S.L.A.T.E`
- **Purpose**: Full SLATE SDK, inference pipeline, GPU benchmarking, CI/CD
- **Git**: `origin` → user's fork or `https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E.git`

When install issues are found:
1. Fix the issue in the relevant installer/SDK file
2. Include `# Modified:` timestamp comment per SLATE rules
3. Commit with `fix(installer):` prefix
4. Push to the appropriate branch

## MANDATORY PROTOCOL  Read Before Any Operation

**Every Copilot session MUST begin by running SLATE protocols before performing work.**
This is NOT optional. These protocols exist to ensure system consistency, prevent
regressions, and maintain the integrity of the agentic AI pipeline.

### Session Start Protocol (REQUIRED)
Before ANY code changes, file creation, or task work, execute these in order:
```bash
python slate/slate_status.py --quick          # 1. System health  confirm GPUs, Python, Ollama
python slate/slate_runtime.py --check-all     # 2. Verify all 7 integrations are active
python slate/slate_workflow_manager.py --status # 3. Check task queue  respect completion rules
```

### Pre-Commit Protocol (REQUIRED)
Before committing or suggesting a commit:
```bash
python slate/slate_workflow_manager.py --enforce  # Block if tasks are stale/overloaded
python slate/slate_workflow_manager.py --cleanup  # Archive deprecated/test tasks
```

### Code Edit Rules (ENFORCED)
Every code edit MUST include a timestamp + author comment:
```python
# Modified: YYYY-MM-DDTHH:MM:SSZ | Author: COPILOT | Change: description
```

## Built-In Safeguards (ENFORCED)

SLATE enforces these protections automatically:

1) **ActionGuard** - Blocks dangerous patterns
   - Destructive commands (`rm -rf`, `format`, `del /s`)
   - Network exposure (`0.0.0.0` bindings)
   - Dynamic execution (`eval`, `exec`)
   - External paid API calls

2) **SDK Source Guard** - Trusted publishers only
   - Microsoft, NVIDIA, Meta, Google, Hugging Face
   - Unknown PyPI packages blocked

3) **PII Scanner** - Before GitHub sync
   - API keys, tokens, credentials detected
   - Personal info blocked from public boards

4) **Resource Limits**
   - Max concurrent tasks enforced
   - Stale tasks (>4h) auto-flagged
   - GPU memory monitored per-runner

## System Overview
SLATE (Synchronized Living Architecture for Transformation and Evolution) is a local-first
AI agent orchestration framework. All operations are LOCAL ONLY (127.0.0.1). Version 2.4.0.

Repository: `SynchronizedLivingArchitecture/S.L.A.T.E`
Python: 3.11+ via `.venv` at `<workspace>\.venv\Scripts\python.exe`
Runner: Self-hosted GitHub Actions runner `slate-runner` at `<workspace>\actions-runner`

## SLATE Protocol Commands  Use These, Not Ad-Hoc Commands

### System Health (run FIRST in every session)
```bash
python slate/slate_status.py --quick          # Quick health check
python slate/slate_status.py --json           # Machine-readable status
```

### Runtime Integration Check
```bash
python slate/slate_runtime.py --check-all     # All 7 integrations (Python, GPU, PyTorch, Transformers, Ollama, ChromaDB, venv)
python slate/slate_runtime.py --json          # JSON output
```

### Hardware & GPU Optimization
```bash
python slate/slate_hardware_optimizer.py       # Detect GPUs
python slate/slate_hardware_optimizer.py --optimize       # Apply optimizations
python slate/slate_gpu_manager.py --status     # Dual-GPU load balancing status
python slate/slate_gpu_manager.py --preload    # Preload models to assigned GPUs
```

### Task & Workflow Management
```bash
python slate/slate_workflow_manager.py --status   # Task queue status
python slate/slate_workflow_manager.py --cleanup   # Clean stale/deprecated tasks
python slate/slate_workflow_manager.py --enforce   # Enforce completion before new tasks
```

### Runner & CI/CD
```bash
python slate/slate_runner_manager.py --status  # Runner status
python slate/slate_runner_manager.py --dispatch "ci.yml"  # Dispatch workflow
```

### Service Orchestration
```bash
python slate/slate_orchestrator.py status      # Service status
python slate/slate_orchestrator.py start       # Start all services (dashboard, runner, monitor)
python slate/slate_orchestrator.py stop        # Stop all services
```

### ML / Agentic AI (GPU Inference)
```bash
python slate/ml_orchestrator.py --status       # ML pipeline status
python slate/ml_orchestrator.py --index-now    # Build codebase embedding index (uses ChromaDB)
python slate/ml_orchestrator.py --benchmarks   # Inference benchmarks
python slate/slate_model_trainer.py --status   # SLATE custom model status
python slate/slate_chromadb.py --status        # ChromaDB vector store status
python slate/slate_chromadb.py --index         # Index codebase into ChromaDB
python slate/slate_chromadb.py --search "query" # Semantic search
```

### Autonomous Loops
```bash
python slate/slate_unified_autonomous.py --status   # Autonomous loop status
python slate/slate_unified_autonomous.py --discover  # Discover available tasks
python slate/copilot_slate_runner.py --status        # Copilot runner bridge status
python slate/integrated_autonomous_loop.py --status  # Integrated loop status
```

### Kubernetes Deployment
```bash
python slate/slate_k8s_deploy.py --status            # K8s cluster status
python slate/slate_k8s_deploy.py --deploy             # Deploy manifests
python slate/slate_k8s_deploy.py --health             # Health check all pods
python slate/slate_k8s_deploy.py --logs <component>   # Component logs
python slate/slate_k8s_deploy.py --teardown           # Remove SLATE from cluster
```

### Benchmarks
```bash
python slate/slate_benchmark.py                # System benchmarks (CPU, memory, disk, GPU)
```

### Project Boards
```bash
python slate/slate_project_board.py --status   # GitHub Projects V2 board status
```

## Project Structure
```
slate/              # Core SDK modules (30 Python files)
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
  slate_multi_runner.py     # Multi-runner parallelism
  slate_real_multi_runner.py # Real multi-runner implementation
  slate_runner_benchmark.py # Runner capacity benchmarks
  feature_flags.py          # Feature flag system
  install_tracker.py        # Installation tracking
  runner_cost_tracker.py    # Runner cost tracking
  runner_fallback.py        # Runner fallback logic
  slate_terminal_monitor.py # Terminal activity tracking
  slate_discussion_manager.py # Discussion automation

agents/             # API servers & agent modules
  runner_api.py             # RunnerAPI class (GitHub API integration)
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

.github/
  workflows/                # 19 CI/CD workflow definitions
    ci.yml                  # Main CI: lint, tests, SDK, security, GPU validation
    cd.yml                  # Build & deploy
    slate.yml               # Integration tests
    agentic.yml             # GPU inference & autonomous agent loop
    codeql.yml              # Security analysis
    pr.yml                  # PR validation
    nightly.yml             # Nightly health checks
    docs.yml                # Documentation validation
    fork-validation.yml     # Fork security gate
    contributor-pr.yml      # External contributor PRs
    multi-runner.yml        # Multi-runner parallelism
    docker.yml              # Container builds
    release.yml             # Release management
    # Modified: 2026-02-09T04:30:00Z | Author: COPILOT | Change: Add K8s workflow
    k8s.yml                 # Kubernetes deployment management
  slate.config.yaml         # Master SLATE configuration
```

## Self-Hosted Runner Details
- **Name**: slate-runner
- **Labels**: `[self-hosted, Windows, X64, slate, gpu, cuda, gpu-2, blackwell]`
- **Work folder**: `slate_work`
- **GPUs**: 2x NVIDIA GeForce RTX 5070 Ti (Blackwell, compute 12.0, 16GB each)
- **Pre-job hook**: Sets `CUDA_VISIBLE_DEVICES=0,1`, SLATE env vars, Python PATH
- **SLATE Custom Models**: slate-coder (12B), slate-fast (3B), slate-planner (7B)

## Workflow Conventions
- All jobs use `runs-on: [self-hosted, slate]`
- Default shell: `powershell` (CI) / `pwsh` 7.5+ (local dev — installed via `dotnet tool install --global PowerShell`)
- Python path step: `"$env:GITHUB_WORKSPACE\.venv\Scripts" | Out-File -Append $env:GITHUB_PATH`
- YAML paths use single quotes to avoid backslash escape issues

## Agent Routing (from slate.config.yaml)
| Pattern | Agent | Role | GPU |
|---------|-------|------|-----|
| implement, code, build, fix | ALPHA | Coding | Yes |
| test, validate, verify, coverage | BETA | Testing | Yes |
| analyze, plan, research, document | GAMMA | Planning | No |
| claude, mcp, sdk, integration | DELTA | External Bridge | No |
| diagnose, investigate, troubleshoot, interactive, explain | COPILOT_CHAT | Chat Participant | No |
| complex, multi-step | COPILOT | Full orchestration | Yes |

## @slate Participant as Subagent (COPILOT_CHAT)
The @slate VS Code chat participant is registered as the **COPILOT_CHAT** agent in the
SLATE agent registry. This enables bidirectional task flow between the autonomous loop
and the interactive chat interface.

### Bridge Architecture
```
Autonomous Loop ──▶ copilot_agent_bridge.py ──▶ .slate_copilot_bridge.json
                                                       │
@slate Participant ◀── slate_agentBridge tool ◀────────┘
       │
       ▼
.slate_copilot_bridge_results.json ──▶ Autonomous Loop picks up results
```

### Bridge Commands
```bash
python slate/copilot_agent_bridge.py --status     # Bridge health
python slate/copilot_agent_bridge.py --pending     # Pending tasks for @slate
python slate/copilot_agent_bridge.py --results     # Completed results
python slate/copilot_agent_bridge.py --cleanup     # Clean stale entries
```

### How It Works
1. Autonomous loop classifies a task matching `diagnose|investigate|troubleshoot|interactive|explain`
2. Task is routed to COPILOT_CHAT agent → enqueued to `.slate_copilot_bridge.json`
3. @slate participant polls via `slate_agentBridge` tool (action: 'poll')
4. Participant processes the task using its full tool suite (20+ tools)
5. Results written back via `slate_agentBridge` tool (action: 'complete')
6. Copilot Runner picks up results and updates task status

## Security Rules (ENFORCED by ActionGuard)
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

## When Copilot Does NOT Run Protocols
If you skip the mandatory protocols above, you risk:
1. **Stale task overload**  creating new tasks when existing ones need completion first
2. **Integration drift**  editing code that depends on an offline service (Ollama, ChromaDB)
3. **Security violations**  introducing `0.0.0.0` bindings or blocked patterns unchecked
4. **Version mismatch**  SDK version diverging from pyproject.toml
5. **GPU misconfiguration**  wrong model placement on dual-GPU system

**Always run the protocols. They take <5 seconds and prevent hours of debugging.**

## Document Evolution Rules (ENFORCED)

These instruction files are **append-only living documents**. All protocol files
(`copilot-instructions.md`, `AGENTS.md`, `slate.config.yaml`) follow strict evolution rules:

1. **ADDITIVE ONLY** — New behaviors, sections, and rules are APPENDED. Never overwrite,
   remove, or replace existing behaviors unless explicitly deprecated via `# DEPRECATED:`.
2. **Preserve All Existing Rules** — Every existing section, behavior, safeguard, and protocol
   remains intact. New additions extend the system, they do not contradict or supersede.
3. **Timestamp Every Change** — Each edit includes `# Modified:` with ISO timestamp, author, and
   a change description that says what was ADDED, not what was "updated" or "replaced".
4. **No Silent Overwrites** — If a behavior needs to change, add a NEW section that augments
   the original. Reference the original section. Never delete the original.
5. **Deprecation Protocol** — To retire a behavior: add `# DEPRECATED: YYYY-MM-DD | Reason:`
   above the section. The section stays in-document for history. A new section replaces it.
6. **Version Accumulation** — The document grows over time. This is intentional. It forms the
   complete behavioral history of the system.

## Chat Participant Enforcement (MANDATORY)

SLATE provides three VS Code chat participants. All agents and subagents MUST use them
aggressively for execution rather than falling back to raw terminal commands or manual work.

### Available Chat Participants

| Participant | Extension | Purpose | When to Use |
|-------------|-----------|---------|-------------|
| `@slate` | `slate.slate-copilot` | SLATE system ops — runner, CI, GPU, orchestrator, specs, agents | System management, health checks, deployments, agent routing |
| `@vscode` | Built-in | VS Code editor operations — files, settings, extensions, debugging | File operations, editor configuration, extension management |

### @slate Tools (20+ LM Tools)

| Tool | Purpose |
|------|--------|
| `slate_systemStatus` | System health check |
| `slate_runtimeCheck` | Integration verification |
| `slate_hardwareInfo` | GPU detection & optimization |
| `slate_runnerStatus` | Runner management |
| `slate_orchestrator` | Service lifecycle |
| `slate_workflow` | Task management |
| `slate_benchmark` | Performance benchmarks |
| `slate_securityAudit` | Security scanning |
| `slate_specKit` | Spec processing, wiki generation, roadmap |
| `slate_planContext` | Compressed context for token efficiency |
| `slate_devCycle` | Development stage management |
| `slate_codeGuidance` | Stage-aligned code guidance |
| `slate_agentBridge` | Autonomous loop ↔ chat bridge |
| `slate_autonomous` | Autonomous task execution |
| `slate_executeWork` | Direct work execution |
| `slate_handoff` | Task delegation between agents |
| `slate_forkCheck` | Fork sync and security |
| `slate_gpuManager` | Dual-GPU load balancing |
| `slate_learningProgress` | Learning/XP tracking |
| `slate_runCommand` | Escape hatch — run any SLATE Python script |
| `slate_kubernetes` | K8s cluster status, deploy, health, logs, teardown |

### Enforcement Rules

1. **Subagents MUST use `@slate`** — When delegating to `runSubagent` with agent name `slate`,
   the subagent has full access to all 20+ SLATE tools. Always prefer `@slate` over raw
   terminal commands for SLATE operations.
2. **Spec work MUST use `slate_specKit`** — Never process specs manually. Use
   `@slate /specs` or invoke `slate_specKit` tool directly.
3. **System operations MUST use `@slate`** — Health checks, runner management, CI dispatch,
   GPU management — all go through `@slate` participant, not ad-hoc Python commands.
4. **Editor operations SHOULD use `@vscode`** — File management, settings changes, extension
   installs — prefer `@vscode` participant when available.
5. **Multi-participant chaining** — Complex tasks should chain participants:
   - `@slate /status` → verify system health
   - `@slate /specs` → process specifications
   - `@vscode` → apply editor-level changes
6. **Never bypass participants for covered operations** — If a participant tool exists for the
   operation, USE IT. Don't fall back to manual terminal unless the tool fails.

### Aggressive Execution Patterns

Participants are NOT optional helpers — they are the PRIMARY execution interface.
Every task should be routed through the appropriate participant FIRST.

```
Task Arrives → Classify Intent → Route to Participant → Execute via Tools → Report
                                        ↓
                            @slate (system/infra/specs/agents)
                            @vscode (editor/files/settings)
                            Terminal (ONLY as fallback)
```

**Escalation Order:**
1. Try participant tool first (e.g., `slate_workflow` for task management)
2. Try participant command second (e.g., `@slate /status`)
3. Try subagent delegation third (e.g., `runSubagent` with `slate` agent)
4. Fall back to terminal ONLY if all participant paths fail

### Subagent Delegation with Participants

When using `runSubagent`, always specify the appropriate agent:

| Task Type | Subagent | Participant Used |
|-----------|----------|------------------|
| System health, runner, CI | `slate` | `@slate` |
| Spec processing, roadmap | `slate` | `@slate /specs` |
| Agent management, autonomous loops | `slate` | `@slate /agents` |
| Multi-step complex operations | `slate` | `@slate` (full orchestration) |
| Code research, file analysis | Default | `@vscode` |
| Planning, architecture | `Plan` | N/A |

## Background Agent Delegation (ENFORCED)
# Modified: 2026-02-08T12:00:00Z | Author: COPILOT | Change: Add background agent delegation as standard pattern for subagents

SLATE agents and subagents can delegate long-running, multi-step, or autonomous tasks to
**background agents**. Background agents run asynchronously in a separate session, freeing
the interactive chat for other work. This is the STANDARD pattern for complex operations.

### When to Use Background Agents

| Scenario | Use Background Agent? | Reason |
|----------|-----------------------|--------|
| Multi-step code changes across many files | Yes | Long-running, non-interactive |
| Full CI/CD pipeline dispatch + monitoring | Yes | Async wait for results |
| Autonomous task loop execution | Yes | Runs independently |
| Docker build + K8s deploy + verify | Yes | Multi-stage pipeline |
| Codebase indexing (ChromaDB) | Yes | Long-running GPU work |
| Quick status check | No | Fast, interactive |
| Single file edit | No | Immediate feedback needed |
| Interactive troubleshooting | No | Requires user dialogue |

### Delegation Pattern

```
User Request → Classify Complexity → Route Decision
                                          │
                    ┌─────────────────────┤
                    ▼                     ▼
              Interactive              Background
              (immediate)             (async session)
                    │                     │
              @slate / terminal      "Delegate to Background Agent"
                    │                     │
              Direct response        Session continues independently
                                          │
                                     Reports back via:
                                     - Session completion notification
                                     - Bridge results file
                                     - Workflow status update
```

### Subagent → Background Agent Escalation

Subagents (via `runSubagent`) can escalate to background agents when:

1. **Task exceeds interactive timeout** — Work that takes >2 minutes
2. **Multi-branch operations** — Push to main, build Docker, deploy K8s, verify
3. **Autonomous loops** — Task discovery + execution cycles
4. **Full pipeline runs** — Lint → test → build → deploy → health check
5. **Batch operations** — Processing multiple specs, files, or workflows

### Background Agent Capabilities

Background agents have FULL access to:
- All SLATE protocol commands (`slate_status`, `slate_runtime`, etc.)
- Terminal execution (`run_in_terminal` with `isBackground=true`)
- File operations (read, write, edit, create)
- Git operations (commit, push, branch management)
- Docker/K8s operations (build, deploy, teardown)
- GitHub API (workflow dispatch, PR creation, issue management)
- All `@slate` participant tools (via subagent delegation)

### Enforcement Rules

1. **Complex multi-step tasks SHOULD use background agents** — When a task involves 3+
   sequential stages (e.g., edit → commit → push → build → deploy → verify), delegate
   to a background agent.
2. **Subagents CAN delegate to background agents** — A subagent running via `runSubagent`
   can itself request background delegation for long-running sub-tasks.
3. **Background agents MUST follow SLATE protocols** — Session start protocol, pre-commit
   protocol, code edit rules, and security safeguards all apply.
4. **Background agents MUST update workflow status** — Use `slate_workflow_manager.py` to
   track task progress and completion.
5. **Results reporting** — Background agents report results via:
   - Session completion summary
   - `.slate_copilot_bridge_results.json` for autonomous loop integration
   - `current_tasks.json` status updates
6. **Never fire-and-forget** — Always ensure the background agent has clear success/failure
   criteria and reporting mechanisms.

### Integration with Existing Patterns

Background agent delegation augments (does NOT replace) the existing escalation order:

```
1. Participant tool (e.g., slate_workflow, slate_specKit)
2. Participant command (e.g., @slate /status)
3. Subagent delegation (runSubagent with 'slate')
4. Background agent delegation (for long-running/async work)
5. Terminal (ONLY as last resort fallback)
```

### Subagent Delegation Table (AUGMENTED)

| Task Type | Subagent | Execution Mode | When Background |
|-----------|----------|----------------|-----------------|
| System health, runner, CI | `slate` | Interactive | CI dispatch + wait |
| Spec processing, roadmap | `slate` | Interactive | Batch spec processing |
| Agent management, autonomous loops | `slate` | **Background** | Always (long-running) |
| Multi-step complex operations | `slate` | **Background** | Always (multi-stage) |
| Code research, file analysis | Default | Interactive | Large codebase scan |
| Planning, architecture | `Plan` | Interactive | Multi-repo analysis |
| Docker build + deploy | `slate` | **Background** | Always (pipeline) |
| Full test suite | `slate` | **Background** | Coverage + reporting |
| Git operations (push + PR) | `slate` | **Background** | Push + CI wait |

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

## Adaptive Instruction Layer (K8s-Driven) — MANDATORY
# Modified: 2026-02-09T06:00:00Z | Author: COPILOT | Change: Add adaptive instruction layer — instructions are now K8s-driven

SLATE instructions are no longer static files. They are **dynamically generated and controlled**
by the Kubernetes-driven Adaptive Instruction Layer. The K8s ConfigMap `slate-instructions`
is the **source of truth** for all agent and Copilot instruction behaviors.

### Architecture

```
┌───────────────────────────────────────────────────────────────────────┐
│                   ADAPTIVE INSTRUCTION LAYER                          │
│                                                                       │
│  System State        Instruction           K8s ConfigMap              │
│  (GPU, K8s, services) → Controller     →  slate-instructions         │
│                        (adaptive_          ├── active-state.yaml      │
│  GitHub Workflows  →   instructions.py)    ├── instruction-block.md   │
│  (instructions.yml)                        ├── copilot-rules.yaml     │
│                                            ├── agent-prompts.yaml     │
│  @slate Extension  ←  Instruction API      └── mcp-tools.yaml        │
│  (queries live      ← (port 8085)                                     │
│   instructions)                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### Operating Modes (Set by Controller)

| Mode | Condition | Behavior |
|------|-----------|----------|
| `NORMAL` | All systems healthy | Full operations, all agents active |
| `DEGRADED` | Some services down | Adjust routing, warn about unavailable tools |
| `MAINTENANCE` | K8s pods unhealthy | Focus on restoration, limit new tasks |
| `AUTONOMOUS` | Autonomous loop active | Coordinate with AI loop, poll bridge |
| `EMERGENCY` | K8s cluster unreachable | Recovery mode, minimal operations |
| `DEVELOPMENT` | Active coding session | Prioritize coding/testing agents |

### Agent Availability (Set by Controller)

| Level | Condition | Available Agents |
|-------|-----------|-----------------|
| `full` | GPU + Ollama + K8s ready | ALPHA, BETA, GAMMA, DELTA, COPILOT |
| `gpu-only` | GPU available, Ollama down | ALPHA (no LLM), BETA (no LLM) |
| `cpu-only` | No GPU access | GAMMA, DELTA only |
| `minimal` | Cluster unreachable | Status/health checks only |

### Protocol Commands

```bash
# Adaptive instruction management
python slate/adaptive_instructions.py --status        # Current instruction state
python slate/adaptive_instructions.py --evaluate      # Evaluate system & generate context
python slate/adaptive_instructions.py --sync           # Full sync: evaluate + apply to K8s
python slate/adaptive_instructions.py --get-context    # Get context-aware instruction block
python slate/adaptive_instructions.py --get-active     # Get active set (K8s → local fallback)
python slate/adaptive_instructions.py --apply          # Push instructions to ConfigMap
python slate/adaptive_instructions.py --json           # JSON output
```

### @slate Extension Integration

The `slate_adaptiveInstructions` tool in the @slate VS Code extension queries the
instruction controller for live instruction state:

| Action | Description |
|--------|-------------|
| `status` | Get current instruction state from K8s ConfigMap |
| `evaluate` | Analyze system and generate instruction context |
| `sync` | Full sync: evaluate + apply + report |
| `get-context` | Get markdown instruction block for sessions |
| `get-active` | Get active instruction set (K8s → local fallback) |
| `apply` | Push evaluated instructions to K8s ConfigMap |

### K8s Resources

| Resource | Type | Purpose |
|----------|------|---------|
| `slate-instructions` | ConfigMap | Stores all instructions, prompts, active state |
| `slate-instruction-controller` | Deployment | HTTP API for instruction queries (port 8085) |
| `slate-instruction-controller-svc` | Service | ClusterIP service for internal access |
| `slate-instruction-sync` | CronJob | Every 5min: evaluate → patch ConfigMap |

### GitHub Workflow

`instructions.yml` triggers instruction sync on:
- Push to `main` (changes to `slate/`, `k8s/`, `.github/copilot-instructions.md`, `AGENTS.md`)
- Manual dispatch with mode selection (sync/evaluate-only/apply-only/validate)
- Nightly at 03:00 UTC

### Session Protocol (AUGMENTED)

Every Copilot session MUST now include adaptive instruction check alongside static protocols:

```bash
python slate/slate_status.py --quick                    # 1. System health
python slate/adaptive_instructions.py --get-active      # 2. Get K8s-driven instruction state
python slate/slate_runtime.py --check-all               # 3. Verify integrations
python slate/slate_workflow_manager.py --status          # 4. Check task queue
```

Step 2 is NEW — it queries the K8s ConfigMap for the current instruction mode,
agent availability, active directives, and tool routing. If K8s is unavailable,
it falls back to the local state file.

### Instruction Flow

```
1. System event (push, timer, dispatch)
     ↓
2. Instruction Controller evaluates:
   - K8s cluster health (pods, deployments)
   - GPU availability (nvidia-smi)
   - Service health (Ollama, Dashboard, Runner)
   - Workflow state (pending/stale tasks)
     ↓
3. Controller generates instruction context:
   - Operating mode (NORMAL/DEGRADED/etc.)
   - Agent availability (full/gpu-only/etc.)
   - Active protocols, tools, directives
     ↓
4. Context applied to K8s ConfigMap:
   - active-state.yaml (machine-readable)
   - instruction-block.md (human-readable)
   - copilot-rules.yaml (session rules)
     ↓
5. Consumers read live instructions:
   - @slate extension (via slate_adaptiveInstructions tool)
   - K8s pods (via ConfigMap volume mount, ~90s propagation)
   - Copilot sessions (via get-context at session start)
   - GitHub workflows (via slate_workflow triggers)
```

## @slate Extension v5.1.0 — Container-First Architecture (ENFORCED)
# Modified: 2026-02-08T12:00:00Z | Author: COPILOT | Change: Add v5.1.0 container-first extension architecture, Copilot SDK integration

The `@slate` VS Code chat participant extension (v5.1.0) runs **exclusively** on K8s or Docker
backends. All local Python execution fallback has been removed. This is the STANDARD architecture.

### Execution Backends

| Backend | Priority | Method | Endpoint |
|---------|----------|--------|----------|
| **Kubernetes** | Primary | HTTP POST to copilot-bridge-svc | `http://127.0.0.1:8083/api/exec` |
| **Docker** | Secondary | `docker exec slate python ...` | Container: `slate` |
| **None** | Offline | Shows deploy prompt | N/A |

There is NO local fallback. If neither K8s nor Docker is available, the extension prompts
the user to deploy with "K8s Deploy" or "Docker Up" task buttons.

### Extension Source Layout (15 files)

```
plugins/slate-copilot/src/
  extension.ts              # Entry point — activates runtime backend + adapter
  slateRuntimeBackend.ts    # K8s/Docker command execution engine (no local)
  slateRuntimeAdapter.ts    # Service URLs, K8s port-forwarding, health monitoring
  slateRunner.ts            # Thin wrapper — routes to runtime backend (33 lines)
  slateParticipant.ts       # @slate chat participant (SYSTEM_PROMPT, commands)
  tools.ts                  # 30+ LanguageModelTool implementations
  slateAgentSdkHooks.ts     # GitHub Copilot SDK Agent hooks (ActionGuard)
  slateServiceMonitor.ts    # Service monitor — delegates to adapter
  slateDiagnostics.ts       # Security scan → Problems panel
  slateTestController.ts    # SLATE tests → Test Explorer
  slateTaskProvider.ts      # Dynamic SLATE tasks → Run Task
  slateCodeLens.ts          # Inline actions on Python/YAML files
  slateGitHubIntegration.ts # CI monitor, PR manager, issue tracker
  slateSchematicBackground.ts # Evolving SLATE background
  slateUnifiedDashboardView.ts # Guided setup + dashboard webview
```

### K8s Service Ports

| Service | Port | Purpose |
|---------|------|---------|
| Dashboard | 8080 | FastAPI dashboard |
| Agent Router | 8081 | Task classification & dispatch |
| Autonomous Loop | 8082 | Autonomous task execution |
| **Copilot Bridge** | **8083** | **Extension ↔ K8s command execution** |
| Workflow Manager | 8084 | Task lifecycle |
| Metrics | 9090 | Prometheus metrics |
| Ollama | 11434 | LLM inference |
| ChromaDB | 8000 | Vector store |

### GitHub Copilot SDK Integration

The Copilot SDK (`@github/copilot-sdk`) is vendored at `vendor/copilot-sdk` and provides:
- **CopilotClient** — JSON-RPC connection to Copilot CLI
- **CopilotSession** — Managed conversation sessions
- **Tool definitions** — Function calling with Zod schemas

SLATE integrates via `slateAgentSdkHooks.ts`:
- **PreToolUse** — Validates tool calls through ActionGuard before execution
- **PostToolUse** — Logs and audits tool execution results
- **UserPromptSubmit** — Scans prompts for security issues (PII, blocked patterns)
- **validateBashCommand** — Quick ActionGuard check for shell commands
- **validateFilePath** — File access validation (read/write/edit)

### Runtime Backend Settings (package.json)

| Setting | Default | Options |
|---------|---------|---------|
| `slate.runtime.backend` | `auto` | `auto`, `kubernetes`, `docker` |
| `slate.runtime.k8sEndpoint` | `http://127.0.0.1:8083` | Custom K8s bridge URL |
| `slate.runtime.dockerContainer` | `slate` | Docker container name |

## Runtime Integrations Update — 11 Integrations (Corrected)
# Modified: 2026-02-09T01:48:00Z | Author: COPILOT | Change: Correct integration count from 7 to 11, document PyTorch local-vs-Docker split, add current operational state

Previous sections reference "7 integrations" for `slate_runtime.py --check-all`. The actual
count is now **11 integrations** after adding Copilot SDK, Semantic Kernel, GitHub Models, and Kubernetes:

| # | Integration | Local Status | Notes |
|---|-------------|-------------|-------|
| 1 | Python 3.11+ | active | 3.11.9 via `.venv` |
| 2 | Virtual Env | active | `.venv\Scripts\python.exe` |
| 3 | NVIDIA GPU | inactive (local) | GPU access via Ollama/Docker/K8s, not torch.cuda locally |
| 4 | PyTorch | active (CPU) | 2.10.0+cpu locally; CUDA 12.8 in Docker image |
| 5 | Transformers | active | 5.1.0 |
| 6 | Ollama | active | 11 models, 4 loaded in VRAM |
| 7 | ChromaDB | active | 1.4.1, 10398 embeddings indexed |
| 8 | Copilot SDK | active | Protocol v2 |
| 9 | Semantic Kernel | active | 1.39.3 (Ollama connected) |
| 10 | GitHub Models | active | 11 models, local inference |
| 11 | Kubernetes | active | 9/9 deployments ready |

### PyTorch Configuration (Local vs Docker)

PyTorch is intentionally **CPU-only** in the local `.venv`. GPU-accelerated PyTorch
with CUDA 12.8 runs inside the Docker release image (`nvidia/cuda:12.8.0-runtime-ubuntu22.04`).
This is by design — local development uses Ollama for GPU inference, Docker/K8s for
containerized GPU workloads.

```
Local (.venv):    torch 2.10.0+cpu    → CPU inference, model loading, testing
Docker/K8s:       torch + cu128       → Full CUDA GPU inference, training
Ollama (local):   GPU direct          → LLM inference (slate-coder, slate-fast, slate-planner)
```

### Corrected Protocol Commands

References to "7 integrations" in this document should read "11 integrations":
```bash
python slate/slate_runtime.py --check-all     # All 11 integrations (Python, venv, GPU, PyTorch, Transformers, Ollama, ChromaDB, Copilot SDK, Semantic Kernel, GitHub Models, K8s)
```

### Current Operational State (2026-02-09)

- **GPUs**: 2x RTX 5070 Ti (Blackwell, 16GB each), GPU 0 = heavy_inference, GPU 1 = quick_tasks
- **Ollama Models**: 11 total — slate-coder (12B), slate-fast (3B), slate-planner (7B), codellama:13b, mistral-nemo, llama3.2:3b, nomic-embed-text, phi, llama3.2, llama2, mistral
- **K8s**: 9 deployments (chromadb, ollama, agent-router, autonomous-loop, copilot-bridge, core, dashboard, instruction-controller, workflow-manager)
- **CronJobs**: 5 (codebase-indexer daily 2am, inference-benchmarks weekly, model-trainer weekly, nightly-health daily midnight, workflow-cleanup every 4h)
- **Dashboard**: http://127.0.0.1:8080
- **Inference Speed**: ~100 tok/s (slate-coder), ~308 tok/s (slate-fast)
- **ChromaDB**: 10398 embeddings, last indexed 2026-02-07
