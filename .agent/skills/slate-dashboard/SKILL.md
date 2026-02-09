---
name: slate-dashboard
description: Access and manage the SLATE Dashboard from the Antigravity runtime. Use when checking system status, viewing tasks, agents, GPU info, or interacting with the dashboard UI.
---

# /slate-dashboard

Access the SLATE Dashboard from the Antigravity agent runtime via the K8s antigravity-bridge or direct Docker connection.

## Usage
/slate-dashboard [endpoint] [--open | --report | --json]

## Description
<!-- Modified: 2026-02-09T04:01:00-05:00 | Author: ANTIGRAVITY (Gemini) | Change: Create dashboard skill for Antigravity runtime -->

This skill gives the Antigravity runtime direct access to the same SLATE Dashboard that the @slate VS Code extension serves in its sidebar. The dashboard is served from the Docker/K8s infrastructure via the antigravity-bridge service.

**Architecture:**
- K8s: `antigravity-bridge-svc:8085` (NodePort `30085`) → `slate-dashboard-svc:8080`
- Docker: Direct connection to `127.0.0.1:8080`
- Auto-detection: Tries K8s bridge first, falls back to direct

**Available endpoints:**
| Endpoint | Description |
|----------|-------------|
| `status` | Full system status (Python, GPU, Ollama, K8s, Antigravity) |
| `health` | Dashboard health check |
| `tasks` | Current task queue |
| `agents` | All registered agents (8 total) |
| `runner` | GitHub Actions runner status |
| `gpu` | GPU hardware info |
| `services` | SLATE service health |
| `orchestrator` | Orchestrator status |
| `github` | GitHub integration status |
| `workflows` | GitHub Actions workflows |
| `forks` | Contributor fork status |
| `k8s` | Kubernetes cluster status |
| `docker` | Docker environment status |
| `activity` | Recent activity feed |
| `specs` | Specification documents |
| `tech` | Tech tree / roadmap |
| `multirunner` | Multi-runner GPU allocation |
| `schematic` | System architecture schematic |
| `report` | Comprehensive system report |

## Instructions

When the user invokes this skill or asks about the dashboard, system status, tasks, agents, or any dashboard-related information:

### 1. Query a specific endpoint
```powershell
// turbo
.\.venv\Scripts\python.exe plugins\slate-antigravity\index.py --dashboard <endpoint>
```

Where `<endpoint>` is one of: `status`, `health`, `tasks`, `agents`, `runner`, `gpu`, `services`, `orchestrator`, `github`, `workflows`, `forks`, `k8s`, `docker`, `activity`, `specs`, `tech`, `multirunner`, `schematic`, `report`

### 2. Get a full system report
```powershell
// turbo
.\.venv\Scripts\python.exe plugins\slate-antigravity\dashboard_client.py report
```

### 3. Open the dashboard in a browser
```powershell
// turbo
Start-Process "http://127.0.0.1:30085"
```
Falls back to `http://127.0.0.1:8080` if K8s bridge isn't available.

### 4. Check dashboard connectivity
```powershell
// turbo
.\.venv\Scripts\python.exe plugins\slate-antigravity\index.py --health
```

## Auto-detection

The dashboard client automatically detects the best available endpoint:
1. **K8s Antigravity Bridge** at `localhost:30085` (NodePort) — preferred
2. **Environment variable** `ANTIGRAVITY_BRIDGE_URL` — custom override
3. **Direct dashboard** at `localhost:8080` — fallback

## K8s Resources

The Antigravity bridge is deployed via `k8s/antigravity-bridge.yaml`:
- **ConfigMap:** `antigravity-bridge-config` — bridge configuration
- **ConfigMap:** `antigravity-bridge-entrypoint` — Python bridge server
- **Deployment:** `antigravity-bridge` — 1 replica reverse proxy
- **Service:** `antigravity-bridge-svc` — NodePort 30085

## Examples

User: "/slate-dashboard"
→ Run `--dashboard status` and show system overview

User: "/slate-dashboard agents"
→ Run `--dashboard agents` and list all registered agents

User: "Show me the task queue"
→ Run `--dashboard tasks` and present the current tasks

User: "What GPUs are available?"
→ Run `--dashboard gpu` and report GPU hardware

User: "Open the dashboard"
→ Run `Start-Process "http://127.0.0.1:30085"`

User: "Give me a full system report"
→ Run `dashboard_client.py report` and present comprehensive status

User: "Is the dashboard connected?"
→ Run `--health` and report connectivity status
