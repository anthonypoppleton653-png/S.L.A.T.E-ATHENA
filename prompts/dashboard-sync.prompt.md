---
name: dashboard-sync
agent: 'agent'
description: 'Refresh SLATE dashboard data, broadcast system status, and sync project board state'
tags: [dashboard, sync, status, project-board, monitoring]
model: 'slate-fast'
# Modified: 2026-02-09T02:42:00-05:00 | Author: ANTIGRAVITY (Gemini) | Change: Fix model from haiku→slate-fast (local-only policy)
# AI Note: When modifying, add a comment with the current date, time, and a 'Gemini' marker.
---

# Dashboard Data Sync & Status Broadcast

Refresh all dashboard data sources, sync project board state, and broadcast current system status.

## Pipeline

### Step 1: Collect system state

```powershell
# Parallel data collection
$statusJob = Start-Job { & "E:\11132025\.venv\Scripts\python.exe" "E:\11132025\slate\slate_status.py" --json }
$workflowJob = Start-Job { & "E:\11132025\.venv\Scripts\python.exe" "E:\11132025\slate\slate_workflow_manager.py" --status }
$runtimeJob = Start-Job { & "E:\11132025\.venv\Scripts\python.exe" "E:\11132025\slate\slate_runtime.py" --json }

# Wait and collect
$status = Receive-Job $statusJob -Wait
$workflow = Receive-Job $workflowJob -Wait
$runtime = Receive-Job $runtimeJob -Wait

Write-Host "=== System Status ==="
Write-Host $status
Write-Host "=== Workflow ==="
Write-Host $workflow
Write-Host "=== Runtime ==="
Write-Host $runtime
```

### Step 2: Sync project boards

```powershell
# Bidirectional sync: KANBAN ↔ current_tasks.json
python slate/slate_project_board.py --sync    # Pull from KANBAN
python slate/slate_project_board.py --push    # Push completions to KANBAN
python slate/slate_project_board.py --status  # Report board state
```

### Step 3: Generate status summary via Ollama

Use slate-fast (3B) to produce a human-readable summary:

```powershell
python -c "
import subprocess, json

# Read current state
with open('current_tasks.json', 'r', encoding='utf-8') as f:
    tasks = json.load(f)

task_summary = json.dumps(tasks.get('tasks', [])[:10], indent=2)

prompt = f'''Generate a concise SLATE dashboard status report.

Tasks: {task_summary}

Include:
1. System health (one line)
2. Task summary: pending/in-progress/completed counts
3. Top 3 priority items
4. Any blockers or warnings
5. Recommended next action

Format as markdown with emoji indicators (✅ ⚠️ ❌ 🔄).
Keep under 20 lines.'''

result = subprocess.run(
    ['ollama', 'run', 'slate-fast', prompt],
    capture_output=True, text=True, timeout=30
)
print(result.stdout)
"
```

### Step 4: Update dashboard server

```powershell
# Refresh the FastAPI dashboard data
python -c "
import urllib.request, json

# Dashboard health check (local only)
try:
    req = urllib.request.urlopen('http://127.0.0.1:8080/api/health', timeout=5)
    health = json.loads(req.read())
    print(f'Dashboard: {health}')
except Exception as e:
    print(f'Dashboard offline: {e}')
    print('Start with: python slate/slate_orchestrator.py start')
"
```

### Step 5: Broadcast to FORGE.md

Append the status summary to FORGE.md for teammate visibility:

```powershell
python -c "
import datetime

timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
entry = f'''
### [COPILOT] {timestamp} | STATUS: Dashboard sync complete

**System**: Healthy | **Tasks**: N pending, N in-progress, N completed
**Boards**: Synced | **Dashboard**: Online/Offline
**Next action**: [recommended action]
'''

with open('FORGE.md', 'a', encoding='utf-8') as f:
    f.write(entry)

print(f'FORGE.md updated at {timestamp}')
"
```

## Scheduling

This prompt can be run:
- **On demand**: When boss asks for status
- **Hourly**: Via K8s CronJob (`workflow-cleanup` every 4h)
- **Pre-commit**: As part of the pre-commit protocol
- **Post-deploy**: After K8s or Docker deployment

## FORGE Log Entry

```
[COPILOT] TIMESTAMP | MAGIC: dashboard-sync
  System: healthy/degraded/offline
  Tasks: N pending / N active / N done
  Boards: synced/stale
  Dashboard: online/offline
```
