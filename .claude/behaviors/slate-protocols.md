# SLATE Operational Protocols
<!-- Modified: 2026-02-10T04:00:00Z | Author: Claude Opus 4.5 | Change: Define SLATE operational protocols for Claude Code -->

## Protocol Registry

These protocols define how Claude Code operates within the SLATE ecosystem.

---

## P001: System Initialization

**Trigger**: Session start, `/slate status`, system check request

```yaml
protocol: P001-INIT
steps:
  1. Check runtime: slate_status --quick
  2. Verify K8s/Docker: slate_runtime --check-all
  3. Load instructions: slate_adaptiveInstructions status
  4. Report state: {backend, healthy, services, gpu_count}
```

**Example**:
```
User: "check slate"
→ slate_status tool
→ Report: "SLATE K8s runtime healthy. 11 pods running. 2x RTX 5070 Ti detected."
```

---

## P002: Task Execution

**Trigger**: User requests a SLATE operation

```yaml
protocol: P002-EXECUTE
pattern: DIAGNOSE → ACT → VERIFY
steps:
  1. DIAGNOSE: Understand current state
  2. ACT: Execute operation via MCP tool or approved Bash
  3. VERIFY: Confirm success, report result
recovery:
  - On failure: Check runtime health
  - On timeout: Retry once, then report
  - On block: Report ActionGuard reason
```

**Example**:
```
User: "deploy to kubernetes"
→ DIAGNOSE: slate_status (check if k8s available)
→ ACT: slate_kubernetes deploy
→ VERIFY: kubectl get pods -n slate
→ Report: "Deployed 11 pods to K8s. Dashboard at localhost:8080"
```

---

## P003: Workflow Management

**Trigger**: Task queue operations, `/slate-workflow`

```yaml
protocol: P003-WORKFLOW
tools:
  - slate_workflow (MCP)
  - slate/slate_workflow_manager.py
actions:
  status: Show queue state, stale tasks, abandoned
  cleanup: Remove stale tasks (>4h in-progress)
  enforce: Check max concurrent, block if exceeded
```

**Rules**:
- Max 5 concurrent tasks
- Stale threshold: 4 hours
- Abandoned threshold: 24 hours
- Auto-archive duplicates

---

## P004: GPU Operations

**Trigger**: GPU status, model loading, `/slate-gpu`

```yaml
protocol: P004-GPU
tools:
  - slate_gpu (MCP)
  - slate_hardware (MCP)
  - slate/slate_hardware_optimizer.py
detection:
  - nvidia-smi for GPU info
  - PyTorch for CUDA availability
  - Ollama for model placement
```

**Dual-GPU Load Balancing**:
```
GPU 0: Primary inference (mistral-nemo)
GPU 1: Secondary inference (llama3.2)
Strategy: Round-robin with affinity
```

---

## P005: Security Validation

**Trigger**: Before any Bash command execution

```yaml
protocol: P005-SECURITY
validator: ActionGuard (slate/action_guard.py)
checks:
  - Dangerous pattern detection
  - External API blocking
  - PII scanning
  - SDK source validation
response:
  ALLOWED: Proceed with execution
  BLOCKED: Report reason, suggest alternative
  ASK: Request user confirmation (rare)
```

**Blocked Patterns**:
```python
BLOCKED = [
    r'rm\s+-rf\s+/',
    r'0\.0\.0\.0',  # except cidr: patterns
    r'eval\s*\(',
    r'exec\s*\(.*input',
    r'api\.openai\.com',
    r'api\.anthropic\.com',
]
```

---

## P006: Error Recovery

**Trigger**: Command failure, timeout, unexpected state

```yaml
protocol: P006-RECOVERY
steps:
  1. Identify error type (runtime, network, permission, logic)
  2. Check system health: slate_status
  3. Attempt automatic recovery:
     - Runtime down → Re-detect, reconnect
     - K8s unreachable → Fallback to Docker
     - Service unhealthy → Report, suggest restart
  4. Report with context and suggestion
```

**Recovery Actions**:
| Error Type | Action |
|------------|--------|
| K8s unreachable | Try Docker fallback |
| Service timeout | Retry once, then report |
| Permission denied | Check ActionGuard, report reason |
| Missing dependency | Suggest install command |

---

## P007: Code Operations

**Trigger**: File read/write/edit requests

```yaml
protocol: P007-CODE
tools:
  - Read, Write, Edit (native)
  - Glob, Grep (search)
validation:
  - Path within workspace
  - Not in excluded dirs (.git, node_modules, .venv)
  - Not credential files (.env, credentials.json)
patterns:
  - Prefer Edit over Write for existing files
  - Always Read before Write (verify current state)
  - Use Glob to find files, not Bash find
```

---

## P008: Git Operations

**Trigger**: Version control requests

```yaml
protocol: P008-GIT
allowed:
  - git status, git diff, git log
  - git add <specific files>
  - git commit -m "message"
  - git push (with confirmation)
blocked:
  - git push --force
  - git reset --hard
  - git clean -f
commit_format: |
  <type>: <description>

  Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

---

## P009: K8s Deployment

**Trigger**: `/slate-kubernetes:k8s`, K8s operations

```yaml
protocol: P009-K8S
tools:
  - slate_kubernetes (MCP)
  - kubectl (via Bash, validated)
deploy_methods:
  - Kustomize (default): kubectl apply -k k8s/
  - Helm: helm install slate ./helm
port_forwards:
  - Dashboard: 8080
  - Ollama: 11434
  - ChromaDB: 8000
  - Bridge: 8083
```

---

## P010: Autonomous Loop

**Trigger**: Background task processing

```yaml
protocol: P010-AUTONOMOUS
source: slate-copilot-bridge task queue
pattern:
  1. Poll: slate_agentBridge action=poll
  2. Process: Execute task via tools
  3. Complete: slate_agentBridge action=complete
constraints:
  - Max 10 tasks per session
  - 10 minute timeout per task
  - Report failures, don't retry indefinitely
```

---

## Protocol Chaining

Protocols can chain for complex operations:

```
User: "Deploy SLATE and run tests"
→ P001-INIT (check current state)
→ P009-K8S (deploy to kubernetes)
→ P002-EXECUTE (run pytest)
→ Report combined result
```

## Protocol Override

User can override protocols with explicit instructions:

```
User: "Force push to main"
→ P008-GIT blocks by default
→ User confirms explicitly
→ Execute with warning logged
```

## Metrics

Track protocol execution for optimization:

```json
{
  "protocol": "P002-EXECUTE",
  "success": true,
  "duration_ms": 1250,
  "tools_used": ["slate_status", "slate_kubernetes"],
  "recovery_needed": false
}
```
