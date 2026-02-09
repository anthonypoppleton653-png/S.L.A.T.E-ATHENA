---
name: slate-orchestrator
description: Start, stop, or check the SLATE orchestrator. Use when managing SLATE services, starting/stopping the dashboard, or checking service status.
---

# /slate

Start, stop, or check the SLATE orchestrator and all services.

## Usage
/slate [start | stop | status | restart]

## Description
<!-- Modified: 2026-02-09T04:30:00Z | Author: COPILOT | Change: Add K8s deployment management to orchestrator skill -->
The SLATE orchestrator manages all SLATE services:
- Dashboard server (port 8080)
- Workflow monitor
- GitHub Actions runner integration
- Background task processing
- Kubernetes deployments (`kubectl apply -k k8s/overlays/local/`)
- Docker container lifecycle (`docker-compose up/down`)

## Instructions

When the user invokes this skill:

**Start SLATE:**
```powershell
.\.venv_slate_ag\Scripts\python.exe -m slate/slate_orchestrator.py start
```

**Stop SLATE:**
```powershell
.\.venv_slate_ag\Scripts\python.exe -m slate/slate_orchestrator.py stop
```

**Check status:**
```powershell
.\.venv_slate_ag\Scripts\python.exe -m slate/slate_orchestrator.py status
```

**Restart (stop then start):**
```powershell
.\.venv_slate_ag\Scripts\python.exe -m slate/slate_orchestrator.py stop
.\.venv_slate_ag\Scripts\python.exe -m slate/slate_orchestrator.py start
```

Report the results showing:
1. Which services started/stopped
2. Dashboard URL (http://localhost:8080)
3. Any errors encountered
4. PID file location

## Examples

User: "/slate start"
→ Start all SLATE services

User: "/slate stop"
→ Stop all running services

User: "/slate"
→ Show current orchestrator status

User: "Start SLATE"
→ Invoke /slate start
