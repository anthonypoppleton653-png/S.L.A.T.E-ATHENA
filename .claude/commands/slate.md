# /slate

Manage the SLATE orchestrator, services, and runner configuration.

## Usage
/slate [start | stop | status | restart | runner | costs]

## Instructions

Based on the argument provided (default: status), execute the appropriate command:

**Start SLATE:**
```powershell
.\.venv\Scripts\python.exe slate/slate_orchestrator.py start
```

**Stop SLATE:**
```powershell
.\.venv\Scripts\python.exe slate/slate_orchestrator.py stop
```

**Check status (default):**
```powershell
.\.venv\Scripts\python.exe slate/slate_orchestrator.py status
```

**Restart:**
Run stop then start.

**Runner management:**
```powershell
# Check runner status and fallback config
.\.venv\Scripts\python.exe slate/runner_fallback.py --status

# Enforce self-hosted only (no fallback)
.\.venv\Scripts\python.exe slate/runner_fallback.py --enforce

# Enable fallback to GitHub-hosted runners
.\.venv\Scripts\python.exe slate/runner_fallback.py --allow-fallback
```

**Cost tracking:**
```powershell
# Update and show cost report
.\.venv\Scripts\python.exe slate/runner_cost_tracker.py --update

# Show savings summary
.\.venv\Scripts\python.exe slate/runner_cost_tracker.py --savings

# Export costs to CSV
.\.venv\Scripts\python.exe slate/runner_cost_tracker.py --export
```

## Report Results
1. Which services started/stopped
2. Dashboard URL (http://localhost:8080) if started
3. Runner status (self-hosted vs fallback mode)
4. Cost savings if applicable
5. Any errors encountered
