# Specification: Autonomous Task Loop

**Spec ID**: 021-autonomous-task-loop
**Status**: complete
**Created**: 2026-02-08
**Completed**: 2026-02-08
**Author**: Claude Opus 4.5
**Tech Tree ID**: autonomous-loop

## Overview

The Autonomous Task Loop is SLATE's self-managing execution system that discovers, classifies, routes, and executes tasks without human intervention. It combines five task discovery sources, ML-powered classification, intelligent agent routing, and self-healing capabilities to maintain continuous operation.

The system operates as a unified "brain" that coordinates all SLATE autonomous components:
- ML Orchestrator (GPU inference via Ollama + PyTorch)
- Unified Autonomous Loop (task discovery + execution)
- Copilot Runner (chat participant bridge)
- Multi-Runner Coordinator (parallel runner dispatch)
- Project Board (KANBAN sync)
- Workflow Manager (task lifecycle)

## Architecture

```
                                AUTONOMOUS TASK LOOP
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                                                                         │
    │  ┌─────────────────────────────────────────────────────────────────┐   │
    │  │                    5-SOURCE TASK DISCOVERY                       │   │
    │  │                                                                  │   │
    │  │   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────┐ │   │
    │  │   │ GitHub   │ │ GitHub   │ │ GitHub   │ │  KANBAN  │ │Local │ │   │
    │  │   │ Issues   │ │   PRs    │ │Discuss.  │ │  Board   │ │Queue │ │   │
    │  │   └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └──┬───┘ │   │
    │  │        │            │            │            │          │      │   │
    │  │        └────────────┴────────────┴────────────┴──────────┘      │   │
    │  │                              │                                   │   │
    │  └──────────────────────────────┼───────────────────────────────────┘   │
    │                                 ▼                                       │
    │  ┌─────────────────────────────────────────────────────────────────┐   │
    │  │                    ML CLASSIFICATION ENGINE                      │   │
    │  │                                                                  │   │
    │  │   Pattern Matching → Semantic Kernel → Ollama Inference → Default│   │
    │  │                                                                  │   │
    │  └──────────────────────────────┬───────────────────────────────────┘   │
    │                                 ▼                                       │
    │  ┌─────────────────────────────────────────────────────────────────┐   │
    │  │                      AGENT ROUTING                               │   │
    │  │                                                                  │   │
    │  │   ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────────────┐│   │
    │  │   │ ALPHA  │ │  BETA  │ │ GAMMA  │ │ DELTA  │ │    COPILOT     ││   │
    │  │   │ Code   │ │  Test  │ │Analysis│ │Integr. │ │  Multi-step    ││   │
    │  │   └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └───────┬────────┘│   │
    │  │       │          │          │          │              │         │   │
    │  │   ┌───┴──────────┴──────────┴──────────┴──────────────┘         │   │
    │  │   │                                                             │   │
    │  └───┼─────────────────────────────────────────────────────────────┘   │
    │      ▼                                                                  │
    │  ┌─────────────────────────────────────────────────────────────────┐   │
    │  │                    GPU WORKER EXECUTION                          │   │
    │  │                                                                  │   │
    │  │   ┌────────────────────┐     ┌────────────────────┐             │   │
    │  │   │     GPU 0          │     │     GPU 1          │             │   │
    │  │   │  RTX 5070 Ti       │     │  RTX 5070 Ti       │             │   │
    │  │   │  ┌──────────────┐  │     │  ┌──────────────┐  │             │   │
    │  │   │  │ slate-coder  │  │     │  │ slate-fast   │  │             │   │
    │  │   │  │ (12B)        │  │     │  │ (3B)         │  │             │   │
    │  │   │  └──────────────┘  │     │  └──────────────┘  │             │   │
    │  │   └────────────────────┘     └────────────────────┘             │   │
    │  │                                                                  │   │
    │  └──────────────────────────────┬───────────────────────────────────┘   │
    │                                 ▼                                       │
    │  ┌─────────────────────────────────────────────────────────────────┐   │
    │  │                    SELF-HEALING & ADAPTATION                     │   │
    │  │                                                                  │   │
    │  │   Health Checks → Auto-Recovery → Strategy Adaptation → Logging │   │
    │  │                                                                  │   │
    │  └─────────────────────────────────────────────────────────────────┘   │
    │                                                                         │
    └─────────────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Unified Autonomous Loop (`slate_unified_autonomous.py`)

The primary task execution engine that implements the discovery-classify-route-execute cycle.

| Method | Purpose |
|--------|---------|
| `discover_tasks()` | Aggregates tasks from all 5 sources |
| `classify_task()` | ML-powered task classification |
| `execute_task()` | Routes and executes via appropriate agent |
| `adapt()` | Adjusts strategy based on success rates |
| `run()` | Main continuous execution loop |

### 2. Integrated Autonomous Loop (`integrated_autonomous_loop.py`)

Top-level coordination layer that manages component health and system-wide orchestration.

| Method | Purpose |
|--------|---------|
| `check_health()` | Monitors all SLATE components |
| `self_heal()` | Automatic recovery from failures |
| `generate_tech_tree_tasks()` | Creates improvement tasks from codebase analysis |
| `run()` | Orchestrates the full autonomous cycle |

### 3. Copilot Slate Runner (`copilot_slate_runner.py`)

Bridges VS Code Copilot Chat to the autonomous system with bidirectional task flow.

| Method | Purpose |
|--------|---------|
| `queue_task()` | Accepts tasks from @slate chat participant |
| `start()` | Runs the Copilot-driven task runner |
| `stop()` | Graceful shutdown with PID management |

## 5-Source Task Discovery

The autonomous loop discovers tasks from five distinct sources, each providing different types of work:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         TASK DISCOVERY SOURCES                           │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. LOCAL TASK QUEUE (current_tasks.json)                               │
│     ├─ Highest priority: explicitly queued tasks                        │
│     ├─ Includes: pending and in_progress tasks                          │
│     └─ Filters: stale detection (>4h in-progress)                       │
│                                                                          │
│  2. GITHUB KANBAN BOARD (Project #5)                                    │
│     ├─ Syncs via slate_project_board.py --sync                          │
│     ├─ Deduplicates against existing task file                          │
│     └─ Returns only genuinely NEW items after sync                      │
│                                                                          │
│  3. GITHUB ISSUES (labeled: autonomous)                                 │
│     ├─ Fetches open issues with 'autonomous' label                      │
│     ├─ Extracts priority from labels (priority:high, priority:critical) │
│     ├─ Creates tasks with gh_issue_{number} IDs                         │
│     └─ Caps at 5 issues per discovery cycle                             │
│                                                                          │
│  4. CODEBASE ANALYSIS (TODOs, FIXMEs)                                   │
│     ├─ Scans slate/ and agents/ directories                             │
│     ├─ Detects: TODO:, FIXME:, HACK:, BUG: markers in comments          │
│     ├─ Excludes self (prevents false positives from pattern defs)       │
│     └─ Caps at 10 items per cycle                                       │
│                                                                          │
│  5. TEST COVERAGE GAPS                                                   │
│     ├─ Compares slate/*.py against tests/test_*.py                      │
│     ├─ Identifies modules without corresponding test files              │
│     └─ Creates low-priority "Add tests for..." tasks                    │
│                                                                          │
│  + BONUS: KUBERNETES HEALTH (when K8s available)                        │
│     ├─ Detects non-Running pods in slate namespace                      │
│     ├─ Tracks high-restart pods (>5 restarts)                           │
│     └─ Monitors failed CronJobs                                         │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Discovery Flow

```
discover_tasks()
    │
    ├─→ _discover_from_task_file()     → Source 1: Local queue
    │
    ├─→ _discover_from_kanban()        → Source 2: KANBAN board
    │        │
    │        ├─ Snapshot existing IDs
    │        ├─ Run slate_project_board.py --sync
    │        └─ Return only NEW items
    │
    ├─→ _discover_from_github_issues() → Source 3: GitHub Issues
    │        │
    │        ├─ Get token from git credential manager
    │        ├─ Fetch issues with 'autonomous' label
    │        └─ Cap at 5 issues
    │
    ├─→ _discover_from_codebase()      → Source 4: Code analysis
    │        │
    │        ├─ Scan .py files for markers
    │        ├─ Only match in comments (#)
    │        └─ Cap at 10 items
    │
    ├─→ _discover_from_coverage()      → Source 5: Test gaps
    │        │
    │        └─ Compare modules vs test files
    │
    ├─→ _discover_from_kubernetes()    → Bonus: K8s health
    │
    ├─→ Deduplicate by title similarity (first 50 chars)
    │
    └─→ Sort by priority (critical > high > medium > low)
```

## ML Classification System

Tasks are classified using a multi-stage fallback chain:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CLASSIFICATION PIPELINE                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Stage 1: PATTERN MATCHING (fastest, 90% confidence)                   │
│  ─────────────────────────────────────────────────────                 │
│  Keyword patterns map directly to agents:                              │
│                                                                         │
│  ALPHA:   implement, code, build, fix, create, add, refactor, write    │
│  BETA:    test, validate, verify, coverage, check, lint, format        │
│  GAMMA:   analyze, plan, research, document, review, design            │
│  DELTA:   claude, mcp, sdk, integration, api, plugin                   │
│  EPSILON: spec, specification, architecture, blueprint, schema, rfc    │
│  ZETA:    benchmark, performance, profile, throughput, latency         │
│  COPILOT: complex, multi-step, orchestrate, deploy, kubernetes, k8s    │
│  COPILOT_CHAT: diagnose, investigate, troubleshoot, interactive        │
│                                                                         │
│                         │                                               │
│                         ▼ (no pattern match)                           │
│                                                                         │
│  Stage 2: SEMANTIC KERNEL (85% confidence)                             │
│  ─────────────────────────────────────────                             │
│  Uses Microsoft Semantic Kernel with SlateAgentPlugin.route_task()     │
│  Provides function-calling enhanced routing                            │
│                                                                         │
│                         │                                               │
│                         ▼ (SK unavailable)                             │
│                                                                         │
│  Stage 3: OLLAMA INFERENCE (80% confidence)                            │
│  ──────────────────────────────────────────                            │
│  ML-based classification via local LLM                                 │
│  Uses ml_orchestrator.classify_task()                                  │
│                                                                         │
│                         │                                               │
│                         ▼ (Ollama unavailable)                         │
│                                                                         │
│  Stage 4: DEFAULT (50% confidence)                                     │
│  ─────────────────────────────────                                     │
│  Falls back to ALPHA (coding agent)                                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Classification Result

```python
{
    "agent": "ALPHA",           # Target agent
    "method": "pattern",        # How it was classified
    "confidence": 0.9,          # Confidence score (0.0-1.0)
    "classification": "...",    # ML classification text (if ML used)
    "sk_response": "..."        # SK response (if SK used)
}
```

## Agent Routing

The system routes tasks to specialized agents based on classification:

| Agent | Specialization | Execution Method |
|-------|---------------|------------------|
| **ALPHA** | Code implementation | `_execute_code_task()` with full inference |
| **BETA** | Testing and validation | `_execute_code_task()` with review focus |
| **GAMMA** | Analysis and planning | `_execute_analysis_task()` |
| **DELTA** | Integration tasks | `_execute_integration_task()` |
| **EPSILON** | Specification work | Architecture and design tasks |
| **ZETA** | Performance | Benchmarking and optimization |
| **COPILOT** | Complex multi-step | `_execute_complex_task()` with planning |
| **COPILOT_CHAT** | Interactive | `_execute_copilot_chat_task()` via bridge |

### Code Task Execution Flow

```
_execute_code_task(task, agent)
    │
    ├─→ Read relevant files for context
    │     └─ Up to 4000 chars per file
    │
    ├─→ Build inference prompt
    │     ├─ System: "You are SLATE-CODER..."
    │     └─ Task + description + code context
    │
    ├─→ Run inference with fallback chain
    │     ├─ Primary: Ollama (local, fast)
    │     └─ Fallback: GitHub Models (cloud, free)
    │
    ├─→ Extract code blocks from response
    │     └─ Regex: ```python ... ```
    │
    ├─→ Validate and apply changes (ALPHA only)
    │     ├─ Syntax check (compile)
    │     ├─ Security check (blocked patterns)
    │     ├─ Create backup
    │     └─ Write updated file
    │
    └─→ Log response to slate_logs/autonomous/
```

### Inference Fallback Chain

```python
def _infer_with_fallback(prompt, task_type, system, max_tokens, temperature):
    """
    Returns: {response, model, tokens, tok_per_sec, source}
    """

    # 1. Try Ollama (fastest, local, no rate limits)
    if ollama.is_running():
        result = ml.infer(prompt, task_type=task_type, ...)
        if result.get("response"):
            return {**result, "source": "ollama"}

    # 2. Fallback to GitHub Models (free cloud)
    if github_models_available:
        role_map = {
            "code_generation": "code",
            "code_review": "code",
            "planning": "planner",
            "analysis": "analysis",
        }
        resp = gh.chat(prompt, role=role_map.get(task_type, "general"), ...)
        return {
            "response": resp.content,
            "model": resp.model,
            "source": "github_models",
        }

    # 3. Return error if all backends unavailable
    return {"response": "", "source": "none", "error": "..."}
```

## Self-Healing Capabilities

The integrated loop includes automatic recovery mechanisms:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       SELF-HEALING SYSTEM                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  HEALTH CHECKS                                                          │
│  ─────────────                                                          │
│  Component         Check Method                      Healthy Criteria   │
│  ─────────────────────────────────────────────────────────────────────  │
│  Ollama           HTTP GET /api/tags                 Response + models  │
│  GPU              nvidia-smi query                   returncode == 0    │
│  Orchestrator     Run status command                 returncode == 0    │
│  ML Orchestrator  Run --status                       returncode == 0    │
│  Multi-runner     File exists check                  File present       │
│  Workflow Mgr     Run --status                       returncode == 0    │
│  Project Board    Run --status                       returncode == 0    │
│  Kubernetes       kubectl get deployments            All ready          │
│                                                                         │
│  AUTOMATIC RECOVERY                                                     │
│  ──────────────────                                                     │
│  Condition                  Action                                      │
│  ─────────────────────────────────────────────────────────────────────  │
│  Ollama not running         Popen("ollama serve") + wait 3s             │
│  Orchestrator unhealthy     Run orchestrator start                      │
│  Stale task (>4h)           Reset to pending status                     │
│  High failure rate (<50%)   Prioritize simpler tasks                    │
│  Agent failures (>70%)      Re-route to fallback agent                  │
│                                                                         │
│  ADAPTATION TRIGGERS                                                    │
│  ───────────────────                                                    │
│  - Every 5 tasks: analyze success rates                                 │
│  - Low success (<50%): reduce_complexity adaptation                     │
│  - Agent-specific failures: agent_issue adaptation                      │
│  - Adaptations stored in state (last 50)                                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Health Check Flow

```
check_health()
    │
    ├─→ _check_ollama()           → HTTP /api/tags
    ├─→ _check_gpu()              → nvidia-smi query
    ├─→ _check_component(orchestrator, ["status"])
    ├─→ _check_component(ml_orchestrator, ["--status"])
    ├─→ _check_file_exists(multi_runner)
    ├─→ _check_component(workflow_manager, ["--status"])
    ├─→ _check_component(project_board, ["--status"])
    ├─→ _check_kubernetes()       → kubectl get deployments
    │
    ├─→ Count healthy components
    ├─→ Record in health_history
    └─→ Return health dict
```

### Self-Heal Flow

```
self_heal(health)
    │
    ├─→ IF ollama unhealthy:
    │     └─ Popen(["ollama", "serve"])
    │        └─ Wait 3 seconds
    │
    ├─→ IF orchestrator unhealthy:
    │     └─ Run orchestrator start command
    │
    └─→ Increment self_heals counter
```

## Error Recovery

The system implements multiple layers of error handling:

### Task-Level Recovery

```python
try:
    result = execute_task(task)
    if result.get("success"):
        update_task_status(task_id, "completed")
        state["tasks_completed"] += 1
    else:
        update_task_status(task_id, "failed", error=result.get("error"))
        state["tasks_failed"] += 1
except Exception as e:
    update_task_status(task_id, "failed", error=str(e))
    state["tasks_failed"] += 1
    log(f"Exception: {e}", "ERROR")
```

### Code Change Safety

Before applying generated code:

1. **Syntax validation**: `compile(code, filename, "exec")`
2. **Security scan**: Check for blocked patterns (`eval(`, `exec(os`, `rm -rf /`, etc.)
3. **Backup creation**: Save original to `slate_logs/backups/{stem}_{timestamp}.py.bak`
4. **Write with validation**: Only write if all checks pass

### Stale Task Detection

```python
def _is_stale(task: dict) -> bool:
    """Task is stale if in-progress for more than 4 hours."""
    started = task.get("started_at")
    if not started or task.get("status") != "in_progress":
        return False
    start_dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
    elapsed = (datetime.now(timezone.utc) - start_dt).total_seconds()
    return elapsed > 4 * 3600  # 4 hours
```

## Workflow Integration

The autonomous loop integrates with the broader SLATE workflow system:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    WORKFLOW INTEGRATION                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  INPUT SOURCES                                                          │
│  ─────────────                                                          │
│  GitHub Actions (agentic.yml)                                          │
│       └─→ Triggers integrated_autonomous_loop.py --run                  │
│                                                                         │
│  Copilot Chat (@slate participant)                                     │
│       └─→ Routes via copilot_slate_runner.py                           │
│              └─→ Bridge queue for bidirectional flow                   │
│                                                                         │
│  Manual CLI                                                             │
│       └─→ python slate_unified_autonomous.py --run --max 50            │
│                                                                         │
│  OUTPUT SINKS                                                           │
│  ────────────                                                           │
│  current_tasks.json                                                     │
│       └─→ Task status updates (pending → in_progress → completed)      │
│                                                                         │
│  KANBAN Board (Project #5)                                             │
│       └─→ Synced via _sync_to_kanban()                                 │
│              └─→ slate_project_board.py --push                         │
│                                                                         │
│  Logs (slate_logs/autonomous/)                                         │
│       └─→ Task execution logs                                          │
│       └─→ Response audit files                                         │
│       └─→ Backup files before code changes                             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## State Management

### Unified Autonomous State (`.slate_autonomous_state.json`)

```json
{
  "started_at": "2026-02-08T10:00:00Z",
  "tasks_discovered": 142,
  "tasks_completed": 98,
  "tasks_failed": 12,
  "cycles": 45,
  "last_cycle": "2026-02-08T14:30:00Z",
  "adaptations": [
    {
      "type": "reduce_complexity",
      "reason": "Low success rate: 45%",
      "action": "Prioritize simpler tasks",
      "time": "2026-02-08T12:00:00Z"
    }
  ],
  "history": [
    {
      "task_id": "gh_issue_123",
      "title": "Fix dashboard WebSocket",
      "agent": "ALPHA",
      "success": true,
      "time": "2026-02-08T14:25:00Z",
      "duration_s": 45.2
    }
  ]
}
```

### Integrated State (`.slate_integrated_state.json`)

```json
{
  "started_at": "2026-02-08T10:00:00Z",
  "cycles": 45,
  "last_cycle": "2026-02-08T14:30:00Z",
  "components_healthy": 7,
  "components_total": 8,
  "tasks_completed": 98,
  "tasks_failed": 12,
  "self_heals": 3,
  "adaptations": [],
  "health_history": [
    {"time": "2026-02-08T14:30:00Z", "healthy": 7, "total": 8}
  ]
}
```

## CLI Reference

### slate_unified_autonomous.py

```powershell
# Run autonomous loop with max 50 tasks
python slate/slate_unified_autonomous.py --run --max 50

# Run until no tasks remain
python slate/slate_unified_autonomous.py --run --stop-on-empty

# Show current status
python slate/slate_unified_autonomous.py --status

# Discover tasks only (no execution)
python slate/slate_unified_autonomous.py --discover

# Execute single task
python slate/slate_unified_autonomous.py --single

# JSON output for automation
python slate/slate_unified_autonomous.py --json
```

### integrated_autonomous_loop.py

```powershell
# Run integrated loop with coordination
python slate/integrated_autonomous_loop.py --run --max 100

# Show system status with component health
python slate/integrated_autonomous_loop.py --status

# Generate tech tree improvement tasks
python slate/integrated_autonomous_loop.py --generate

# Run warmup only (preload models)
python slate/integrated_autonomous_loop.py --warmup

# JSON output
python slate/integrated_autonomous_loop.py --json
```

### copilot_slate_runner.py

```powershell
# Start Copilot runner
python slate/copilot_slate_runner.py --start --max-tasks 50

# Stop runner
python slate/copilot_slate_runner.py --stop

# Show runner status
python slate/copilot_slate_runner.py --status

# Check bridge status
python slate/copilot_slate_runner.py --bridge-status

# Queue task from CLI
python slate/copilot_slate_runner.py --queue "fix the dashboard layout"
```

## Execution Cycle

The complete autonomous cycle follows this pattern:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       INTEGRATED CYCLE                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Phase 0: WARMUP                                                        │
│  ───────────────                                                        │
│  - Configure Ollama environment                                         │
│  - Preload models to GPUs                                              │
│  - Build embedding index (if not skipped)                              │
│                                                                         │
│                         │                                               │
│                         ▼                                               │
│                                                                         │
│  Phase 1: HEALTH CHECK                                                  │
│  ─────────────────────                                                  │
│  - Check all 8 components                                              │
│  - Record health history                                               │
│                                                                         │
│                         │                                               │
│                         ▼                                               │
│                                                                         │
│  Phase 2: SELF-HEAL                                                     │
│  ─────────────────                                                      │
│  - IF components unhealthy → attempt recovery                          │
│  - Start Ollama if not running                                         │
│  - Restart orchestrator if needed                                      │
│                                                                         │
│                         │                                               │
│                         ▼                                               │
│                                                                         │
│  Phase 3: OLLAMA CHECK                                                  │
│  ────────────────────                                                   │
│  - IF Ollama unavailable → wait and retry                              │
│  - Required for ML inference                                           │
│                                                                         │
│                         │                                               │
│                         ▼                                               │
│                                                                         │
│  Phase 4: TASK GENERATION                                               │
│  ────────────────────────                                               │
│  - IF pending < 3 → generate tech tree tasks                           │
│  - Inject up to 5 new tasks                                            │
│                                                                         │
│                         │                                               │
│                         ▼                                               │
│                                                                         │
│  Phase 5: TASK EXECUTION (batch of 5)                                   │
│  ────────────────────────────────────                                   │
│  - Discover tasks from all sources                                     │
│  - Sort by priority                                                    │
│  - Route GPU-intensive via scheduler                                   │
│  - Execute via appropriate agent                                       │
│                                                                         │
│                         │                                               │
│                         ▼                                               │
│                                                                         │
│  Phase 6: ADAPTATION                                                    │
│  ──────────────────                                                     │
│  - Analyze recent success rates                                        │
│  - Adjust strategy if needed                                           │
│  - Every 20 cycles: re-warmup models                                   │
│  - Every 50 cycles: refresh embedding index                            │
│                                                                         │
│                         │                                               │
│                         ▼                                               │
│                                                                         │
│  Phase 7: SYNC                                                          │
│  ───────────                                                            │
│  - Push completed tasks to KANBAN                                      │
│  - Update current_tasks.json                                           │
│                                                                         │
│                         │                                               │
│                         ▼                                               │
│                                                                         │
│  LOOP → (back to Phase 1)                                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Implementation Files

| File | Purpose |
|------|---------|
| `slate/slate_unified_autonomous.py` | Core autonomous task loop |
| `slate/integrated_autonomous_loop.py` | Top-level coordination with self-healing |
| `slate/copilot_slate_runner.py` | VS Code Copilot Chat bridge |
| `slate/copilot_agent_bridge.py` | Bidirectional task queue for @slate participant |
| `slate/ml_orchestrator.py` | ML inference orchestration |
| `slate/slate_ai_scheduler.py` | GPU-aware task scheduling |
| `slate/slate_warmup.py` | Model preloading and keep-alive |
| `slate/slate_project_board.py` | KANBAN board sync |
| `slate/slate_workflow_manager.py` | Task lifecycle management |

## Related Specifications

- **007-slate-design-system**: Dashboard UI for monitoring autonomous operations
- **012-watchmaker-3d-dashboard**: Visualization of task flow and agent activity
- **vendor-integration**: SDK integration for Semantic Kernel and other backends

## Workflow Files

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `agentic.yml` | Scheduled/manual | Runs integrated autonomous loop |
| `ai-maintenance.yml` | Every 4h | Codebase analysis and doc updates |
| `service-management.yml` | Manual | Manages SLATE services |
