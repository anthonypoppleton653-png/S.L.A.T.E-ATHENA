# CLI Reference
<!-- Modified: 2026-02-08T23:00:00Z | Author: Claude Opus 4.5 | Change: Comprehensive CLI documentation with all commands -->

Complete reference for SLATE command-line tools.

## Quick Reference

<table>
<tr>
<th>Category</th>
<th>Command</th>
<th>Description</th>
</tr>
<tr>
<td rowspan="3"><strong>System</strong></td>
<td><code>slate_status.py</code></td>
<td>System status check</td>
</tr>
<tr>
<td><code>slate_runtime.py</code></td>
<td>Integration verification</td>
</tr>
<tr>
<td><code>slate_benchmark.py</code></td>
<td>Performance testing</td>
</tr>
<tr>
<td rowspan="2"><strong>Hardware</strong></td>
<td><code>slate_hardware_optimizer.py</code></td>
<td>Hardware detection/optimization</td>
</tr>
<tr>
<td><code>slate_gpu_manager.py</code></td>
<td>Dual-GPU load balancing</td>
</tr>
<tr>
<td rowspan="3"><strong>AI</strong></td>
<td><code>unified_ai_backend.py</code></td>
<td>AI backend management</td>
</tr>
<tr>
<td><code>foundry_local.py</code></td>
<td>Foundry + Ollama client</td>
</tr>
<tr>
<td><code>slate_ai_orchestrator.py</code></td>
<td>AI orchestration and analysis</td>
</tr>
<tr>
<td rowspan="4"><strong>Workflow</strong></td>
<td><code>slate_orchestrator.py</code></td>
<td>Service lifecycle</td>
</tr>
<tr>
<td><code>slate_workflow_manager.py</code></td>
<td>Task queue management</td>
</tr>
<tr>
<td><code>slate_workflow_coordinator.py</code></td>
<td>Workflow scheduling</td>
</tr>
<tr>
<td><code>slate_multi_runner.py</code></td>
<td>Multi-runner coordination</td>
</tr>
<tr>
<td rowspan="3"><strong>Kubernetes</strong></td>
<td><code>slate_k8s_deploy.py</code></td>
<td>K8s cluster deploy, status, health</td>
</tr>
<tr>
<td><code>docker build</code></td>
<td>Build release/dev/CPU images</td>
</tr>
<tr>
<td><code>k8s/deploy.ps1</code></td>
<td>PowerShell deploy wrapper</td>
</tr>
<tr>
<td rowspan="3"><strong>Training</strong></td>
<td><code>slate_training_pipeline.py</code></td>
<td>Secure AI training pipeline</td>
</tr>
<tr>
<td><code>slate_ai_scheduler.py</code></td>
<td>AI task scheduling</td>
</tr>
<tr>
<td><code>slate_model_trainer.py</code></td>
<td>Custom model training</td>
</tr>
<tr>
<td rowspan="2"><strong>Spec-Kit</strong></td>
<td><code>slate_spec_kit.py</code></td>
<td>Specification processing and wiki</td>
</tr>
<tr>
<td><code>slate_project_board.py</code></td>
<td>GitHub Project boards</td>
</tr>
<tr>
<td rowspan="2"><strong>Claude Code</strong></td>
<td><code>claude_code_manager.py</code></td>
<td>Claude Code integration</td>
</tr>
<tr>
<td><code>claude_code_validator.py</code></td>
<td>Configuration validation</td>
</tr>
<tr>
<td rowspan="2"><strong>Vendor SDKs</strong></td>
<td><code>vendor_integration.py</code></td>
<td>Vendor SDK status</td>
</tr>
<tr>
<td><code>slate_copilot_sdk.py</code></td>
<td>GitHub Copilot integration</td>
</tr>
</table>

---

## System Commands

### slate_status.py

Check overall system status.

```bash
# Quick status
python slate/slate_status.py --quick

# Full status with details
python slate/slate_status.py

# Task summary
python slate/slate_status.py --tasks

# JSON output
python slate/slate_status.py --json
```

**Output Example:**
```
SLATE Status
============
Version: 2.5.0
Python: 3.11.9
Platform: Windows 11

Hardware:
  GPU 0: NVIDIA RTX xxxx (xGB)  # Auto-detected
  RAM: xxGB

Backends:
  Ollama: Connected (mistral-nemo)
  Foundry: Available

Tasks:
  Pending: 3
  In Progress: 1
  Completed: 24

Status: Ready
```

*Note: Output reflects your actual hardware configuration.*

### slate_runtime.py

Verify all integrations.

```bash
# Check all integrations
python slate/slate_runtime.py --check-all

# Check specific integration
python slate/slate_runtime.py --check ollama
python slate/slate_runtime.py --check gpu
python slate/slate_runtime.py --check chromadb

# JSON output
python slate/slate_runtime.py --check-all --json
```

**Integrations Checked:**
1. Ollama connection
2. Foundry Local
3. GPU detection
4. ChromaDB vector store
5. Task queue
6. File locks
7. Configuration files
8. Agent system
9. Dashboard server
10. AI Toolkit

---

## Orchestrator Commands

### slate_orchestrator.py

Manages the complete SLATE system lifecycle with dev/prod modes.

```bash
# Start all services (auto-detect mode)
python slate/slate_orchestrator.py start

# Start in development mode (hot-reload)
python slate/slate_orchestrator.py start --mode dev

# Start in production mode (static)
python slate/slate_orchestrator.py start --mode prod

# Stop all services
python slate/slate_orchestrator.py stop

# Show service status
python slate/slate_orchestrator.py status

# Restart all services
python slate/slate_orchestrator.py restart
```

**Modes:**
| Mode | Features |
|------|----------|
| `dev` | Hot-reload via watchfiles, WebSocket push to dashboard |
| `prod` | Static process supervision, Docker/systemd-bound |

**Services Managed:**
- Dashboard server (FastAPI on port 8080)
- GitHub Actions runner (self-hosted)
- Workflow manager (task lifecycle)
- System health monitoring
- File watcher (dev mode only)

---

## Hardware Commands

### slate_hardware_optimizer.py

Detect and optimize for your hardware.

```bash
# Detect hardware
python slate/slate_hardware_optimizer.py

# Install optimal PyTorch
python slate/slate_hardware_optimizer.py --install-pytorch

# Apply runtime optimizations
python slate/slate_hardware_optimizer.py --optimize

# Detailed hardware report
python slate/slate_hardware_optimizer.py --verbose
```

**Detection Output:**
```
Hardware Detection
==================
GPU Architecture: [Auto-detected]
GPU Count: [Your GPU count]
Total VRAM: [Your VRAM]
CUDA Version: [Your version]
cuDNN: [Your version]

Recommendations:
  - Enable TF32: [Based on GPU]
  - Enable BF16: [Based on GPU]
  - Flash Attention: [Based on GPU]
  - CUDA Graphs: [Based on GPU]

Apply with: --optimize
```

*Note: SLATE auto-detects your hardware and provides tailored recommendations.*

### slate_gpu_manager.py

Manage dual-GPU load balancing for Ollama.

```bash
# GPU status overview
python slate/slate_gpu_manager.py --status

# Balance models across GPUs
python slate/slate_gpu_manager.py --balance

# Configure Ollama for dual-GPU
python slate/slate_gpu_manager.py --configure

# Preload models to assigned GPUs
python slate/slate_gpu_manager.py --preload

# JSON output
python slate/slate_gpu_manager.py --json
```

**GPU Layout:**
```
GPU 0 (Primary):   slate-coder, slate-planner — heavy inference
GPU 1 (Secondary): slate-fast, nomic-embed-text — quick tasks + embeddings
```

---

## Benchmark Commands

### slate_benchmark.py

Run performance benchmarks.

```bash
# Full benchmark suite
python slate/slate_benchmark.py

# Quick benchmark
python slate/slate_benchmark.py --quick

# CPU only
python slate/slate_benchmark.py --cpu-only

# GPU only
python slate/slate_benchmark.py --gpu-only

# Save results
python slate/slate_benchmark.py --output results.json
```

**Benchmark Output:**
```
SLATE Benchmark
===============
CPU Benchmark:
  Single-threaded: 1,245 ops/sec
  Multi-threaded: 8,920 ops/sec

GPU Benchmark:
  FP32: 12.4 TFLOPS
  FP16: 24.8 TFLOPS
  Memory Bandwidth: 672 GB/s

LLM Benchmark:
  Ollama (mistral-nemo):
    Tokens/sec: 48.5
    First token: 120ms
    Context: 8192 tokens

Overall Score: 8,450 points
```

---

## AI Backend Commands

### unified_ai_backend.py

Manage AI backends.

```bash
# Check all backend status
python slate/unified_ai_backend.py --status

# Test specific backend
python slate/unified_ai_backend.py --test ollama
python slate/unified_ai_backend.py --test foundry

# Generate with auto-routing
python slate/unified_ai_backend.py --generate "Write hello world in Python"

# Force specific backend
python slate/unified_ai_backend.py --generate "..." --backend ollama
```

### foundry_local.py

Foundry Local specific commands.

```bash
# Check Foundry status
python slate/foundry_local.py --check

# List available models
python slate/foundry_local.py --models

# Generate text
python slate/foundry_local.py --generate "Explain REST APIs"

# Use specific model
python slate/foundry_local.py --generate "..." --model phi-3.5-mini
```

---

## AI Orchestrator Commands

### slate_ai_orchestrator.py

Central orchestrator for all local AI operations.

```bash
# Show orchestrator status
python slate/slate_ai_orchestrator.py --status

# Warmup AI models
python slate/slate_ai_orchestrator.py --warmup

# Analyze full codebase
python slate/slate_ai_orchestrator.py --analyze-codebase

# Analyze recently changed files
python slate/slate_ai_orchestrator.py --analyze-recent

# Update documentation with AI
python slate/slate_ai_orchestrator.py --update-docs

# Monitor GitHub integrations
python slate/slate_ai_orchestrator.py --monitor-github

# Collect training data
python slate/slate_ai_orchestrator.py --collect-training

# Train custom model
python slate/slate_ai_orchestrator.py --train

# Full analysis (all steps)
python slate/slate_ai_orchestrator.py --full

# JSON output
python slate/slate_ai_orchestrator.py --analyze-codebase --json
```

**Capabilities:**
| Feature | Schedule | Description |
|---------|----------|-------------|
| Quick Analysis | Every 4 hours | Analyze recently changed files |
| Full Analysis | Daily 2am | Complete codebase analysis |
| Documentation | Daily | Auto-generate/update docs |
| GitHub Monitor | Daily | Analyze workflows and integrations |
| Model Training | Weekly Sunday | Train custom SLATE model |

---

## AI Scheduler Commands

### slate_ai_scheduler.py

Intelligently schedule AI tasks across dual GPUs.

```bash
# Show scheduler status
python slate/slate_ai_scheduler.py --status

# View task queue
python slate/slate_ai_scheduler.py --queue

# Add task to queue
python slate/slate_ai_scheduler.py --add "code_review:Review recent changes"
python slate/slate_ai_scheduler.py --add "analysis:Investigate performance issue"

# Generate optimal schedule
python slate/slate_ai_scheduler.py --schedule

# Run scheduled tasks
python slate/slate_ai_scheduler.py --run
python slate/slate_ai_scheduler.py --run --max-tasks 20

# JSON output
python slate/slate_ai_scheduler.py --queue --json
```

**Task Types & Priorities:**
| Task Type | Priority | Preferred GPU |
|-----------|----------|---------------|
| `training` | 1 | GPU 0 |
| `embedding` | 2 | GPU 1 |
| `code_review` | 3 | GPU 0 |
| `code_generation` | 4 | GPU 0 |
| `analysis` | 5 | GPU 0 |
| `planning` | 6 | GPU 0 |
| `documentation` | 7 | GPU 1 |
| `classification` | 8 | GPU 1 |
| `summarization` | 9 | GPU 1 |
| `quick` | 10 | GPU 1 |
| `general` | 11 | Either |

---

## Training Pipeline Commands

### slate_training_pipeline.py

Secure AI training pipeline with secret filtering.

```bash
# Collect training data from git repository
python slate/slate_training_pipeline.py --collect

# Validate training data is secret-free
python slate/slate_training_pipeline.py --validate

# Prepare Modelfile for training
python slate/slate_training_pipeline.py --prepare

# Train custom model
python slate/slate_training_pipeline.py --train

# Train with specific base model
python slate/slate_training_pipeline.py --train --base-model mistral-nemo

# Show pipeline status
python slate/slate_training_pipeline.py --status

# JSON output
python slate/slate_training_pipeline.py --collect --json
```

**Security Protocol:**
| Protection | Description |
|------------|-------------|
| Secret Filtering | API keys, tokens, passwords, credentials are redacted |
| PII Scanner | Email, phone, SSN, addresses are filtered |
| File Exclusion | .env, .pem, credentials.json are excluded |
| Commit Sanitization | Author emails are redacted (except known safe domains) |
| Local Only | Trained models are NEVER distributed |

---

## Workflow Commands

### slate_workflow_manager.py

Task lifecycle management with automatic cleanup.

```bash
# Show workflow status
python slate/slate_workflow_manager.py --status

# Analyze task state (JSON output)
python slate/slate_workflow_manager.py --analyze

# Clean up stale/test/deprecated tasks
python slate/slate_workflow_manager.py --cleanup

# Dry run cleanup (show what would be cleaned)
python slate/slate_workflow_manager.py --cleanup --dry-run

# Check if new tasks can be accepted
python slate/slate_workflow_manager.py --enforce

# JSON output
python slate/slate_workflow_manager.py --status --json
```

**Automatic Rules:**
| Rule | Threshold | Action |
|------|-----------|--------|
| Stale | in-progress > 4h | Auto-reset to pending |
| Abandoned | pending > 24h | Flagged for review |
| Duplicates | Same title | Auto-archived |
| Max concurrent | 5 tasks | Block new tasks |

### slate_workflow_coordinator.py

Coordinate AI-powered GitHub Actions workflows.

```bash
# Show coordinator status
python slate/slate_workflow_coordinator.py --status

# Generate execution plan
python slate/slate_workflow_coordinator.py --plan

# Dispatch scheduled workflows
python slate/slate_workflow_coordinator.py --dispatch

# Dry run dispatch
python slate/slate_workflow_coordinator.py --dispatch --dry-run

# Analyze workflow efficiency
python slate/slate_workflow_coordinator.py --optimize

# JSON output
python slate/slate_workflow_coordinator.py --plan --json
```

**Optimal Workflow Sequence:**
```
Phase 1: Training     -> ai-training.yml (model updates first)
Phase 2: Maintenance  -> ai-maintenance.yml, fork-intelligence.yml (parallel)
Phase 3: Agentic      -> agentic.yml (task execution with updated models)
Phase 4: Validation   -> ci.yml, nightly.yml (parallel)
Phase 5: Services     -> service-management.yml (always last)
```

---

## Multi-Runner Commands

### slate_multi_runner.py

Coordinate multiple parallel GitHub Actions runners.

```bash
# Initialize runner configuration
python slate/slate_multi_runner.py --init

# Use minimal 2-runner config
python slate/slate_multi_runner.py --init --minimal

# Show runner status
python slate/slate_multi_runner.py --status

# Scale to target runner count (max 50)
python slate/slate_multi_runner.py --scale 10

# Assign task to runner
python slate/slate_multi_runner.py --assign "task-123"

# Mark runner task complete
python slate/slate_multi_runner.py --complete "runner-001"

# JSON output
python slate/slate_multi_runner.py --json
```

**Status Output:**
```
SLATE Multi-Runner Status
==========================
Total Runners: 8
  Running: 3
  Idle:    5
  Error:   0
Max Parallel: 8

GPU Distribution:
  GPU 0: 4 runners
  GPU 1: 4 runners

Runners:
  ID           Name                      Profile      GPU   Status
  ------------ ------------------------- ------------ ----- --------
  runner-001   slate-gpu-primary-01      gpu_heavy    0     running
  runner-002   slate-gpu-primary-02      gpu_heavy    0     idle
  ...
```

### slate_runner_manager.py

Auto-detect and configure GitHub Actions runners.

```bash
# Detect runner configuration
python slate/slate_runner_manager.py --detect

# Auto-setup runner for SLATE
python slate/slate_runner_manager.py --setup

# Force reconfiguration
python slate/slate_runner_manager.py --setup --force

# Show runner status
python slate/slate_runner_manager.py --status

# Dispatch a workflow
python slate/slate_runner_manager.py --dispatch "ci.yml"

# Dispatch agentic AI workflow
python slate/slate_runner_manager.py --agentic autonomous
python slate/slate_runner_manager.py --agentic single-task --max-tasks 5
python slate/slate_runner_manager.py --agentic build-models

# JSON output
python slate/slate_runner_manager.py --status --json
```

**Agentic Modes:**
| Mode | Description |
|------|-------------|
| `autonomous` | Full autonomous task execution |
| `single-task` | Execute single task and stop |
| `inference-bench` | Run inference benchmarks |
| `discover` | Discover and queue new tasks |
| `health-check` | Run system health checks |
| `build-models` | Build custom AI models |

---

## Kubernetes & Containers

### slate_k8s_deploy.py

Manage Kubernetes deployments for the SLATE local cloud.

```bash
# Cluster status overview
python slate/slate_k8s_deploy.py --status

# Deploy all manifests (auto-detect Helm or Kustomize)
python slate/slate_k8s_deploy.py --deploy

# Deploy with Kustomize
python slate/slate_k8s_deploy.py --deploy-kustomize

# Deploy with Helm
python slate/slate_k8s_deploy.py --deploy-helm

# Health check all pods and deployments
python slate/slate_k8s_deploy.py --health

# View logs for a specific component
python slate/slate_k8s_deploy.py --logs slate-core
python slate/slate_k8s_deploy.py --logs ollama
python slate/slate_k8s_deploy.py --logs chromadb

# Port-forward all SLATE services to localhost
python slate/slate_k8s_deploy.py --port-forward

# Port-forward in background (non-blocking)
python slate/slate_k8s_deploy.py --port-forward --background

# Preload SLATE models into K8s Ollama
python slate/slate_k8s_deploy.py --preload-models

# Remove all SLATE resources from cluster
python slate/slate_k8s_deploy.py --teardown
```

### Docker Commands

```bash
# Build release image (CUDA 12.8)
docker build -t slate:local .

# Build CPU-only image
docker build -f Dockerfile.cpu -t slate:cpu .

# Build dev image
docker build -f Dockerfile.dev -t slate-dev:local .

# Docker Compose
docker-compose up -d                         # GPU production
docker-compose -f docker-compose.dev.yml up  # Dev mode
docker-compose -f docker-compose.prod.yml up -d  # Prod
```

### K8s Component Names

| Component | Description |
|-----------|-------------|
| `slate-core` | Core SDK + Dashboard |
| `ollama` | LLM inference (GPU) |
| `chromadb` | Vector store |
| `slate-agent-router` | Agent task routing |
| `slate-autonomous-loop` | Autonomous execution |
| `slate-copilot-bridge` | Copilot integration bridge |
| `slate-workflow-manager` | Task lifecycle |

### K8s Port Forwards

| Service | Local Port | K8s Service |
|---------|------------|-------------|
| Dashboard | 8080 | slate-dashboard-svc |
| Agent Router | 8081 | slate-agent-router-svc |
| Autonomous | 8082 | slate-autonomous-svc |
| Bridge | 8083 | slate-copilot-bridge-svc |
| Workflow | 8084 | slate-workflow-svc |
| Instructions | 8085 | slate-instruction-controller-svc |
| Ollama | 11434 | ollama-svc |
| ChromaDB | 8000 | chromadb-svc |
| Metrics | 9090 | slate-metrics-svc |

---

## Spec-Kit Commands

### slate_spec_kit.py

Process specifications and generate wiki documentation.

```bash
# Full processing (parse, analyze, generate wiki)
python slate/slate_spec_kit.py --process-all --wiki --analyze

# Generate wiki pages only (no AI analysis)
python slate/slate_spec_kit.py --wiki

# Run AI analysis only
python slate/slate_spec_kit.py --analyze

# Show spec-kit status
python slate/slate_spec_kit.py --status

# List all specifications
python slate/slate_spec_kit.py --list

# Brief output (spec names only)
python slate/slate_spec_kit.py --list --brief

# Show development roadmap from specs
python slate/slate_spec_kit.py --roadmap

# Process a specific spec
python slate/slate_spec_kit.py --spec 006-natural-theme-system

# JSON output
python slate/slate_spec_kit.py --status --json
```

### slate_project_board.py

Manage GitHub Project boards.

```bash
# Check all project boards status
python slate/slate_project_board.py --status

# Update all boards from current_tasks.json
python slate/slate_project_board.py --update-all

# Sync KANBAN to local tasks
python slate/slate_project_board.py --sync

# Push pending tasks to KANBAN
python slate/slate_project_board.py --push
```

---

## Claude Code Commands

### claude_code_manager.py

Manage Claude Code configuration and integration.

```bash
# Show Claude Code integration status
python slate/claude_code_manager.py --status

# Validate configuration
python slate/claude_code_manager.py --validate

# Generate validation report
python slate/claude_code_manager.py --report

# Test an MCP server
python slate/claude_code_manager.py --test-mcp slate

# Add a permission rule
python slate/claude_code_manager.py --add-permission "Bash(python *)"
python slate/claude_code_manager.py --add-permission "Write(*.py)" --permission-type deny

# Show recommended Agent SDK options
python slate/claude_code_manager.py --agent-options

# JSON output
python slate/claude_code_manager.py --status --json
```

### claude_code_validator.py

Validate Claude Code settings.

```bash
# Run all validation checks
python slate/claude_code_validator.py --all

# Check specific component
python slate/claude_code_validator.py --check settings
python slate/claude_code_validator.py --check mcp
python slate/claude_code_validator.py --check permissions
```

---

## Vendor SDK Commands

### vendor_integration.py

Check status of all vendor SDK integrations.

```bash
# Full vendor SDK status
python slate/vendor_integration.py

# Run integration tests
python slate/vendor_integration.py --test

# JSON output
python slate/vendor_integration.py --json
```

**Vendors Tracked:**
| Vendor | Description |
|--------|-------------|
| openai-agents-python | Agent/Tool/Guardrail abstractions |
| semantic-kernel | LLM orchestration and skills |
| autogen | Multi-agent conversation framework |
| copilot-sdk | GitHub Copilot tool definitions |
| spec-kit | Specification-driven development |

### slate_copilot_sdk.py

GitHub Copilot SDK integration.

```bash
# Start SLATE Copilot session (interactive)
python slate/slate_copilot_sdk.py

# Plugin status (no Copilot CLI needed)
python slate/slate_copilot_sdk.py --status

# Execute tool standalone
python slate/slate_copilot_sdk.py --tool slate_status

# Run as persistent agent server
python slate/slate_copilot_sdk.py --server

# Verify full SDK integration
python slate/slate_copilot_sdk.py --verify
```

---

## Dashboard Commands

### Start Dashboard

```bash
# Start on default port (8080)
python agents/slate_dashboard_server.py

# Custom port
python agents/slate_dashboard_server.py --port 9000

# Debug mode
python agents/slate_dashboard_server.py --debug
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SLATE_OLLAMA_HOST` | Ollama host | 127.0.0.1 |
| `SLATE_OLLAMA_PORT` | Ollama port | 11434 |
| `SLATE_DASHBOARD_PORT` | Dashboard port | 8080 |
| `SLATE_LOG_LEVEL` | Log verbosity | INFO |
| `SLATE_GPU_DEVICE` | Force GPU device | auto |
| `SLATE_K8S` | Enable K8s mode | false |
| `SLATE_DOCKER` | Running in container | 0 |
| `SLATE_MODE` | Runtime mode (dev/prod) | dev |
| `SLATE_WORKSPACE` | Workspace root | auto-detected |
| `SLATE_RUNNER` | Running as GitHub runner | false |
| `SLATE_GPU_COUNT` | Number of GPUs | auto-detected |
| `CUDA_VISIBLE_DEVICES` | CUDA device IDs | 0,1 |
| `COPILOT_CLI_PATH` | Path to Copilot CLI | auto-detected |
| `GITHUB_TOKEN` | GitHub authentication | via gh auth |

---

## Common Patterns

### Health Check Script

```bash
#!/bin/bash
# health_check.sh

echo "Checking SLATE health..."

# Quick status
python slate/slate_status.py --quick

# Check integrations
python slate/slate_runtime.py --check-all

# Test Ollama
curl -s http://127.0.0.1:11434/api/tags > /dev/null && echo "Ollama: OK" || echo "Ollama: FAIL"

echo "Health check complete"
```

### Development Workflow

```bash
# Start development environment
python slate/slate_hardware_optimizer.py --optimize
python slate/slate_orchestrator.py start --mode dev

# Work...

# Stop all services
python slate/slate_orchestrator.py stop
```

### Full AI Analysis Pipeline

```bash
# 1. Warmup models
python slate/slate_ai_orchestrator.py --warmup

# 2. Collect training data
python slate/slate_training_pipeline.py --collect

# 3. Validate data is secret-free
python slate/slate_training_pipeline.py --validate

# 4. Run full codebase analysis
python slate/slate_ai_orchestrator.py --analyze-codebase

# 5. Update documentation
python slate/slate_ai_orchestrator.py --update-docs

# 6. Train custom model (optional)
python slate/slate_training_pipeline.py --train
```

### K8s Deployment Workflow

```bash
# 1. Check prerequisites
python slate/slate_k8s_deploy.py --status

# 2. Deploy SLATE stack
python slate/slate_k8s_deploy.py --deploy

# 3. Health check
python slate/slate_k8s_deploy.py --health

# 4. Set up port forwarding
python slate/slate_k8s_deploy.py --port-forward

# 5. Preload models
python slate/slate_k8s_deploy.py --preload-models

# Access dashboard at http://localhost:8080
```

### Multi-Runner Setup

```bash
# 1. Initialize optimal configuration
python slate/slate_multi_runner.py --init

# 2. Scale to desired capacity
python slate/slate_multi_runner.py --scale 8

# 3. Configure GPU manager
python slate/slate_gpu_manager.py --configure

# 4. Preload models
python slate/slate_gpu_manager.py --preload

# 5. Check status
python slate/slate_multi_runner.py --status
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Configuration error |
| 3 | Connection error |
| 4 | Hardware error |

---

## Next Steps

- [Configuration](Configuration)
- [Troubleshooting](Troubleshooting)
- [Development](Development)
- [Kubernetes Deployment](Kubernetes-Deployment)
