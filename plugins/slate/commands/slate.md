---
description: Main SLATE command — system operator with ActionGuard security
---

# /slate

S.L.A.T.E. — Synchronized Living Architecture for Transformation and Evolution

## Usage

```
/slate [action] [options]
```

## Actions

| Action | Description |
|--------|-------------|
| `status` | System health check (default) |
| `start` | Start orchestrator |
| `stop` | Stop orchestrator |
| `workflow` | Task queue management |
| `runner` | GitHub Actions runner |
| `gpu` | GPU status and management |
| `k8s` | Kubernetes deployment |
| `help` | Show all commands |

## Behavior Profile

This plugin runs with **SLATE Operator Behavior**:
- Permission bypass enabled (ActionGuard validates instead)
- Container-first execution (K8s > Docker)
- 10 operational protocols (P001-P010)

## Instructions

Parse the user's request and execute the appropriate protocol:

**P001-INIT (status):**
```bash
.venv/Scripts/python.exe slate/slate_status.py --quick
```

**Orchestrator (start/stop):**
```bash
.venv/Scripts/python.exe slate/slate_orchestrator.py start
.venv/Scripts/python.exe slate/slate_orchestrator.py stop
```

**Workflow:**
```bash
.venv/Scripts/python.exe slate/slate_workflow_manager.py --status
```

**Runner:**
```bash
.venv/Scripts/python.exe slate/slate_runner_manager.py --status
```

**GPU:**
```bash
.venv/Scripts/python.exe slate/slate_gpu_manager.py --status
```

**K8s:**
```bash
.venv/Scripts/python.exe slate/slate_k8s.py --status
```

## Security

All commands are validated by ActionGuard before execution.
Blocked patterns: `rm -rf /`, `0.0.0.0`, `eval()`, external APIs.

## Examples

```
/slate                    # Quick status
/slate status             # Full status check
/slate start              # Start services
/slate workflow cleanup   # Clean stale tasks
/slate k8s deploy         # Deploy to Kubernetes
```
