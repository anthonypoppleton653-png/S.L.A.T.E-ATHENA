# Getting Started
<!-- Modified: 2026-02-08T12:00:00Z | Author: Claude Opus 4.5 | Change: Comprehensive update with installation options, first-time setup, verification, and examples -->

<div align="center">

**Turn your local hardware into an AI operations center for GitHub**

*One command. Full ecosystem.*

</div>

---

## System Requirements

<table>
<tr>
<th>Component</th>
<th>Minimum</th>
<th>Recommended</th>
</tr>
<tr>
<td><strong>Python</strong></td>
<td>3.11+</td>
<td>3.12+ (latest stable)</td>
</tr>
<tr>
<td><strong>Git</strong></td>
<td>2.30+</td>
<td>2.40+ with Git LFS</td>
</tr>
<tr>
<td><strong>RAM</strong></td>
<td>8GB</td>
<td>16GB+ for multi-model inference</td>
</tr>
<tr>
<td><strong>Storage</strong></td>
<td>10GB</td>
<td>50GB+ for models and vector store</td>
</tr>
<tr>
<td><strong>GPU</strong></td>
<td>Optional (CPU works)</td>
<td>NVIDIA RTX 20xx+ with 8GB+ VRAM</td>
</tr>
<tr>
<td><strong>OS</strong></td>
<td>Windows 10, Ubuntu 20.04, macOS 12</td>
<td>Windows 11, Ubuntu 22.04, macOS 14</td>
</tr>
<tr>
<td><strong>CUDA</strong></td>
<td>11.8 (if GPU)</td>
<td>12.4+ (for Blackwell/Ada)</td>
</tr>
</table>

**Download Links:**
- [Python](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)
- [CUDA Toolkit](https://developer.nvidia.com/cuda-downloads) (optional)
- [VS Code](https://code.visualstudio.com/) with [Claude Code extension](https://marketplace.visualstudio.com/items?itemName=Anthropic.claude-code)

---

## Installation Options

Choose the installation method that best fits your workflow:

### Option 1: Full Ecosystem Install (Recommended)

One command installs everything with a live dashboard.

```bash
git clone https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E.git && cd S.L.A.T.E && python install_slate.py
```

The installer:
- Creates virtual environment
- Installs all dependencies (PyTorch with CUDA auto-detection)
- Configures Ollama models
- Sets up ChromaDB vector store
- Starts dashboard at **http://127.0.0.1:8080**

### Option 2: Copilot-Assisted Install

Using Claude Code or GitHub Copilot with SLATE plugin:

```
@slate /install
```

Or within a Claude Code session:

```
/slate-status --install
```

The Copilot-assisted install provides:
- Interactive configuration prompts
- Hardware detection and optimization
- Step-by-step progress feedback
- Automatic troubleshooting

### Option 3: Manual Setup

For full control over each step:

```bash
# 1. Clone repository
git clone https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E.git
cd S.L.A.T.E

# 2. Create virtual environment
python -m venv .venv

# 3. Activate (choose your OS)
.venv\Scripts\activate              # Windows (cmd)
.venv\Scripts\Activate.ps1          # Windows (PowerShell)
source .venv/bin/activate           # Linux/macOS

# 4. Install dependencies
pip install -r requirements.txt

# 5. Install PyTorch with CUDA (optional, for GPU)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# 6. Verify installation
python slate/slate_status.py --quick
```

### Option 4: Docker Deployment

For containerized environments:

```bash
# Build release image (CUDA 12.8)
docker build -t slate:local .

# Quick start with Docker Compose (GPU)
docker-compose up -d

# Access dashboard
# http://127.0.0.1:8080
```

**CPU-only Docker:**

```bash
docker build -f Dockerfile.cpu -t slate:cpu .
docker run -d -p 8080:8080 slate:cpu
```

### Option 5: Kubernetes Local Cloud

For production stability with full microservices:

```powershell
# Deploy with Kustomize (local overlay)
kubectl apply -k k8s/overlays/local/

# Check deployment status
python slate/slate_k8s_deploy.py --status

# Health check all pods
python slate/slate_k8s_deploy.py --health

# Port-forward services to localhost
python slate/slate_k8s_deploy.py --port-forward
```

**Helm deployment:**

```bash
helm install slate ./helm -n slate --create-namespace -f helm/values.yaml
```

See [Architecture > Kubernetes](Architecture#kubernetes--container-architecture) for full deployment details.

---

## What Gets Installed

<table>
<tr>
<th>Component</th>
<th>Purpose</th>
<th>Port</th>
<th>Cost</th>
</tr>
<tr>
<td><strong>Ollama</strong></td>
<td>Local LLM inference (mistral-nemo, llama3.2, phi)</td>
<td>11434</td>
<td align="center"><code>FREE</code></td>
</tr>
<tr>
<td><strong>ChromaDB</strong></td>
<td>Vector store for codebase memory and RAG</td>
<td>local</td>
<td align="center"><code>FREE</code></td>
</tr>
<tr>
<td><strong>PyTorch</strong></td>
<td>GPU-optimized for your hardware</td>
<td>-</td>
<td align="center"><code>FREE</code></td>
</tr>
<tr>
<td><strong>Foundry Local</strong></td>
<td>ONNX-optimized inference (optional)</td>
<td>5272</td>
<td align="center"><code>FREE</code></td>
</tr>
<tr>
<td><strong>GitHub Runner</strong></td>
<td>Self-hosted Actions runner with AI access</td>
<td>-</td>
<td align="center"><code>FREE</code></td>
</tr>
<tr>
<td><strong>Dashboard</strong></td>
<td>Real-time monitoring and task management</td>
<td>8080</td>
<td align="center"><code>FREE</code></td>
</tr>
</table>

---

## First-Time Setup

After installation, configure these components for optimal performance.

### GPU Configuration

SLATE auto-detects your GPU, but you can manually configure:

```bash
# Detect hardware and see recommendations
python slate/slate_hardware_optimizer.py

# Apply optimizations for your GPU
python slate/slate_hardware_optimizer.py --optimize

# Install optimal PyTorch for your GPU architecture
python slate/slate_hardware_optimizer.py --install-pytorch
```

**Dual-GPU Setup:**

```bash
# Check dual-GPU status
python slate/slate_gpu_manager.py --status

# Enable load balancing
python slate/slate_gpu_manager.py --enable-balance

# Test both GPUs
python slate/slate_gpu_manager.py --test
```

**Environment variables for GPU control:**

```bash
# Force specific GPU
export CUDA_VISIBLE_DEVICES=0

# Use multiple GPUs
export CUDA_VISIBLE_DEVICES=0,1

# Set memory fraction
export SLATE_GPU_MEMORY_FRACTION=0.9
```

### Ollama Models

Install and configure local LLM models:

**Windows:**
```bash
winget install Ollama.Ollama
```

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**macOS:**
```bash
brew install ollama
```

**Pull recommended models:**

```bash
# Primary model (7B, fast, best for code)
ollama pull mistral-nemo

# Lightweight model (2.7B, very fast)
ollama pull phi

# Code-specialized model
ollama pull codellama

# General purpose
ollama pull llama3.2
```

**Verify Ollama:**

```bash
# Check service is running
curl http://127.0.0.1:11434/api/tags

# Test inference
curl http://127.0.0.1:11434/api/generate -d '{"model":"mistral-nemo","prompt":"Hello!","stream":false}'
```

### Claude Code Integration

SLATE is distributed as a Claude Code plugin with commands, skills, and MCP tools.

**For Local Development (this repo):**

```bash
# Just cd into the workspace - plugin auto-loads
cd /path/to/S.L.A.T.E
claude  # Plugin loads automatically at project scope
```

**For External Users (install from GitHub):**

```bash
# Add marketplace and install
/plugin marketplace add SynchronizedLivingArchitecture/S.L.A.T.E
/plugin install slate@slate-marketplace

# Enable plugin
/plugin enable slate@slate-marketplace --scope user
```

**Configure MCP Server (optional):**

Add to `~/.claude/config.json`:

```json
{
  "mcpServers": {
    "slate": {
      "command": "<workspace>\\.venv\\Scripts\\python.exe",
      "args": ["<workspace>\\slate\\mcp_server.py"],
      "env": {
        "SLATE_WORKSPACE": "<workspace>",
        "PYTHONPATH": "<workspace>"
      }
    }
  }
}
```

**Validate Claude Code configuration:**

```bash
python slate/claude_code_manager.py --validate
python slate/claude_code_manager.py --test-mcp slate
```

### Multi-Runner Setup

For parallel task execution with multiple GitHub Actions runners:

```bash
# Check current runner status
python slate/slate_runner_manager.py --status

# Auto-configure runner with GPU labels
python slate/slate_runner_manager.py --setup

# Register additional runner (multi-runner mode)
python slate/slate_multi_runner.py --add-runner

# View all runners
python slate/slate_multi_runner.py --list
```

**Runner labels are auto-detected:**
- `self-hosted` - All runners
- `slate` - SLATE-configured runner
- `gpu`, `cuda` - GPU-enabled runners
- `blackwell`, `ada`, `ampere` - Architecture-specific
- `multi-gpu` - Dual-GPU configurations

---

## Verifying Installation

Run these commands to confirm everything is working:

### Quick Status Check

```bash
python slate/slate_status.py --quick
```

Expected output:
```
SLATE Status
============
Version: 2.5.0
Python: 3.11.x
GPU: NVIDIA RTX xxxx (detected)
Ollama: Connected
Status: Ready
```

### Full Integration Check

```bash
python slate/slate_runtime.py --check-all
```

This verifies:
- Ollama connection and models
- Foundry Local (if installed)
- GPU detection and CUDA
- ChromaDB vector store
- Task queue system
- File locks
- Configuration files
- Workflow system
- Dashboard server
- AI Toolkit

### Dashboard Test

```bash
python agents/slate_dashboard_server.py
```

Open your browser to: **http://127.0.0.1:8080**

You should see the SLATE dashboard with:
- System status panel
- Task queue visualization
- GPU utilization graphs
- AI backend status

### AI Backend Test

```bash
# Check all backends
python slate/unified_ai_backend.py --status

# Test generation
python slate/unified_ai_backend.py --generate "Write hello world in Python"
```

### Kubernetes Health Check (if using K8s)

```bash
python slate/slate_k8s_deploy.py --status
python slate/slate_k8s_deploy.py --health
```

---

## Your First Task

### Using the Task Queue

Tasks are managed in `current_tasks.json`. Here is how to create and manage tasks:

**1. Create a task manually:**

```json
{
  "tasks": [
    {
      "id": "task_001",
      "title": "Fix login bug",
      "description": "Users can't login with special characters in password",
      "status": "pending",
      "assigned_to": "workflow",
      "priority": 2
    }
  ]
}
```

**2. Create a task via Python API:**

```python
from slate import create_task, get_tasks

# Create a new task
task = create_task(
    title="Implement dark mode",
    description="Add dark mode toggle to settings page",
    priority=3
)
print(f"Created task: {task.id}")

# List all tasks
tasks = get_tasks()
for t in tasks:
    print(f"- [{t.status}] {t.title}")
```

**3. Create a task via CLI:**

```bash
# Using the task creation utility
python -c "
from slate import create_task
task = create_task(
    title='Add unit tests',
    description='Create tests for authentication module',
    priority=2
)
print(f'Created: {task.id}')
"
```

### Using Claude Code Commands

With the SLATE plugin loaded, use slash commands:

```
/slate-status              # Check system status
/slate-workflow            # View and manage task queue
/slate-gpu                 # Check GPU utilization
/slate-spec-kit analyze    # Run AI analysis on specs
```

### Using MCP Tools

MCP tools are available in Claude Code sessions:

```
# Check status
slate_status

# Create a task
slate_workflow --action create --title "My task" --priority 2

# Run AI task
slate_ai --task "Review this code for bugs"
```

### Example: Code Review Task

Here is a complete example of creating and executing a code review task:

```python
from slate import create_task, get_task_status
from slate.unified_ai_backend import UnifiedBackend

# 1. Create the task
task = create_task(
    title="Review authentication module",
    description="Check for security issues in auth.py",
    priority=1,
    task_type="code_review"
)

# 2. The task is automatically routed to Ollama (FREE)
backend = UnifiedBackend()
result = backend.generate(
    prompt=f"Review this code for security issues:\n{open('auth.py').read()}",
    task_type="code_review"
)

# 3. View the result
print(result)
```

### Example: AI-Assisted Bug Fix

```python
from slate.unified_ai_backend import UnifiedBackend

backend = UnifiedBackend()

# Describe the bug and get AI assistance
response = backend.generate(
    prompt="""
    Bug: Login fails when password contains special characters like & or <

    Current code:
    def validate_password(password):
        return password == stored_password

    Please provide a fix that properly handles special characters.
    """,
    task_type="bug_fix"
)

print(response)
```

---

## Quick Reference Commands

| Task | Command |
|:-----|:--------|
| System status | `python slate/slate_status.py --quick` |
| Full integration check | `python slate/slate_runtime.py --check-all` |
| Start dashboard | `python agents/slate_dashboard_server.py` |
| Hardware detection | `python slate/slate_hardware_optimizer.py` |
| GPU optimization | `python slate/slate_hardware_optimizer.py --optimize` |
| AI backend status | `python slate/unified_ai_backend.py --status` |
| Workflow health | `python slate/slate_workflow_manager.py --status` |
| Runner status | `python slate/slate_runner_manager.py --status` |
| K8s status | `python slate/slate_k8s_deploy.py --status` |
| Run tests | `python -m pytest tests/ -v` |

---

## Troubleshooting

### Ollama Not Connecting

```bash
# Check if Ollama is running
curl http://127.0.0.1:11434/api/tags

# Start Ollama service (if not running)
ollama serve
```

### GPU Not Detected

```bash
# Check CUDA installation
nvidia-smi

# Verify PyTorch CUDA
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"

# Reinstall PyTorch with CUDA
pip install torch --index-url https://download.pytorch.org/whl/cu124
```

### Import Errors

```bash
# Ensure virtual environment is activated
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS

# Reinstall dependencies
pip install -r requirements.txt
```

### Dashboard Not Starting

```bash
# Check if port is in use
netstat -ano | findstr :8080  # Windows
lsof -i :8080  # Linux/macOS

# Use different port
python agents/slate_dashboard_server.py --port 9000
```

For more troubleshooting, see [Troubleshooting](Troubleshooting).

---

## Next Steps

- [Learn about the Architecture](Architecture) - System design and components
- [Configure AI Backends](AI-Backends) - Ollama, Foundry Local, and routing
- [Explore CLI Commands](CLI-Reference) - Full command reference
- [Configuration Guide](Configuration) - Customize your setup
- [Kubernetes Deployment](Architecture#kubernetes--container-architecture) - Production deployment
- [Contributor Guide](Contributor-Guide) - Help improve SLATE

---

## Additional Resources

| Resource | Description |
|:---------|:------------|
| [GitHub Repository](https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E) | Source code and issues |
| [Specifications](Specifications) | Design specs and architecture decisions |
| [API Reference](API-Reference) | Python API documentation |
| [Development Guide](Development) | Contributing and extending SLATE |
