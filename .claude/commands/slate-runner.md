# /slate-runner

Manage the GitHub Actions self-hosted runner for SLATE.

## Usage
/slate-runner [--status | --setup | --dispatch <workflow>]

## Instructions

Based on the argument provided (default: --status):

**Check runner status:**
```bash
./.venv/Scripts/python.exe slate/slate_runner_manager.py --status
```

**Auto-configure runner:**
```bash
./.venv/Scripts/python.exe slate/slate_runner_manager.py --setup
```

**Dispatch a workflow:**
```bash
./.venv/Scripts/python.exe slate/slate_runner_manager.py --dispatch "ci.yml"
```

Report findings including:
1. Runner online/offline status
2. GPU configuration detected
3. Labels configured (self-hosted, slate, gpu, cuda, etc.)
4. Pre-job hooks status
5. Recent workflow runs
