---
name: slate
description: Main SLATE orchestrator control. Use to start, stop, or manage all SLATE services.
---

# /slate

Control the main SLATE orchestrator — start, stop, or check status of all services.

## Usage
/slate [start | stop | status]

## Description

This skill provides control over the SLATE orchestrator which manages:
- Dashboard server (port 8080)
- Ollama LLM service (port 11434)
- GitHub Actions runner
- Workflow coordinator
- AI backend services

## Instructions

When the user invokes this skill, run the appropriate SLATE orchestrator command:

**Start all services:**
```powershell
.\.venv\Scripts\python.exe slate/slate_orchestrator.py start
```

**Stop all services:**
```powershell
.\.venv\Scripts\python.exe slate/slate_orchestrator.py stop
```

**Check status:**
```powershell
.\.venv\Scripts\python.exe slate/slate_orchestrator.py status
```

Report the results clearly showing which services started/stopped successfully.

## Examples

User: "/slate start"
→ Start all SLATE services

User: "/slate stop"
→ Stop all SLATE services

User: "/slate status"
→ Show orchestrator and service status

User: "Start SLATE"
→ Invoke this skill with start action
