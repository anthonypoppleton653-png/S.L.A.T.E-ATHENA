# S.L.A.T.E. Claude Code Instructions (User Template)
# Modified: 2026-02-09T23:00:00Z | Author: COPILOT | Change: Create sanitized CLAUDE.md template for public distribution
#
# This file is copied to CLAUDE.md in the user's workspace during installation.
# Placeholders ({{...}}) are populated by install_slate.py.

# S.L.A.T.E. — Claude Code Development Guidelines

## Quick Reference

- **System**: S.L.A.T.E. v3.0.0
- **Fork Name**: `{{FORK_NAME}}`
- **Python**: `.venv/Scripts/python.exe` (Windows) or `.venv/bin/python` (Linux/macOS)
- **Security**: LOCAL ONLY — all bindings on `127.0.0.1`

## Session Start

Before any work:
```bash
python slate/slate_status.py --quick
python slate/slate_runtime.py --check-all
python slate/slate_workflow_manager.py --status
```

## Code Edit Rules

Every code edit MUST include:
```python
# Modified: YYYY-MM-DDTHH:MM:SSZ | Author: {{AUTHOR_NAME}} | Change: description
```

## Security Rules

- ALL network bindings: `127.0.0.1` ONLY
- No `eval()`, `exec()`, `rm -rf /`, `base64.b64decode`
- No external telemetry
- No `curl.exe` on Windows (use `urllib.request` or `Invoke-RestMethod`)

## Protocol Commands

```bash
python slate/slate_status.py --quick          # Health check
python slate/slate_runtime.py --check-all     # All integrations
python slate/slate_workflow_manager.py --status   # Task queue
python slate/slate_orchestrator.py status      # Services
python slate/slate_hardware_optimizer.py       # GPU detection
python slate/slate_benchmark.py               # Benchmarks
python slate/slate_updater.py --check          # Check for updates
python slate/slate_updater.py --update         # Pull latest
```

## Agent Routing

| Pattern | Agent | Role |
|---------|-------|------|
| implement, code, build, fix | ALPHA | Coding |
| test, validate, verify | BETA | Testing |
| analyze, plan, research | GAMMA | Planning |
| claude, mcp, sdk | DELTA | Bridge |
| complex, multi-step | COPILOT | Orchestration |

## Project Structure

```
slate/              # Core SDK (30+ modules)
agents/             # API servers (dashboard, runner API)
models/             # Ollama Modelfiles (slate-coder, slate-fast, slate-planner)
plugins/            # VS Code extensions (@slate chat participant)
skills/             # Copilot Chat skills
k8s/                # Kubernetes manifests
helm/               # Helm chart
tests/              # Test suite
```

## Docker / Kubernetes

```bash
docker compose up -d                          # Start with GPU
docker compose --profile cpu up -d            # CPU only
python slate/slate_k8s_deploy.py --deploy     # K8s deploy
python slate/slate_k8s_deploy.py --status     # K8s status
```
