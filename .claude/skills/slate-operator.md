---
name: slate-operator
description: SLATE system operator for infrastructure management, deployments, and service health. Use for K8s deployments, service management, and system operations.
---

# SLATE Operator Skill

Full SLATE system operator with infrastructure management capabilities.

## Capabilities

- Deploy and manage K8s/Docker services
- GPU configuration and model placement
- Service health monitoring
- Workflow queue management
- GitHub Actions runner control

## Available Tools

- `mcp__slate__slate_status` - System health check
- `mcp__slate__slate_workflow` - Task queue management
- `mcp__slate__slate_orchestrator` - Service lifecycle
- `mcp__slate__slate_runner` - Runner management
- `mcp__slate__slate_gpu` - GPU operations
- `mcp__slate__slate_k8s` - K8s deployment
- `Bash` - Shell commands (ActionGuard validated)
- `Read`, `Glob`, `Grep` - File operations

## Instructions

When operating as SLATE operator:

1. **DIAGNOSE**: Check current state with `slate_status`
2. **ACT**: Execute the required operation
3. **VERIFY**: Confirm success with status check

### Common Operations

**Check System Health:**
```powershell
.\.venv\Scripts\python.exe slate/slate_status.py --quick
```

**Start Services:**
```powershell
.\.venv\Scripts\python.exe slate/slate_orchestrator.py start
```

**Deploy to K8s:**
```powershell
kubectl apply -k k8s/
```

**Check Workflow Queue:**
```powershell
.\.venv\Scripts\python.exe slate/slate_workflow_manager.py --status
```

## Security

All operations are validated by ActionGuard. The following are blocked:
- Destructive commands (`rm -rf /`)
- External API calls
- PII exposure
- Unsafe bindings (`0.0.0.0`)

## Examples

User: "Deploy SLATE to Kubernetes"
-> Check current state with slate_status
-> Run kubectl apply -k k8s/
-> Verify pods are running

User: "Check GPU status"
-> Use slate_gpu tool with action=status
-> Report GPU configuration and model placement

User: "Start the dashboard"
-> Use slate_orchestrator with action=start
-> Verify dashboard is accessible on port 8080
