# SLATE Tasks Skill

Manage the SLATE task queue for agent work distribution.

## Task File

Tasks are stored in `current_tasks.json` at the workspace root.

## Commands

### List Tasks
```powershell
.\.venv\Scripts\python.exe slate/slate_status.py --tasks
```

### Task Summary
```powershell
.\.venv\Scripts\python.exe -c "
import json
from pathlib import Path
tasks = json.loads(Path('current_tasks.json').read_text())
pending = len([t for t in tasks if t.get('status') == 'pending'])
progress = len([t for t in tasks if t.get('status') == 'in-progress'])
done = len([t for t in tasks if t.get('status') == 'completed'])
print(f'Tasks: {len(tasks)} total, {pending} pending, {progress} in-progress, {done} done')
"
```

## MCP Tool

Use `slate_list_tasks` to get tasks programmatically.

## Task Structure

```json
{
  "id": "task_001",
  "title": "Implement feature X",
  "description": "Detailed description...",
  "status": "pending",
  "priority": "high",
  "assigned_to": "ALPHA",
  "created_at": "2026-02-06T12:00:00Z"
}
```

## Task Statuses

| Status | Meaning |
|--------|---------|
| `pending` | Not yet started |
| `in-progress` | Being worked on |
| `completed` | Finished |
| `blocked` | Waiting on dependency |

## Agent Assignment

| Agent | Role |
|-------|------|
| `ALPHA` | Coding & implementation |
| `BETA` | Testing & validation |
| `GAMMA` | Planning & triage |
| `DELTA` | Claude Code bridge |
| `auto` | ML-based smart routing |
