# /slate-discussions

Manage GitHub Discussions integration with SLATE workflow system.

## Usage
/slate-discussions [--status | --unanswered | --sync | --metrics]

## Instructions

Based on the argument provided (default: --status):

**For status check (default):**
```powershell
.\.venv\Scripts\python.exe slate/slate_discussion_manager.py --status
```

**For unanswered Q&A:**
```powershell
.\.venv\Scripts\python.exe slate/slate_discussion_manager.py --unanswered
```

**For syncing to tasks:**
```powershell
.\.venv\Scripts\python.exe slate/slate_discussion_manager.py --sync-tasks
```

**For engagement metrics:**
```powershell
.\.venv\Scripts\python.exe slate/slate_discussion_manager.py --metrics
```

**For full processing:**
```powershell
.\.venv\Scripts\python.exe slate/slate_discussion_manager.py --process-all
```

Report findings including:
1. Total discussions and categories
2. Unanswered Q&A count
3. Stale discussions (>7 days)
4. Recent activity metrics

## Discussion Categories

| Category | Routing | Action |
|----------|---------|--------|
| Announcements | None | Informational only |
| Ideas/Feature | ROADMAP board | Creates tracking issue |
| Q&A/Help | Metrics tracking | Monitors response time |
| Show & Tell | Engagement log | Community showcase |
| Bugs/Issues | BUG TRACKING | Creates bug issue |

## Workflow Integration

The `discussion-automation.yml` workflow:
- Triggers on discussion events (create, edit, label, answer)
- Runs PII scanning before processing
- Routes to appropriate project boards
- Hourly scheduled processing for metrics

ARGUMENTS: --status
