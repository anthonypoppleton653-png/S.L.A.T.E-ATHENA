---
name: workflow-cleanup
agent: 'agent'
description: 'Clean up stale tasks, enforce completion rules, and maintain workflow health'
tags: [workflow, maintenance, tasks]
model: 'haiku'
---

# Workflow Cleanup

Maintain healthy task workflow by cleaning stale tasks and enforcing completion rules.

## Check Workflow Status

First, assess the current state:

```powershell
python slate/slate_workflow_manager.py --status
```

## Cleanup Operations

### Auto-Cleanup Stale Tasks

Tasks in-progress for >4 hours are considered stale:

```powershell
python slate/slate_workflow_manager.py --cleanup
```

This will:
- Reset stale tasks to pending
- Archive abandoned tasks (>24h pending)
- Remove duplicate tasks
- Update task timestamps

### Enforce Completion Rules

Before creating new tasks, verify existing tasks are handled:

```powershell
python slate/slate_workflow_manager.py --enforce
```

This blocks new task creation if:
- More than 5 tasks are in-progress
- Stale tasks exist without resolution
- Duplicate tasks are detected

## Task States

| State | Duration Threshold | Action |
|-------|-------------------|--------|
| pending | >24h | Flag for review |
| in_progress | >4h | Auto-reset to pending |
| completed | N/A | Archive after 7 days |
| failed | N/A | Require manual review |

## Manual Task Management

### View all tasks
```powershell
python slate/slate_workflow_manager.py --list
```

### Reset specific task
```powershell
python slate/slate_workflow_manager.py --reset <task-id>
```

### Archive completed
```powershell
python slate/slate_workflow_manager.py --archive-completed
```

## Best Practices

1. Run cleanup before starting new work sessions
2. Check workflow status after long-running operations
3. Don't create new tasks if existing ones are stale
4. Review failed tasks before retrying
