# SLATE Runner Skill

Manage the self-hosted GitHub Actions runner with GPU support.

## Current Runner

- **Name**: `slate-DESKTOP-R3UD82D`
- **Labels**: `self-hosted`, `slate`, `gpu`, `windows`, `cuda`, `gpu-2`, `blackwell`
- **Hardware**: 2x RTX 5070 Ti

## Commands

### Check Status
```powershell
.\.venv\Scripts\python.exe slate/slate_runner_manager.py --status
```

### Start Runner
```powershell
.\.venv\Scripts\python.exe slate/slate_runner_manager.py --start
```

### Stop Runner
```powershell
.\.venv\Scripts\python.exe slate/slate_runner_manager.py --stop
```

### Start as Service
```powershell
.\.venv\Scripts\python.exe slate/slate_runner_manager.py --start --service
```

### Provision SLATE Environment
```powershell
.\.venv\Scripts\python.exe slate/slate_runner_manager.py --provision
```

## MCP Tool

Use `slate_runner_status` to get runner status programmatically.

## Dashboard

Runner controls are available at http://127.0.0.1:8080 in the Runner panel.

## Runner Location

Default: `C:\actions-runner`

## Getting a Token

1. Go to https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E./settings/actions/runners
2. Click "New self-hosted runner"
3. Copy the token
4. Run: `python slate/slate_sdk.py --setup --runner --runner-token YOUR_TOKEN`

## Auto-Detected Labels

Labels are automatically detected based on hardware:
- `gpu` - If NVIDIA GPU detected
- `cuda` - If CUDA available
- `gpu-N` - Number of GPUs
- `blackwell` - RTX 50 series
- `ada-lovelace` - RTX 40 series
- `ampere` - RTX 30 series
