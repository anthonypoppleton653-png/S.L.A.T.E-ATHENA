---
name: slate-multirunner
description: Manage multiple GitHub Actions self-hosted runners with GPU allocation.
---

# /slate-multirunner

Manage multiple GitHub Actions self-hosted runners.

## Usage
/slate-multirunner [status | list | assign <runner> <gpu>]

## Description

This skill manages multiple GitHub Actions runners including:
- Runner status and health
- GPU assignment per runner
- Workflow distribution
- Runner lifecycle management

## Instructions

When the user invokes this skill, check runner configuration:

**List all runners:**
```powershell
Get-ChildItem -Path "e:\11132025" -Filter "actions-runner*" -Directory | ForEach-Object { $_.Name }
```

**Check runner status:**
```powershell
.\.venv_slate_ag\Scripts\python.exe -m slate/slate_runner_manager.py --status
```

## Examples

User: "/slate-multirunner"
→ Show all runner status

User: "/slate-multirunner list"
→ List configured runners

User: "How many runners are active?"
→ Invoke this skill with status action
