---
name: slate-claude
description: Validate and manage Claude Code configuration for SLATE.
---

# /slate-claude

Validate Claude Code integration and configuration.

## Usage
/slate-claude [validate | report | status | agent-options]

## Description

This skill validates Claude Code configuration including:
- MCP server connectivity
- Permission settings
- Hook integration
- Agent SDK options

## Instructions

When the user invokes this skill, run validation commands:

**Quick validation:**
```powershell
.\.venv_slate_ag\Scripts\python.exe -m slate/claude_code_manager.py --validate
```

**Full report:**
```powershell
.\.venv_slate_ag\Scripts\python.exe -m slate/claude_code_manager.py --report
```

**Agent SDK options:**
```powershell
.\.venv_slate_ag\Scripts\python.exe -m slate/claude_code_manager.py --agent-options
```

## Examples

User: "/slate-claude"
→ Run validation checks

User: "/slate-claude report"
→ Generate full integration report

User: "Is Claude Code configured correctly?"
→ Invoke this skill with validate action
