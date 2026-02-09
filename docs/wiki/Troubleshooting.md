# Troubleshooting

Common issues and their solutions for S.L.A.T.E. (Synchronized Living Architecture for Transformation and Evolution).

---

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Installation Issues](#installation-issues)
3. [GPU Detection Problems](#gpu-detection-problems)
4. [Ollama Connection Issues](#ollama-connection-issues)
5. [Multi-Runner Problems](#multi-runner-problems)
6. [Kubernetes Deployment Issues](#kubernetes-deployment-issues)
7. [Claude Code Integration Issues](#claude-code-integration-issues)
8. [MCP Server Problems](#mcp-server-problems)
9. [Workflow and Task Queue Issues](#workflow-and-task-queue-issues)
10. [Memory and Performance Issues](#memory-and-performance-issues)
11. [Common Error Messages](#common-error-messages)
12. [Debug Commands and Log Locations](#debug-commands-and-log-locations)
13. [How to Report Issues](#how-to-report-issues)

---

## Quick Diagnostics

Run these commands first to identify issues:

```powershell
# Full system status (auto-detects everything)
.\.venv\Scripts\python.exe slate/slate_status.py --quick

# Check all integrations (Python, GPU, Ollama, K8s, etc.)
.\.venv\Scripts\python.exe slate/slate_runtime.py --check-all

# JSON output for automation
.\.venv\Scripts\python.exe slate/slate_status.py --json

# Test Ollama connection directly
curl http://127.0.0.1:11434/api/tags

# Check runner status
.\.venv\Scripts\python.exe slate/slate_runner_manager.py --status

# Validate Claude Code configuration
.\.venv\Scripts\python.exe slate/claude_code_manager.py --validate

# Check workflow health
.\.venv\Scripts\python.exe slate/slate_workflow_manager.py --status
```

---

## Installation Issues

### Virtual Environment Not Created

**Symptoms:**
- "python: command not found" or wrong Python version
- "No module named 'slate'" errors
- Scripts fail with import errors

**Solutions:**

```powershell
# Verify Python 3.11+
python --version

# Create virtual environment
python -m venv .venv

# Activate on Windows
.\.venv\Scripts\activate

# Activate on Linux/macOS
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"
```

### Dependency Installation Fails

**Symptoms:**
- "pip install" errors
- "Could not build wheels" errors
- Missing system libraries

**Solutions:**

```powershell
# Update pip
pip install --upgrade pip setuptools wheel

# Install with verbose output to see errors
pip install -e ".[dev]" -v

# For CUDA-related packages, ensure CUDA toolkit is installed
# Then reinstall PyTorch with correct CUDA version
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```

### Git Clone Issues

**Symptoms:**
- Repository clone fails
- Submodule errors
- Permission denied

**Solutions:**

```powershell
# Clone with submodules
git clone --recursive https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E.git

# If already cloned, initialize submodules
git submodule update --init --recursive

# For permission issues, check SSH key or use HTTPS
git remote set-url origin https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E.git
```

---

## GPU Detection Problems

### GPU Not Detected

**Symptoms:**
- "No CUDA devices found"
- `torch.cuda.is_available()` returns False
- Operations falling back to CPU
- `nvidia-smi` not found or returns errors

**Solutions:**

```powershell
# Check NVIDIA driver is installed
nvidia-smi

# If nvidia-smi not found, install NVIDIA drivers from:
# https://www.nvidia.com/Download/index.aspx

# Check CUDA installation
nvcc --version

# Verify PyTorch can see CUDA
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'Device count: {torch.cuda.device_count()}')"

# Check SLATE GPU detection
.\.venv\Scripts\python.exe slate/slate_status.py --quick
```

### CUDA Version Mismatch

**Symptoms:**
- "CUDA driver version is insufficient for CUDA runtime"
- PyTorch CUDA operations fail
- "CUDA error: no kernel image is available for execution"

**Solutions:**

```powershell
# Check your CUDA version
nvidia-smi  # Shows "CUDA Version" in top right

# Check PyTorch CUDA version
python -c "import torch; print(torch.version.cuda)"

# Reinstall PyTorch with matching CUDA
# For CUDA 12.4:
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# For CUDA 12.1:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Check hardware optimizer for details
.\.venv\Scripts\python.exe slate/slate_hardware_optimizer.py --verbose
```

### Out of GPU Memory

**Symptoms:**
- "CUDA out of memory" errors
- Process crashes during inference
- GPU utilization shows 100% memory

**Solutions:**

```powershell
# Monitor GPU memory in real-time
nvidia-smi -l 1

# Check what processes are using GPU
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv

# Clear GPU memory from Python
python -c "import torch; torch.cuda.empty_cache(); print('GPU cache cleared')"

# Reduce batch size or use smaller models
# In Ollama, unload unused models:
ollama stop

# Use smaller models (phi is ~1.6GB)
ollama pull phi:latest
```

### Multi-GPU Not Working

**Symptoms:**
- Only one GPU being used
- CUDA_VISIBLE_DEVICES not respected
- Uneven GPU utilization

**Solutions:**

```powershell
# Verify both GPUs are visible
nvidia-smi

# Set CUDA_VISIBLE_DEVICES to use specific GPUs
$env:CUDA_VISIBLE_DEVICES = "0,1"

# Check PyTorch sees both
python -c "import torch; print(f'GPUs: {torch.cuda.device_count()}')"

# Check SLATE GPU manager
.\.venv\Scripts\python.exe slate/slate_gpu.py --status

# Configure Ollama for multi-GPU (requires restart)
# Edit ~/.ollama/config.json or set environment:
$env:OLLAMA_NUM_GPU = 2
ollama serve
```

---

## Ollama Connection Issues

### Ollama Not Running

**Symptoms:**
- Connection refused on port 11434
- "Could not connect to Ollama" errors
- `curl http://127.0.0.1:11434/api/tags` fails

**Solutions:**

```powershell
# Start Ollama service
ollama serve

# Or on Windows, start the Ollama application from Start menu

# Verify it's running
curl http://127.0.0.1:11434/api/tags

# Check if port is blocked
netstat -an | findstr 11434

# If port in use by another process, find and stop it
netstat -ano | findstr 11434
taskkill /F /PID <pid>
```

### No Models Available

**Symptoms:**
- Empty model list
- "Model not found" errors
- `ollama list` shows no models

**Solutions:**

```powershell
# List available models
ollama list

# Pull recommended SLATE model (mistral-nemo ~7GB)
ollama pull mistral-nemo

# Or pull smaller model for testing (~1.6GB)
ollama pull phi:latest

# Verify model is available
ollama list

# Test model works
ollama run phi "Hello, test message"
```

### Model Load Failures

**Symptoms:**
- "Out of memory" during model loading
- Model loading hangs indefinitely
- "Error loading model" messages

**Solutions:**

```powershell
# Check GPU memory before loading
nvidia-smi

# Unload all current models
ollama stop

# Try a smaller model first
ollama pull phi:latest
ollama run phi "test"

# If that works, try larger model with single GPU
$env:OLLAMA_NUM_GPU = 1
ollama pull mistral-nemo

# Check Ollama logs (Windows)
# Look in %APPDATA%\Ollama\logs or console output

# Check Ollama logs (Linux/macOS)
journalctl -u ollama
# or
~/.ollama/logs/server.log
```

### Ollama Timeout Errors

**Symptoms:**
- Requests timeout after 60 seconds
- "Context deadline exceeded"
- Slow responses or hanging

**Solutions:**

```powershell
# Increase timeout in environment
$env:OLLAMA_REQUEST_TIMEOUT = "300"

# Restart Ollama with new timeout
ollama serve

# Check system resources
# High CPU/memory usage may indicate resource contention
taskmgr

# Try running inference directly to isolate issue
ollama run phi "quick test"
```

---

## Multi-Runner Problems

### Runner Not Detected

**Symptoms:**
- "Runner not installed" messages
- `--detect` shows no runner
- Runner exists but SLATE doesn't find it

**Solutions:**

```powershell
# Check runner detection
.\.venv\Scripts\python.exe slate/slate_runner_manager.py --detect

# SLATE looks for runners in these locations:
# - <workspace>/actions-runner
# - <workspace>/../actions-runner
# - C:/actions-runner
# - ~/actions-runner

# If runner is elsewhere, create symlink
# Windows (Admin PowerShell):
New-Item -ItemType SymbolicLink -Path "actions-runner" -Target "D:\path\to\runner"

# Linux/macOS:
ln -s /path/to/runner actions-runner
```

### Runner Not Starting

**Symptoms:**
- Runner process not running
- Service fails to start
- "Could not connect to GitHub" errors

**Solutions:**

```powershell
# Check runner status
.\.venv\Scripts\python.exe slate/slate_runner_manager.py --status

# Start runner manually (foreground mode)
cd actions-runner
.\run.cmd  # Windows
./run.sh   # Linux/macOS

# If service mode, check Windows service
Get-Service -Name "*actions*"
Start-Service -Name "actions.runner.*"

# Re-configure runner if needed
cd actions-runner
.\config.cmd remove  # Remove old config
.\config.cmd --url https://github.com/YOUR/REPO --token YOUR_TOKEN
```

### GitHub Authentication Issues

**Symptoms:**
- "Not authenticated" in runner status
- Workflow dispatch fails
- "gh auth status" fails

**Solutions:**

```powershell
# Check GitHub CLI authentication
gh auth status

# Re-authenticate
gh auth login

# For workflow dispatch, ensure token has "workflow" scope
gh auth login --scopes workflow

# Test repository access
gh repo view

# List workflows
gh workflow list
```

### Workflow Dispatch Failures

**Symptoms:**
- "Failed to dispatch workflow" errors
- Workflow doesn't start
- "Workflow not found" messages

**Solutions:**

```powershell
# List available workflows
gh workflow list

# Check workflow exists and is enabled
gh workflow view ci.yml

# Manually dispatch to test
gh workflow run ci.yml

# Check recent runs
gh run list --limit 5

# View specific run logs
gh run view <run-id> --log

# Enable disabled workflow
gh workflow enable ci.yml
```

---

## Kubernetes Deployment Issues

### kubectl Not Found

**Symptoms:**
- "kubectl not found" errors
- K8s status shows unavailable
- Cannot deploy to cluster

**Solutions:**

```powershell
# Install kubectl
# Windows (winget):
winget install Kubernetes.kubectl

# Windows (chocolatey):
choco install kubernetes-cli

# Verify installation
kubectl version --client

# Configure cluster access
kubectl config view
kubectl config use-context <context-name>
```

### Cluster Connection Failed

**Symptoms:**
- "Unable to connect to the server"
- "The connection to the server was refused"
- Context not set

**Solutions:**

```powershell
# Check current context
kubectl config current-context

# List available contexts
kubectl config get-contexts

# Switch to correct context
kubectl config use-context docker-desktop
# or
kubectl config use-context minikube

# Test connection
kubectl cluster-info

# For minikube, ensure it's running
minikube status
minikube start
```

### Pods Not Starting

**Symptoms:**
- Pods stuck in Pending/CrashLoopBackOff
- ImagePullBackOff errors
- OOMKilled pods

**Solutions:**

```powershell
# Check pod status
kubectl get pods -n slate

# Describe problem pod
kubectl describe pod <pod-name> -n slate

# Check pod logs
kubectl logs <pod-name> -n slate
kubectl logs <pod-name> -n slate --previous  # Previous container

# For ImagePullBackOff - check image exists and registry access
kubectl describe pod <pod-name> -n slate | findstr "Image"

# For CrashLoopBackOff - check container logs
kubectl logs <pod-name> -n slate -f

# For OOMKilled - increase memory limits in deployment
kubectl edit deployment <deployment-name> -n slate
```

### Service Not Accessible

**Symptoms:**
- Cannot reach service via port-forward
- Service health check fails
- "Connection refused" from within cluster

**Solutions:**

```powershell
# Check service exists
kubectl get svc -n slate

# Check endpoints (should show pod IPs)
kubectl get endpoints -n slate

# Port-forward for testing
kubectl port-forward -n slate svc/slate-dashboard-svc 8080:8080

# Check pod is ready
kubectl get pods -n slate -o wide

# Test from within cluster (run a test pod)
kubectl run test-curl --rm -it --image=curlimages/curl -- sh
# Then: curl http://slate-dashboard-svc.slate:8080/health
```

### PersistentVolumeClaim Pending

**Symptoms:**
- PVCs stuck in Pending state
- "No persistent volumes available" errors

**Solutions:**

```powershell
# Check PVC status
kubectl get pvc -n slate

# Describe PVC for details
kubectl describe pvc <pvc-name> -n slate

# Check available PVs
kubectl get pv

# For local development, create a local storage class
kubectl apply -f - <<EOF
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: local-storage
provisioner: kubernetes.io/no-provisioner
volumeBindingMode: WaitForFirstConsumer
EOF

# Or use hostPath for testing (not for production)
```

### GPU Not Available in K8s

**Symptoms:**
- GPU pods won't schedule
- "Insufficient nvidia.com/gpu" error
- GPU device plugin not installed

**Solutions:**

```powershell
# Check for NVIDIA device plugin
kubectl get daemonset -n kube-system | findstr nvidia

# Install NVIDIA device plugin
kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.0/nvidia-device-plugin.yml

# Check node GPU capacity
kubectl describe node | findstr -A 5 "Capacity"

# Check GPU allocatable
kubectl describe node | findstr "nvidia.com/gpu"

# Verify SLATE K8s GPU detection
.\.venv\Scripts\python.exe slate/k8s_integration.py --gpu
```

---

## Claude Code Integration Issues

### Plugin Not Loading

**Symptoms:**
- SLATE commands not available
- `/slate:status` not recognized
- Plugin scope mismatch errors

**Solutions:**

```powershell
# For local development (this workspace):
# Just cd into the workspace - plugin auto-loads
cd /path/to/S.L.A.T.E
claude  # Plugin should load automatically

# Check plugin manifest exists
dir .claude-plugin\plugin.json

# Verify manifest is valid JSON
python -c "import json; print(json.load(open('.claude-plugin/plugin.json')))"

# Do NOT mix local and marketplace plugins
# If you have .claude-plugin/, don't use /plugin install
```

### Permission Errors

**Symptoms:**
- "Permission denied" for tool use
- ActionGuard blocking commands
- "Ask" prompts appearing unexpectedly

**Solutions:**

```powershell
# Check current permissions
.\.venv\Scripts\python.exe slate/claude_code_manager.py --status

# View permission rules
type .claude\settings.local.json

# Add permission rule
.\.venv\Scripts\python.exe slate/claude_code_manager.py --add-permission "Bash(*)"

# Check ActionGuard is not blocking legitimate commands
.\.venv\Scripts\python.exe slate/action_guard.py --validate "python --version"
```

### Behavior Profile Not Active

**Symptoms:**
- SLATE Operator behavior not applied
- Default Claude Code behavior instead
- Security protocols not enforced

**Solutions:**

```powershell
# Verify settings.json has behavior reference
type .claude\settings.json | findstr "behavior"

# Should contain:
# "behavior": { "profile": "slate-operator" }

# Check behavior file exists
type .claude\behaviors\slate-operator.md

# Verify settings.local.json for permissions
type .claude\settings.local.json
```

### Validation Failures

**Symptoms:**
- Claude Code validation reports failures
- Missing or invalid configuration
- Integration tests failing

**Solutions:**

```powershell
# Run validation
.\.venv\Scripts\python.exe slate/claude_code_manager.py --validate

# Generate full report
.\.venv\Scripts\python.exe slate/claude_code_manager.py --report

# Check specific component
.\.venv\Scripts\python.exe slate/claude_code_validator.py --check settings
.\.venv\Scripts\python.exe slate/claude_code_validator.py --check mcp
.\.venv\Scripts\python.exe slate/claude_code_validator.py --check plugin
```

---

## MCP Server Problems

### MCP Server Won't Start

**Symptoms:**
- "MCP package not installed" error
- Server process crashes immediately
- "Connection refused" from Claude Code

**Solutions:**

```powershell
# Install MCP package
pip install mcp

# Test server manually
.\.venv\Scripts\python.exe slate/mcp_server.py

# Check for import errors
python -c "from mcp.server import Server; print('MCP OK')"

# Verify Python path
python -c "import sys; print(sys.executable)"
```

### MCP Tools Not Available

**Symptoms:**
- Tools not listed in Claude Code
- "Tool not found" errors
- Empty tool list

**Solutions:**

```powershell
# Test MCP server tool listing
.\.venv\Scripts\python.exe slate/claude_code_manager.py --test-mcp slate

# Check .mcp.json configuration
type .mcp.json

# Verify paths in .mcp.json are correct
# Ensure ${CLAUDE_PLUGIN_ROOT} is being expanded

# Restart Claude Code after MCP changes
```

### MCP Tool Execution Fails

**Symptoms:**
- Tool returns errors
- "Command timed out" messages
- Subprocess failures

**Solutions:**

```powershell
# Test tool directly (bypassing MCP)
.\.venv\Scripts\python.exe slate/slate_status.py --quick

# Check venv Python is correct
.\.venv\Scripts\python.exe --version

# Increase timeout if needed (default 60s)
# Edit mcp_server.py timeout parameter

# Check for missing dependencies
pip check
```

---

## Workflow and Task Queue Issues

### Tasks Not Processing

**Symptoms:**
- Tasks stuck in pending
- No agent picking up tasks
- Workflow not starting

**Solutions:**

```powershell
# Check task queue status
.\.venv\Scripts\python.exe slate/slate_workflow_manager.py --status

# View current tasks
type current_tasks.json

# Check for stale tasks (in-progress > 4 hours)
.\.venv\Scripts\python.exe slate/slate_workflow_manager.py --cleanup

# Verify runner is available
.\.venv\Scripts\python.exe slate/slate_runner_manager.py --status

# Dispatch workflow manually
gh workflow run agentic.yml
```

### Stale Task Accumulation

**Symptoms:**
- Many in-progress tasks for hours
- Task queue blocked
- "Max concurrent tasks reached"

**Solutions:**

```powershell
# Auto-cleanup stale tasks
.\.venv\Scripts\python.exe slate/slate_workflow_manager.py --cleanup

# Force cleanup with enforcement
.\.venv\Scripts\python.exe slate/slate_workflow_manager.py --enforce

# Manually reset stuck task
# Edit current_tasks.json and change "status": "in_progress" to "pending"

# Archive and reset entire queue (last resort)
mv current_tasks.json current_tasks.json.bak
echo '{"tasks": [], "created_at": "2026-02-08T00:00:00Z"}' > current_tasks.json
```

### Corrupted Task File

**Symptoms:**
- JSON parse errors
- "Error loading tasks" messages
- Task operations fail silently

**Solutions:**

```powershell
# Validate JSON syntax
python -c "import json; json.load(open('current_tasks.json'))"

# If invalid, check for backup
dir current_tasks.json.bak

# Reset to empty queue
echo '{"tasks": [], "created_at": "2026-02-08T00:00:00Z"}' > current_tasks.json

# Recover from archive
type .slate_archive\archived_tasks.json

# Check for lock file issues
del current_tasks.json.lock
```

### File Lock Deadlock

**Symptoms:**
- Operations hang indefinitely
- "Timeout waiting for lock" errors
- Multiple processes stuck

**Solutions:**

```powershell
# Remove stale lock file
del current_tasks.json.lock

# Check for processes holding the file
handle.exe current_tasks.json  # Requires Sysinternals

# Kill stuck Python processes
tasklist | findstr python
taskkill /F /PID <pid>

# Restart with fresh state
.\.venv\Scripts\python.exe slate/slate_workflow_manager.py --status
```

---

## Memory and Performance Issues

### Slow Inference

**Symptoms:**
- Long response times (>30 seconds)
- High latency on simple queries
- CPU-bound inference

**Solutions:**

```powershell
# Check GPU utilization (should show inference activity)
nvidia-smi -l 1

# Ensure GPU is being used
python -c "import torch; print(torch.cuda.is_available())"

# Use faster model
ollama pull phi:latest  # ~1.6GB, very fast

# Check if model is already loaded (warm)
ollama ps

# Pre-warm model before use
ollama run phi "warmup"
```

### High Memory Usage

**Symptoms:**
- System slowdown
- Swapping/paging
- Out of memory errors

**Solutions:**

```powershell
# Monitor memory usage
taskmgr  # Windows
htop     # Linux

# Check GPU memory
nvidia-smi

# Unload unused Ollama models
ollama stop

# Clear Python caches
python -c "import torch; torch.cuda.empty_cache()"

# Reduce concurrent tasks
# Edit SlateWorkflowManager.MAX_CONCURRENT_TASKS in slate/slate_workflow_manager.py

# Restart services to clear memory
.\.venv\Scripts\python.exe slate/slate_orchestrator.py stop
.\.venv\Scripts\python.exe slate/slate_orchestrator.py start
```

### Dashboard Slow or Unresponsive

**Symptoms:**
- UI hangs or freezes
- WebSocket disconnects
- Slow API responses

**Solutions:**

```powershell
# Check dashboard server
curl http://127.0.0.1:8080/api/status

# Restart dashboard
# Kill existing process
netstat -ano | findstr 8080
taskkill /F /PID <pid>

# Start fresh
.\.venv\Scripts\python.exe agents/slate_dashboard_server.py

# Check for blocking operations
# Review server logs for slow endpoints
```

### Import/Startup Slowness

**Symptoms:**
- Long startup time
- Slow imports
- "Loading..." messages

**Solutions:**

```powershell
# Profile imports
python -X importtime slate/slate_status.py 2>&1 | sort -n

# Check for unnecessary imports
# Use lazy imports for heavy modules

# Verify SSD/disk performance
winsat disk -drive c

# Use __pycache__ (enabled by default)
# Clear corrupted cache if needed
python -c "import py_compile; py_compile.compile('slate/slate_status.py')"
```

---

## Common Error Messages

### "ModuleNotFoundError: No module named 'slate'"

**Cause:** Python path not configured or venv not activated.

**Solution:**
```powershell
.\.venv\Scripts\activate
pip install -e .
```

### "CUDA out of memory"

**Cause:** GPU memory exhausted by model or batch size.

**Solution:**
```powershell
# Clear cache and use smaller model
python -c "import torch; torch.cuda.empty_cache()"
ollama pull phi:latest
```

### "Connection refused on port 11434"

**Cause:** Ollama service not running.

**Solution:**
```powershell
ollama serve
```

### "ActionGuard: Blocked pattern detected"

**Cause:** Command matches dangerous pattern (rm -rf, 0.0.0.0, etc.).

**Solution:**
```powershell
# Review command for safety
# Use safer alternative
# If legitimate, check action_guard.py patterns
```

### "kubectl: command not found"

**Cause:** kubectl not installed or not in PATH.

**Solution:**
```powershell
winget install Kubernetes.kubectl
# Add to PATH if needed
```

### "gh: command not found"

**Cause:** GitHub CLI not installed.

**Solution:**
```powershell
winget install GitHub.cli
gh auth login
```

### "Runner not installed"

**Cause:** GitHub Actions runner not found in expected locations.

**Solution:**
```powershell
# Download runner from GitHub repo Settings > Actions > Runners
# Extract to one of:
#   <workspace>/actions-runner
#   C:/actions-runner
#   ~/actions-runner
```

### "MCP package not installed"

**Cause:** MCP library missing from environment.

**Solution:**
```powershell
pip install mcp
```

### "Permission denied" in Claude Code

**Cause:** Tool not allowed by settings or ActionGuard.

**Solution:**
```powershell
.\.venv\Scripts\python.exe slate/claude_code_manager.py --add-permission "Bash(*)"
```

---

## Debug Commands and Log Locations

### Diagnostic Commands

```powershell
# Full system diagnostic
.\.venv\Scripts\python.exe slate/slate_status.py --quick

# JSON output for scripting
.\.venv\Scripts\python.exe slate/slate_status.py --json > status.json

# Runtime integration check
.\.venv\Scripts\python.exe slate/slate_runtime.py --check-all

# Hardware and GPU details
.\.venv\Scripts\python.exe slate/slate_hardware_optimizer.py --verbose

# Claude Code validation
.\.venv\Scripts\python.exe slate/claude_code_manager.py --report

# K8s cluster status
.\.venv\Scripts\python.exe slate/k8s_integration.py --cluster

# Workflow health
.\.venv\Scripts\python.exe slate/slate_workflow_manager.py --status

# Runner detailed status
.\.venv\Scripts\python.exe slate/slate_runner_manager.py --detect --json

# ActionGuard command testing
.\.venv\Scripts\python.exe slate/action_guard.py --validate "your command here"
```

### Log Locations

| Component | Log Location |
|-----------|--------------|
| Error logs | `.slate_errors/` |
| Archived tasks | `.slate_archive/` |
| Tech tree state | `.slate_tech_tree/tech_tree.json` |
| Code changes | `.slate_changes/` |
| Nemo sessions | `.slate_nemo/` |
| Vector index | `.slate_index/` |
| Ollama logs (Windows) | `%APPDATA%\Ollama\logs\` |
| Ollama logs (Linux) | `~/.ollama/logs/` or journalctl |
| GitHub runner logs | `actions-runner/_diag/` |
| K8s pod logs | `kubectl logs <pod> -n slate` |

### Collecting Diagnostics for Bug Reports

```powershell
# Create diagnostic bundle
mkdir slate_diag
.\.venv\Scripts\python.exe slate/slate_status.py --json > slate_diag\status.json
.\.venv\Scripts\python.exe slate/slate_runtime.py --check-all > slate_diag\runtime.txt
.\.venv\Scripts\python.exe slate/slate_hardware_optimizer.py --verbose > slate_diag\hardware.txt
.\.venv\Scripts\python.exe slate/claude_code_manager.py --report > slate_diag\claude.txt
.\.venv\Scripts\python.exe slate/slate_workflow_manager.py --status > slate_diag\workflow.txt
copy current_tasks.json slate_diag\
nvidia-smi > slate_diag\gpu.txt 2>&1
python --version > slate_diag\python.txt
pip list > slate_diag\packages.txt

# Compress for sharing
Compress-Archive -Path slate_diag -DestinationPath slate_diagnostics.zip
```

---

## How to Report Issues

### Before Reporting

1. **Check this troubleshooting guide** - Your issue may already be documented
2. **Run diagnostics** - Collect output from the diagnostic commands above
3. **Check recent changes** - Did the issue start after an update?
4. **Try basic fixes** - Restart services, clear caches, check connections

### Required Information

When reporting an issue, include:

1. **Environment:**
   - Operating system and version
   - Python version (`python --version`)
   - GPU model and driver version (`nvidia-smi`)
   - SLATE version/commit (`git log -1 --oneline`)

2. **Diagnostic output:**
   - `slate/slate_status.py --json` output
   - Relevant error messages (full traceback)
   - Steps to reproduce

3. **Configuration:**
   - `.mcp.json` (remove any secrets)
   - `.claude/settings.json` (relevant sections)
   - Environment variables (SLATE_*, CUDA_*)

### Reporting Channels

1. **GitHub Issues** (preferred):
   - https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E/issues
   - Use issue templates when available
   - Tag appropriately (bug, enhancement, question)

2. **GitHub Discussions** (for questions):
   - https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E/discussions
   - Use Q&A category for troubleshooting help

### Security Issues

For security vulnerabilities:
- Do NOT create a public issue
- Email security concerns privately
- Include reproduction steps and potential impact

---

## Reset to Clean State

If all else fails, reset to a clean state:

```powershell
# 1. Backup important data
copy current_tasks.json tasks_backup.json
copy .slate_tech_tree\tech_tree.json tech_tree_backup.json

# 2. Stop all services
.\.venv\Scripts\python.exe slate/slate_orchestrator.py stop
ollama stop

# 3. Clean caches and temporary files
Remove-Item -Recurse -Force slate_cache\ -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force .slate_errors\ -ErrorAction SilentlyContinue
Remove-Item -Force *.lock -ErrorAction SilentlyContinue

# 4. Reinstall dependencies
pip install -e ".[dev]" --force-reinstall

# 5. Reset configuration (optional - destructive!)
# Remove-Item -Recurse -Force .slate_index\  # Vector DB
# echo '{"tasks": []}' > current_tasks.json   # Task queue

# 6. Restart services
.\.venv\Scripts\python.exe slate/slate_orchestrator.py start

# 7. Verify
.\.venv\Scripts\python.exe slate/slate_status.py --quick
```

---

## Next Steps

- [Configuration](Configuration) - Review your settings
- [CLI Reference](CLI-Reference) - Command documentation
- [Development](Development) - Contributing guide
- [Architecture](Architecture) - System design overview
