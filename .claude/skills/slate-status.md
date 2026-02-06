# SLATE Status Skill

Check system health, GPU status, and component availability.

## Commands

### Quick Status
```powershell
.\.venv\Scripts\python.exe slate/slate_status.py --quick
```

### Full Status (JSON)
```powershell
.\.venv\Scripts\python.exe slate/slate_status.py --json
```

### SDK Status
```powershell
.\.venv\Scripts\python.exe slate/slate_sdk.py --status
```

### Verify Installation
```powershell
.\.venv\Scripts\python.exe slate/slate_sdk.py --verify
```

## MCP Tool

Use `slate_get_status` to get system status programmatically.

## Components Checked

- GPU availability (nvidia-smi)
- Python environment (.venv)
- Core modules (slate_status, action_guard, sdk_source_guard)
- AI backends (Ollama, Foundry Local)
- Self-hosted runner status
- Task queue state

## Interpreting Status

| Status | Meaning |
|--------|---------|
| `online` | Component running and healthy |
| `offline` | Component not running |
| `degraded` | Running but with issues |
| `unknown` | Cannot determine state |
