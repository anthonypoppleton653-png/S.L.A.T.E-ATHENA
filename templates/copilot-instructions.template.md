# S.L.A.T.E. Copilot Instructions (User Template)
# Modified: 2026-02-09T23:00:00Z | Author: COPILOT | Change: Create sanitized user template for public distribution
#
# This file is auto-generated during installation by install_slate.py.
# It is placed at .github/copilot-instructions.md in the user's workspace.
# Personal configuration (fork name, GPU config) is populated by the installer.

## Workspace

**This workspace is a S.L.A.T.E. installation.**
All paths are relative to the workspace root.

- **Repo**: `SynchronizedLivingArchitecture/S.L.A.T.E`
- **Purpose**: Full SLATE SDK, inference pipeline, GPU benchmarking, CI/CD
- **Fork Name**: `{{FORK_NAME}}`

## Session Start Protocol
Before ANY code changes, execute:
```bash
python slate/slate_status.py --quick
python slate/slate_runtime.py --check-all
python slate/slate_workflow_manager.py --status
```

## Code Edit Rules
Every code edit MUST include a timestamp + author comment:
```python
# Modified: YYYY-MM-DDTHH:MM:SSZ | Author: {{AUTHOR_NAME}} | Change: description
```

## System Overview
SLATE (Synchronized Living Architecture for Transformation and Evolution) is a local-first
AI agent orchestration framework. All operations are LOCAL ONLY (127.0.0.1).

Python: 3.11+ via `.venv`
Runner: Self-hosted GitHub Actions runner (optional)

## SLATE Protocol Commands

### System Health
```bash
python slate/slate_status.py --quick
python slate/slate_status.py --json
```

### Runtime Integration Check
```bash
python slate/slate_runtime.py --check-all
```

### Hardware & GPU Optimization
```bash
python slate/slate_hardware_optimizer.py
python slate/slate_hardware_optimizer.py --optimize
```

### Task & Workflow Management
```bash
python slate/slate_workflow_manager.py --status
python slate/slate_workflow_manager.py --cleanup
python slate/slate_workflow_manager.py --enforce
```

### Service Orchestration
```bash
python slate/slate_orchestrator.py status
python slate/slate_orchestrator.py start
python slate/slate_orchestrator.py stop
```

### ML / Agentic AI
```bash
python slate/ml_orchestrator.py --status
python slate/ml_orchestrator.py --benchmarks
python slate/slate_chromadb.py --status
python slate/slate_chromadb.py --search "query"
```

### Kubernetes Deployment
```bash
python slate/slate_k8s_deploy.py --status
python slate/slate_k8s_deploy.py --deploy
python slate/slate_k8s_deploy.py --health
```

### Update System
```bash
python slate/slate_updater.py --check
python slate/slate_updater.py --update
python slate/slate_updater.py --update --channel stable
```

## Security Rules
- ALL network bindings: `127.0.0.1` ONLY — never `0.0.0.0`
- No external telemetry (ChromaDB telemetry disabled)
- Blocked patterns: `eval(`, `exec(os`, `rm -rf /`, `base64.b64decode`

## Agent Routing
| Pattern | Agent | Role |
|---------|-------|------|
| implement, code, build, fix | ALPHA | Coding |
| test, validate, verify | BETA | Testing |
| analyze, plan, research | GAMMA | Planning |
| claude, mcp, sdk | DELTA | External Bridge |
| complex, multi-step | COPILOT | Full Orchestration |

## Docker Deployment
```bash
docker compose up -d                    # GPU mode (requires NVIDIA Container Toolkit)
docker compose --profile cpu up -d      # CPU mode
docker compose build                    # Rebuild image
```

## Project Structure
```
slate/              # Core SDK modules
agents/             # API servers & agent modules
models/             # Ollama Modelfiles for custom models
plugins/            # VS Code extensions
skills/             # Copilot Chat skill definitions
k8s/                # Kubernetes manifests
helm/               # Helm chart
docker-compose.yml  # Docker orchestration
```
