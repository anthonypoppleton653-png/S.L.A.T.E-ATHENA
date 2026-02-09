---
description: Manage SLATE task workflow queue
---

# /slate-workflow

Manage the SLATE task workflow queue.

## Usage

```
/slate-workflow [action]
```

## Actions

| Action | Description |
|--------|-------------|
| `status` | Show queue status (default) |
| `cleanup` | Remove stale tasks (>4h) |
| `enforce` | Check rules before new tasks |

## Instructions

**Status:**
```bash
.venv/Scripts/python.exe slate/slate_workflow_manager.py --status
```

**Cleanup:**
```bash
.venv/Scripts/python.exe slate/slate_workflow_manager.py --cleanup
```

**Enforce:**
```bash
.venv/Scripts/python.exe slate/slate_workflow_manager.py --enforce
```
