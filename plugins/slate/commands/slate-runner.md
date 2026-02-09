---
description: Manage GitHub Actions self-hosted runner
---

# /slate-runner

Manage the SLATE GitHub Actions self-hosted runner.

## Usage

```
/slate-runner [action]
```

## Actions

| Action | Description |
|--------|-------------|
| `status` | Runner status (default) |
| `setup` | Configure runner hooks |
| `dispatch` | Dispatch workflow |

## Instructions

**Status:**
```bash
.venv/Scripts/python.exe slate/slate_runner_manager.py --status
```

**Setup:**
```bash
.venv/Scripts/python.exe slate/slate_runner_manager.py --setup
```

**Dispatch:**
```bash
.venv/Scripts/python.exe slate/slate_runner_manager.py --dispatch "ci.yml"
```
