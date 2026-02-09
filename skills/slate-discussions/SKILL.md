---
name: slate-discussions
description: Manage GitHub Discussions for community engagement and feature ideation.
---

# /slate-discussions

Manage GitHub Discussions for the SLATE repository.

## Usage
/slate-discussions [status | unanswered | sync | metrics]

## Description

This skill integrates with GitHub Discussions for:
- Tracking unanswered Q&A
- Syncing Ideas to roadmap
- Engagement metrics
- Community management

## Instructions

When the user invokes this skill, run discussion management commands:

**Check discussion status:**
```powershell
.\.venv\Scripts\python.exe slate/slate_discussion_manager.py --status
```

**List unanswered Q&A:**
```powershell
.\.venv\Scripts\python.exe slate/slate_discussion_manager.py --unanswered
```

**Sync to tasks:**
```powershell
.\.venv\Scripts\python.exe slate/slate_discussion_manager.py --sync-tasks
```

## Examples

User: "/slate-discussions"
→ Show discussion system status

User: "/slate-discussions unanswered"
→ List unanswered Q&A discussions

User: "Any community questions?"
→ Invoke this skill with unanswered action
