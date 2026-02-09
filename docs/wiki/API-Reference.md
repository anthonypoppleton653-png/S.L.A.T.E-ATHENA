# API Reference

Complete API documentation for SLATE modules, REST endpoints, MCP tools, and SDK integrations.

## Table of Contents

1. [Core Package API](#core-package-api)
2. [Dashboard REST API](#dashboard-rest-api)
3. [MCP Server Tools](#mcp-server-tools)
4. [Schematic SDK API](#schematic-sdk-api)
5. [Interactive Experience API](#interactive-experience-api)
6. [K8s Integration API](#k8s-integration-api)
7. [Vendor SDK Integration](#vendor-sdk-integration)
8. [GPU Management API](#gpu-management-api)
9. [Workflow Management API](#workflow-management-api)
10. [Error Handling](#error-handling)
11. [Authentication](#authentication)

---

## Core Package API

### Package Initialization

```python
import slate

# Package info
print(slate.__version__)  # "2.4.0"
print(slate.__author__)   # "SLATE Team"
```

### Available Exports

```python
from slate import (
    # Status functions
    get_status,
    get_quick_status,

    # Task functions
    get_tasks,
    create_task,
    complete_task,

    # AI functions
    generate,

    # Utilities
    greet,
    fibonacci,
)
```

---

### Status Module

#### get_status()

Get comprehensive system status.

```python
from slate import get_status

status = get_status()
print(status)
```

**Returns:**
```python
{
    "version": "2.4.0",
    "python": "3.11.9",
    "platform": "Windows",
    "hardware": {
        "gpu_count": 2,
        "gpu_names": ["RTX 5070 Ti", "RTX 5070 Ti"],
        "total_vram": "32GB",
        "ram": "64GB"
    },
    "backends": {
        "ollama": {"status": "connected", "model": "mistral-nemo"},
        "foundry": {"status": "available"}
    },
    "tasks": {
        "pending": 3,
        "in_progress": 1,
        "completed": 24
    },
    "status": "ready"
}
```

#### get_quick_status()

Get minimal status check.

```python
from slate import get_quick_status

status = get_quick_status()
# Returns: {"status": "ready", "version": "2.4.0"}
```

---

### Task Module

#### Task Schema

```python
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Task:
    task_id: str
    title: str
    description: str
    status: str  # "pending", "in_progress", "completed", "blocked"
    priority: str  # "low", "medium", "high", "urgent"
    assigned_to: str  # "workflow" or "auto"
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[str] = None
```

#### get_tasks()

Retrieve all tasks from the queue.

```python
from slate import get_tasks

tasks = get_tasks()
for task in tasks:
    print(f"{task['task_id']}: {task['title']} [{task['status']}]")
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| status_filter | str | No | Filter by status ("pending", "in_progress", "completed") |
| assigned_to | str | No | Filter by executor |

**Returns:** List of task dictionaries.

#### create_task()

Create a new task.

```python
from slate import create_task

task = create_task(
    title="Implement login feature",
    description="Add user authentication with JWT",
    priority="high",
    assigned_to="workflow"
)
print(f"Created task: {task['task_id']}")
```

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| title | str | Yes | - | Short task title |
| description | str | Yes | - | Detailed description |
| priority | str | No | "medium" | Priority level |
| assigned_to | str | No | "auto" | Target agent |

**Returns:** Created task dictionary.

#### complete_task()

Mark a task as completed.

```python
from slate import complete_task

result = complete_task(
    task_id="task_001",
    result="Implemented JWT authentication with refresh tokens"
)
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| task_id | str | Yes | Task to complete |
| result | str | No | Completion summary |

---

### AI Module

#### generate()

Generate text using the unified AI backend.

```python
from slate import generate

response = generate(
    prompt="Write a Python function to calculate factorial",
    task_type="code_generation"
)
print(response)
```

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| prompt | str | Yes | - | Input prompt |
| task_type | str | No | "general" | Task type for routing |
| backend | str | No | "auto" | Force specific backend |
| model | str | No | None | Force specific model |
| temperature | float | No | 0.7 | Sampling temperature |
| max_tokens | int | No | 2048 | Maximum tokens |

**Task Types:**
- `code_generation` - Writing new code
- `code_review` - Reviewing existing code
- `test_generation` - Writing tests
- `bug_fix` - Fixing bugs
- `refactoring` - Code refactoring
- `documentation` - Writing docs
- `analysis` - Code analysis
- `general` - General queries

**Returns:** Generated text string.

---

## Dashboard REST API

Base URL: `http://127.0.0.1:8080`

### Health & Status Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/status` | GET | Full system status |
| `/api/orchestrator` | GET | Orchestrator status |
| `/api/runner` | GET | GitHub runner status |
| `/api/services` | GET | All service statuses |
| `/api/integrations` | GET | All integration statuses |

#### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2026-02-08T12:00:00Z",
  "service": "slate-dashboard"
}
```

#### GET /api/status

Get comprehensive system status.

**Response:**
```json
{
  "version": "2.4.0",
  "python": "3.11.9",
  "platform": "Windows",
  "hardware": {
    "gpu_count": 2,
    "gpu_names": ["RTX 5070 Ti", "RTX 5070 Ti"],
    "total_vram": "32GB"
  },
  "backends": {
    "ollama": {"status": "connected", "model": "mistral-nemo"},
    "foundry": {"status": "available"}
  },
  "tasks": {
    "pending": 3,
    "in_progress": 1,
    "completed": 24
  }
}
```

#### GET /api/services

Get all service statuses.

**Response:**
```json
{
  "services": [
    {"id": "dashboard", "name": "Dashboard", "online": true, "port": 8080},
    {"id": "ollama", "name": "Ollama", "online": true, "port": 11434},
    {"id": "foundry", "name": "Foundry Local", "online": false, "port": 5272},
    {"id": "runner", "name": "GitHub Runner", "online": true}
  ]
}
```

---

### Task Management Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/tasks` | GET | List all tasks |
| `/api/tasks` | POST | Create task |
| `/api/tasks/{id}` | PUT | Update task |
| `/api/tasks/{id}` | DELETE | Delete task |

#### GET /api/tasks

List all tasks with statistics.

**Response:**
```json
{
  "tasks": [
    {
      "id": "abc123",
      "title": "Implement feature X",
      "description": "Add new functionality",
      "status": "pending",
      "priority": 3,
      "assigned_to": "workflow",
      "created_at": "2026-02-08T10:00:00Z"
    }
  ],
  "stats": {
    "total": 10,
    "pending": 5,
    "in_progress": 2,
    "completed": 3
  }
}
```

#### POST /api/tasks

Create a new task.

**Request Body:**
```json
{
  "title": "New Task",
  "description": "Task description",
  "priority": 3,
  "assigned_to": "workflow"
}
```

**Response:** `201 Created`
```json
{
  "id": "xyz789",
  "title": "New Task",
  "description": "Task description",
  "status": "pending",
  "priority": 3,
  "assigned_to": "workflow",
  "created_at": "2026-02-08T12:00:00Z",
  "created_by": "dashboard"
}
```

#### PUT /api/tasks/{task_id}

Update an existing task.

**Request Body:**
```json
{
  "status": "in_progress",
  "assigned_to": "workflow"
}
```

**Response:**
```json
{
  "id": "xyz789",
  "title": "New Task",
  "status": "in_progress",
  "updated_at": "2026-02-08T12:30:00Z"
}
```

#### DELETE /api/tasks/{task_id}

Delete a task.

**Response:**
```json
{
  "deleted": "xyz789"
}
```

---

### GitHub Integration Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/workflows` | GET | List recent workflow runs |
| `/api/workflow/{run_id}` | GET | Get workflow run details |
| `/api/workflow-pipeline` | GET | Get workflow pipeline stats |
| `/api/dispatch/{workflow_name}` | POST | Dispatch a workflow |
| `/api/github/prs` | GET | List open pull requests |
| `/api/github/commits` | GET | List recent commits |
| `/api/github/issues` | GET | List open issues |
| `/api/github/releases` | GET | Get latest release |

#### GET /api/workflows

Get recent GitHub workflow runs.

**Response:**
```json
{
  "runs": [
    {
      "name": "CI",
      "status": "completed",
      "conclusion": "success",
      "createdAt": "2026-02-08T10:00:00Z",
      "updatedAt": "2026-02-08T10:05:00Z",
      "databaseId": 12345,
      "headBranch": "main",
      "event": "push"
    }
  ],
  "count": 15
}
```

#### POST /api/dispatch/{workflow_name}

Dispatch a GitHub workflow.

**Request Body (optional):**
```json
{
  "input_name": "input_value"
}
```

**Response:**
```json
{
  "success": true,
  "workflow": "ci.yml"
}
```

---

### System Health Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/system/gpu` | GET | Real-time GPU utilization |
| `/api/system/resources` | GET | CPU, memory, disk usage |
| `/api/system/ollama` | GET | Ollama service and models |

#### GET /api/system/gpu

Get real-time GPU utilization.

**Response:**
```json
{
  "available": true,
  "gpus": [
    {
      "index": 0,
      "name": "NVIDIA GeForce RTX 5070 Ti",
      "gpu_util": 45,
      "memory_util": 60,
      "memory_used": 9600,
      "memory_total": 16384,
      "temperature": 65
    },
    {
      "index": 1,
      "name": "NVIDIA GeForce RTX 5070 Ti",
      "gpu_util": 30,
      "memory_util": 40,
      "memory_used": 6400,
      "memory_total": 16384,
      "temperature": 58
    }
  ]
}
```

#### GET /api/system/resources

Get CPU, memory, disk usage.

**Response:**
```json
{
  "available": true,
  "cpu": {
    "percent": 25.5,
    "cores": 16
  },
  "memory": {
    "percent": 45.2,
    "used_gb": 28.9,
    "total_gb": 64.0
  },
  "disk": {
    "percent": 35.5,
    "free_gb": 500.0,
    "total_gb": 1000.0
  }
}
```

#### GET /api/system/ollama

Get Ollama service status and loaded models.

**Response:**
```json
{
  "available": true,
  "models": [
    {"name": "mistral-nemo:latest", "size": "4.7 GB"},
    {"name": "llama3.2:latest", "size": "3.8 GB"}
  ],
  "loaded": [
    {"name": "mistral-nemo:latest", "vram": "4.8 GB"}
  ]
}
```

---

### SLATE Control Panel Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/slate/run-protocol` | POST | Run guided SLATE protocol |
| `/api/slate/update` | POST | Update from git and check forks |
| `/api/slate/debug` | POST | Run diagnostics |
| `/api/slate/security` | POST | Run security audit |
| `/api/slate/deploy/{action}` | POST | Manage services (start/stop/status) |
| `/api/slate/agents` | POST | Check agent system status |
| `/api/slate/gpu` | POST | GPU management status |
| `/api/slate/benchmark` | POST | Run performance benchmarks |

#### POST /api/slate/run-protocol

Run the guided SLATE protocol: status -> runtime -> workflow -> enforce.

**Response:**
```json
{
  "success": true,
  "steps": [
    {"step": "System Health", "success": true, "output": "..."},
    {"step": "Runtime Integrations", "success": true, "output": "..."},
    {"step": "Workflow Status", "success": true, "output": "..."},
    {"step": "Enforce Completion", "success": true, "output": "..."}
  ]
}
```

#### POST /api/slate/deploy/{action}

Manage SLATE services.

**Path Parameters:**
- `action`: `start`, `stop`, or `status`

**Response:**
```json
{
  "success": true,
  "output": "All services started successfully"
}
```

---

### AI Intelligence Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/slate/ai/recommend` | GET | Get AI recommendation for next action |
| `/api/slate/ai/record` | POST | Record action for pattern learning |
| `/api/slate/ai/summarize` | POST | Get AI summary of action result |
| `/api/slate/ai/recovery` | POST | Get AI-suggested fix for failure |

#### GET /api/slate/ai/recommend

Get AI-powered recommendation for next action.

**Response:**
```json
{
  "recommendation": "Run workflow cleanup to clear 3 stale tasks",
  "recommended_order": ["status", "cleanup", "benchmark"],
  "usage_stats": {
    "total_actions": 150,
    "success_rate": 0.92
  }
}
```

#### POST /api/slate/ai/recovery

Get AI-suggested fix for a failed action.

**Request Body:**
```json
{
  "action": "workflow-cleanup",
  "error": "Failed to acquire lock on current_tasks.json"
}
```

**Response:**
```json
{
  "suggestion": "Try stopping other SLATE processes that may hold the file lock, then retry the cleanup operation.",
  "steps": [
    "Check for other running SLATE processes",
    "Wait 5 seconds for lock release",
    "Retry the cleanup operation"
  ]
}
```

---

### Background Actions Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/slate/background/{action}` | POST | Queue background action |
| `/api/slate/background/history` | GET | Get action history |
| `/api/slate/background/result/{action_id}` | GET | Get specific action result |

**Supported Actions:**
- `status` - System status check
- `runtime` - Runtime integration check
- `update` - Workflow status update
- `benchmark` - Performance benchmark
- `security` - Security audit
- `agents` - Agent system status
- `gpu` - GPU management
- `autonomous-discover` - Autonomous task discovery
- `autonomous-single` - Run single autonomous step
- `workflow-cleanup` - Clean stale tasks
- `workflow-enforce` - Enforce workflow rules
- `health-check` - Full health check

#### POST /api/slate/background/{action}

Queue a SLATE action for background execution.

**Response:**
```json
{
  "id": "status-1707400000",
  "action": "status",
  "status": "queued",
  "message": "Background action 'status' started"
}
```

#### GET /api/slate/background/result/{action_id}

Get the result of a specific background action.

**Response:**
```json
{
  "id": "status-1707400000",
  "action": "status",
  "status": "completed",
  "started_at": "2026-02-08T12:00:00Z",
  "completed_at": "2026-02-08T12:00:05Z",
  "output": "All systems operational",
  "error": null
}
```

---

### Docker & Kubernetes Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/docker/containers` | GET | List Docker containers |
| `/api/docker/images` | GET | List Docker images |
| `/api/docker/action` | POST | Container action (start/stop/restart) |
| `/api/kubernetes/status` | GET | K8s cluster status |
| `/api/kubernetes/health` | GET | K8s health check |

#### GET /api/docker/containers

Get Docker container list.

**Response:**
```json
{
  "available": true,
  "containers": [
    {
      "id": "abc123",
      "name": "slate-dashboard",
      "image": "slate:latest",
      "status": "running",
      "ports": "8080:8080",
      "created": "2026-02-08T10:00:00Z"
    }
  ]
}
```

#### POST /api/docker/action

Perform Docker container action.

**Request Body:**
```json
{
  "container": "slate-dashboard",
  "action": "restart"
}
```

**Response:**
```json
{
  "success": true,
  "output": "slate-dashboard"
}
```

---

### WebSocket API

#### WS /ws

Real-time WebSocket for live updates.

**Connection:**
```javascript
const ws = new WebSocket('ws://127.0.0.1:8080/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data.type, data);
};
```

**Event Types:**
| Event | Description |
|-------|-------------|
| `task_created` | New task created |
| `task_updated` | Task updated |
| `task_deleted` | Task deleted |
| `workflow_dispatched` | Workflow dispatched |
| `slate_protocol` | Protocol run completed |
| `guided_workflow_started` | Guided workflow started |
| `guided_workflow_submitted` | Job submitted |
| `feedback` | Feedback event from Claude layer |
| `schematic_update` | Schematic diagram updated |

---

## MCP Server Tools

SLATE provides 12 core MCP tools for Claude Code integration.

### slate_status

Check the status of all SLATE services and system components.

**Parameters:**
| Parameter | Type | Values | Default | Description |
|-----------|------|--------|---------|-------------|
| format | string | quick, json, full | quick | Output format |

**Example:**
```json
{"format": "json"}
```

### slate_workflow

Manage the SLATE task workflow queue.

**Parameters:**
| Parameter | Type | Values | Default | Description |
|-----------|------|--------|---------|-------------|
| action | string | status, cleanup, enforce | status | Action to perform |

**Actions:**
- `status` - View current queue state
- `cleanup` - Fix stale/abandoned tasks
- `enforce` - Check and enforce workflow rules

### slate_orchestrator

Control the SLATE orchestrator services.

**Parameters:**
| Parameter | Type | Values | Description |
|-----------|------|--------|-------------|
| action | string | start, stop, status | Action to perform (required) |

### slate_runner

Manage the GitHub Actions self-hosted runner.

**Parameters:**
| Parameter | Type | Values | Default | Description |
|-----------|------|--------|---------|-------------|
| action | string | status, setup, dispatch | status | Action to perform |
| workflow | string | - | ci.yml | Workflow file to dispatch |

### slate_ai

Execute AI tasks using SLATE's unified backend.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| task | string | - | The AI task to execute |
| check_status | boolean | false | Check backend status instead |

**Example:**
```json
{"task": "Review this Python function for security issues"}
```

### slate_runtime

Check all SLATE runtime integrations and dependencies.

**Parameters:**
| Parameter | Type | Values | Default | Description |
|-----------|------|--------|---------|-------------|
| format | string | text, json | text | Output format |

### slate_hardware

Detect GPUs and optimize hardware configuration.

**Parameters:**
| Parameter | Type | Values | Default | Description |
|-----------|------|--------|---------|-------------|
| action | string | detect, optimize, install-pytorch | detect | Action to perform |

### slate_benchmark

Run SLATE performance benchmarks (GPU, inference, throughput).

**Parameters:** None

### slate_gpu

Manage dual-GPU load balancing for Ollama LLMs.

**Parameters:**
| Parameter | Type | Values | Default | Description |
|-----------|------|--------|---------|-------------|
| action | string | status, configure, preload | status | Action to perform |

**Actions:**
- `status` - Show GPU/model placement
- `configure` - Set up dual-GPU environment
- `preload` - Warm models on GPUs

### slate_claude_code

Validate and manage Claude Code configuration.

**Parameters:**
| Parameter | Type | Values | Default | Description |
|-----------|------|--------|---------|-------------|
| action | string | validate, report, status, agent-options | status | Action to perform |
| format | string | text, json | text | Output format |

### slate_spec_kit

Process specifications and generate wiki pages.

**Parameters:**
| Parameter | Type | Values | Default | Description |
|-----------|------|--------|---------|-------------|
| action | string | status, process-all, wiki, analyze | status | Action to perform |
| format | string | text, json | text | Output format |

### slate_schematic

Generate circuit-board style system diagrams.

**Parameters:**
| Parameter | Type | Values | Default | Description |
|-----------|------|--------|---------|-------------|
| action | string | from-system, from-tech-tree, components | from-system | Source for diagram |
| output | string | - | docs/assets/slate-schematic.svg | Output file path |
| theme | string | blueprint, dark, light | blueprint | Diagram theme |

---

## Schematic SDK API

The Schematic SDK provides programmatic access to diagram generation.

### REST Endpoints

Base URL: `/api/schematic`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/templates` | GET | List available templates |
| `/template/{template_id}` | GET | Render a template |
| `/system-state` | GET | Generate from current state |
| `/tech-tree` | GET | Generate from tech tree |
| `/live-status` | POST | Generate with live status |
| `/custom` | POST | Create custom schematic |
| `/widget/system` | GET | Get embeddable widget |
| `/widget/compact` | GET | Get compact widget |

### GET /api/schematic/templates

List available schematic templates.

**Response:**
```json
{
  "templates": [
    {"id": "system", "name": "System Architecture", "description": "..."},
    {"id": "inference", "name": "Inference Pipeline", "description": "..."},
    {"id": "cicd", "name": "CI/CD Pipeline", "description": "..."}
  ]
}
```

### GET /api/schematic/template/{template_id}

Render a pre-built schematic template.

**Query Parameters:**
- `format`: `svg`, `base64`, or `json`

**Response (SVG):**
```json
{
  "svg": "<svg ...>...</svg>",
  "title": "System Architecture",
  "width": 900,
  "height": 600,
  "format": "svg"
}
```

**Response (Base64):**
```json
{
  "data_uri": "data:image/svg+xml;base64,...",
  "img_tag": "<img src=\"data:image/svg+xml;base64,...\" alt=\"System Architecture\">",
  "title": "System Architecture"
}
```

### POST /api/schematic/live-status

Generate schematic with live service status.

**Request Body:**
```json
{
  "services": {
    "dashboard": "active",
    "ollama": "active",
    "foundry": "inactive",
    "chromadb": "active",
    "gpu": "active",
    "runner": "pending"
  }
}
```

**Status Values:** `active`, `pending`, `error`, `inactive`

### POST /api/schematic/custom

Create a custom schematic.

**Request Body:**
```json
{
  "title": "My Architecture",
  "width": 900,
  "height": 600,
  "theme": "blueprint",
  "layout": "hierarchical",
  "nodes": [
    {
      "type": "service",
      "id": "api",
      "label": "API Gateway",
      "status": "active",
      "x": 100,
      "y": 100
    }
  ],
  "connections": [
    {
      "id": "c1",
      "from_node": "api",
      "to_node": "db",
      "label": "SQL"
    }
  ]
}
```

**Node Types:** `service`, `ai`, `gpu`, `database`

### WebSocket /api/schematic/ws/live

Real-time schematic updates.

**Client Messages:**
```json
{"type": "request_update", "timestamp": 1707400000}
```
```json
{"type": "request_template", "template_id": "system"}
```

**Server Messages:**
```json
{
  "type": "schematic_update",
  "svg": "<svg>...</svg>",
  "title": "SLATE System Architecture"
}
```

### Python SDK

```python
from slate.schematic_sdk import (
    SchematicEngine,
    SchematicConfig,
    ComponentStatus,
    ServiceNode,
    AINode,
    GPUNode,
    DatabaseNode,
    FlowConnector,
    generate_from_system_state,
    generate_from_tech_tree,
)

# Create engine
config = SchematicConfig(
    title="My Architecture",
    theme="blueprint",
    layout="hierarchical",
    width=900,
    height=600,
)
engine = SchematicEngine(config)

# Add nodes
engine.add_node(ServiceNode(
    id="api",
    label="API Gateway",
    status=ComponentStatus.ACTIVE,
    x=100, y=100
))

engine.add_node(GPUNode(
    id="gpu-cluster",
    label="Dual RTX 5070 Ti",
    status=ComponentStatus.ACTIVE,
    x=300, y=200
))

# Add connections
engine.add_connector(FlowConnector(
    id="c1",
    from_node="api",
    to_node="gpu-cluster",
    label="CUDA"
))

# Render
svg = engine.render_svg()

# Or use convenience functions
svg = generate_from_system_state()
svg = generate_from_tech_tree()
```

---

## Interactive Experience API

The Interactive API provides endpoints for learning, development cycle, and feedback systems.

### Learning Endpoints

Base URL: `/api/interactive`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/paths` | GET | List learning paths |
| `/start` | POST | Start learning session |
| `/progress` | GET | Get learning progress |
| `/current-step` | GET | Get current step |
| `/complete-step` | POST | Complete a step |
| `/achievements` | GET | Get all achievements |
| `/ai-explain` | POST | Get AI explanation |
| `/hints/{step_id}` | GET | Get step hints |

#### GET /api/interactive/paths

List all available learning paths.

**Response:**
```json
{
  "paths": [
    {
      "id": "getting-started",
      "name": "Getting Started with SLATE",
      "description": "Learn the basics",
      "step_count": 10,
      "completed_steps": 3,
      "progress_percent": 30
    }
  ]
}
```

#### GET /api/interactive/progress

Get current learning progress.

**Response:**
```json
{
  "completed_steps": ["step-1", "step-2", "step-3"],
  "achievements": [
    {"id": "first-task", "name": "First Task", "xp": 100}
  ],
  "total_xp": 350,
  "level": 2,
  "streak_days": 5,
  "last_activity": "2026-02-08T10:00:00Z"
}
```

### Development Cycle Endpoints

Base URL: `/api/devcycle`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/state` | GET | Get current cycle state |
| `/transition` | POST | Transition to new stage |
| `/activities/{stage}` | GET | Get stage activities |
| `/activity` | POST | Add new activity |
| `/activity/{id}` | PUT | Update activity |
| `/activity/{id}` | DELETE | Complete activity |
| `/visualization` | GET | Get visualization data |
| `/metrics` | GET | Get cycle metrics |
| `/advance` | POST | Advance to next stage |

**Development Stages:** `plan`, `code`, `test`, `deploy`, `feedback`

#### GET /api/devcycle/state

Get current development cycle state.

**Response:**
```json
{
  "current_stage": "code",
  "stage_progress_percent": 60,
  "cycle_count": 3,
  "activities": {
    "plan": [...],
    "code": [...],
    "test": [...]
  }
}
```

### Feedback Endpoints

Base URL: `/api/feedback`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tool-event` | POST | Record tool execution |
| `/history` | GET | Get tool history |
| `/patterns` | GET | Get usage patterns |
| `/insights` | GET | Get AI insights |
| `/recovery` | POST | Get recovery suggestion |
| `/metrics` | GET | Get feedback metrics |
| `/session/start` | POST | Start tracking session |
| `/session/end` | POST | End session |
| `/session/{id}` | GET | Get session stats |

#### POST /api/feedback/tool-event

Record a tool execution event.

**Request Body:**
```json
{
  "tool_name": "Read",
  "tool_input": {"file_path": "/path/to/file"},
  "tool_output": "file contents...",
  "success": true,
  "duration_ms": 150,
  "session_id": "session-123"
}
```

#### GET /api/feedback/insights

Generate AI-powered insights.

**Response:**
```json
{
  "insights": [
    "Read operations are 95% successful",
    "Average tool execution time: 120ms",
    "Most used tool: Edit (45%)"
  ]
}
```

### GitHub Achievements Endpoints

Base URL: `/api/github`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/achievements` | GET | Get all achievements |
| `/achievements/status` | GET | Get achievement summary |
| `/achievements/refresh` | POST | Refresh from GitHub |
| `/achievements/recommendations` | GET | Get recommendations |

---

## K8s Integration API

### REST Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/k8s/status` | GET | K8s integration status |
| `/api/k8s/services` | GET | List SLATE services |
| `/api/k8s/health/{service_name}` | GET | Check service health |
| `/api/k8s/pod` | GET | Get current pod info |

#### GET /api/k8s/status

Get comprehensive K8s integration status.

**Response:**
```json
{
  "environment": "kubernetes",
  "pod": {
    "name": "slate-dashboard-abc123",
    "namespace": "slate",
    "ip": "10.244.0.15",
    "node": "minikube"
  },
  "summary": {
    "total_services": 9,
    "healthy": 7,
    "degraded": 1,
    "unhealthy": 1,
    "all_required_healthy": true
  },
  "services": {
    "ollama": {
      "status": "healthy",
      "url": "http://ollama-svc:11434",
      "latency_ms": 25.3,
      "metadata": {"models": ["mistral-nemo"]}
    }
  },
  "cluster": {
    "kubectl_version": "v1.29.0",
    "deployments": [...],
    "pods": [...],
    "cronjobs": [...],
    "gpu": {"device_plugin_installed": true, "total_gpus": 2}
  },
  "timestamp": "2026-02-08T12:00:00Z"
}
```

#### GET /api/k8s/health/{service_name}

Check health of a specific SLATE service.

**Path Parameters:**
- `service_name`: `ollama`, `chromadb`, `dashboard`, `agent-router`, `autonomous`, `copilot-bridge`, `workflow`, `instruction-controller`, `metrics`

**Response:**
```json
{
  "name": "ollama",
  "status": "healthy",
  "url": "http://ollama-svc:11434",
  "latency_ms": 25.3,
  "last_check": "2026-02-08T12:00:00Z",
  "error": null,
  "metadata": {"models": ["mistral-nemo", "llama3.2"]}
}
```

### Python SDK

```python
from slate.k8s_integration import get_k8s_integration, SlateK8sIntegration

# Get singleton instance
k8s = get_k8s_integration()

# Check environment
if k8s.is_k8s_environment():
    print("Running in Kubernetes")
    print(k8s.get_pod_info())

# Check all services
health = await k8s.check_all_services()
for name, status in health.items():
    print(f"{name}: {status.status.value}")

# Get full status with cluster info
status = await k8s.get_full_status()

# Cluster operations (via kubectl)
cluster = k8s.get_cluster_status()
deployments = k8s._get_deployments()
pods = k8s._get_pods()
gpu_info = k8s._detect_gpu_plugin()

# Deployment operations
k8s.restart_deployment("slate-dashboard")
k8s.scale_deployment("slate-dashboard", replicas=3)
logs = k8s.get_pod_logs("slate-dashboard-abc123", tail=100)

# ConfigMap reading
data = k8s.read_configmap("slate-instructions")
value = k8s.read_configmap_key("slate-instructions", "active-state.yaml")
```

### K8s Service Definitions

| Service | K8s Service Name | Port | Health Endpoint | Required |
|---------|------------------|------|-----------------|----------|
| Ollama | ollama-svc | 11434 | /api/tags | Yes |
| ChromaDB | chromadb-svc | 8000 | /api/v2/heartbeat | No |
| Dashboard | slate-dashboard-svc | 8080 | /health | Yes |
| Agent Router | slate-agent-router-svc | 8081 | /health | No |
| Autonomous | slate-autonomous-svc | 8082 | /health | No |
| Copilot Bridge | slate-copilot-bridge-svc | 8083 | /health | No |
| Workflow | slate-workflow-svc | 8084 | /health | No |
| Instruction Controller | slate-instruction-controller-svc | 8085 | /health | No |
| Metrics | slate-metrics-svc | 9090 | /metrics | No |

---

## Vendor SDK Integration

SLATE integrates with multiple vendor SDKs for advanced AI orchestration.

### Integration Status API

```python
from slate.vendor_integration import get_full_status, run_integration_tests

# Get full vendor status
status = get_full_status()
print(f"Available: {status['summary']['available']}/{status['summary']['total']}")

for vendor in status['vendors']:
    print(f"  {vendor['name']}: {'OK' if vendor['available'] else 'Not Available'}")

# Run integration tests
results = run_integration_tests()
print(f"Passed: {results['summary']['passed']}/{results['summary']['total']}")
```

### Supported Vendors

| Vendor | Integration File | Description |
|--------|------------------|-------------|
| openai-agents-python | slate/vendor_agents_sdk.py | Agent/Tool/Guardrail abstractions |
| autogen | slate/vendor_autogen_sdk.py | Multi-agent conversation framework |
| semantic-kernel | slate/slate_semantic_kernel.py | LLM orchestration and skills |
| copilot-sdk | slate/copilot_sdk_tools.py | GitHub Copilot tool definitions |
| spec-kit | slate/slate_spec_kit.py | Specification-driven development |

### OpenAI Agents SDK

```python
from slate.vendor_agents_sdk import (
    SDK_AVAILABLE,
    Agent,
    function_tool,
    InputGuardrail,
    Runner,
)

if SDK_AVAILABLE:
    # Create agent with tools
    agent = Agent(
        name="slate-agent",
        instructions="You are a SLATE assistant.",
        tools=[function_tool(my_tool_function)],
    )

    # Add guardrail
    guardrail = InputGuardrail(
        name="safety",
        check=lambda input: "safe" not in input,
    )
```

### Microsoft AutoGen

```python
from slate.vendor_autogen_sdk import (
    SDK_AVAILABLE,
    Agent,
    BaseAgent,
    AgentRuntime,
    ClosureAgent,
)

if SDK_AVAILABLE:
    # Create runtime
    runtime = AgentRuntime()

    # Create closure agent for simple tasks
    agent = ClosureAgent(
        name="task-agent",
        on_message=lambda msg: f"Processed: {msg}"
    )
```

### Microsoft Semantic Kernel

```python
from slate.slate_semantic_kernel import (
    _check_sk_available,
    _check_ollama_available,
)

sk_ok, sk_version = _check_sk_available()
ollama_ok = _check_ollama_available()

if sk_ok and ollama_ok:
    import semantic_kernel as sk

    kernel = sk.Kernel()
    # Add Ollama chat service
    # kernel.add_chat_service(...)
```

---

## GPU Management API

### GPU Manager Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/slate/gpu` | POST | GPU management status |
| `/api/system/gpu` | GET | Real-time GPU utilization |

### Python SDK

```python
from slate.slate_gpu_manager import SlateGPUManager

manager = SlateGPUManager()

# Get status
status = manager.get_status()
print(f"GPUs: {status['gpu_count']}")
print(f"Total VRAM: {status['total_vram_gb']} GB")

# Configure dual-GPU
manager.configure_dual_gpu()

# Preload models
manager.preload_models()

# Get model placement
placement = manager.get_model_placement()
for model, gpu in placement.items():
    print(f"{model} -> GPU {gpu}")
```

### Hardware Optimizer

```python
from slate.slate_hardware_optimizer import HardwareOptimizer

optimizer = HardwareOptimizer()

# Detect hardware
info = optimizer.detect()
print(f"GPU: {info['gpu_name']}")
print(f"Architecture: {info['architecture']}")  # ampere, ada, blackwell
print(f"VRAM: {info['vram_gb']}GB")
print(f"CUDA: {info['cuda_version']}")

# Get recommendations
recs = optimizer.get_recommendations()
for rec in recs:
    print(f"- {rec}")

# Apply optimizations
optimizer.apply_optimizations()

# Install correct PyTorch for architecture
optimizer.install_pytorch()
```

---

## Workflow Management API

### Workflow Guide Endpoints

Base URL: `/api/workflow/guide`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/status` | GET | Get guided workflow status |
| `/start` | POST | Start guided workflow |
| `/category/{category}` | POST | Select job category |
| `/template/{template_id}` | POST | Select job template |
| `/configure` | POST | Configure job parameters |
| `/submit` | POST | Submit job to pipeline |
| `/pipeline` | GET | Get pipeline status |
| `/complete` | POST | Complete workflow |
| `/reset` | POST | Reset workflow |

#### POST /api/workflow/guide/start

Start the guided workflow submission process.

**Response:**
```json
{
  "success": true,
  "active": true,
  "step": "category",
  "categories": [
    {"id": "code", "name": "Code Generation", "templates": [...]},
    {"id": "test", "name": "Testing", "templates": [...]}
  ]
}
```

#### POST /api/workflow/guide/submit

Submit the configured job to the workflow pipeline.

**Response:**
```json
{
  "success": true,
  "job_id": "job-abc123",
  "task": {
    "id": "task-xyz789",
    "title": "Generated Task",
    "status": "pending"
  },
  "pipeline_state": "queued"
}
```

### Workflow Manager SDK

```python
from slate.slate_workflow_manager import SlateWorkflowManager

manager = SlateWorkflowManager()

# Get status
status = manager.get_status()
print(f"Pending: {status['pending']}")
print(f"In Progress: {status['in_progress']}")
print(f"Stale: {status['stale']}")

# Cleanup stale tasks
result = manager.cleanup()
print(f"Cleaned: {result['cleaned']}")

# Enforce rules
result = manager.enforce()
print(f"Violations: {result['violations']}")

# Check if can accept new tasks
can_accept = manager.can_accept_task()
```

---

## Error Handling

### Exception Hierarchy

```python
from slate.exceptions import (
    SlateError,           # Base exception
    BackendError,         # AI backend issues
    TaskError,            # Task queue issues
    ConfigurationError,   # Config problems
    HardwareError,        # GPU/hardware issues
)

try:
    response = generate("prompt")
except BackendError as e:
    print(f"Backend failed: {e}")
except SlateError as e:
    print(f"SLATE error: {e}")
```

### Stability Exceptions

```python
from slate.stability import (
    CircuitBreakerOpen,   # Circuit breaker triggered
    ResourcesExhausted,   # Resource limits exceeded
)

try:
    result = await some_operation()
except CircuitBreakerOpen:
    print("Service temporarily unavailable, circuit breaker open")
except ResourcesExhausted:
    print("Resource limits exceeded, try again later")
```

### HTTP Error Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Invalid parameters |
| 404 | Not Found - Resource not found |
| 500 | Internal Server Error |
| 501 | Not Implemented - Feature not available |

### Error Response Format

```json
{
  "error": "Error message description",
  "detail": "Additional details if available"
}
```

For multi-step operations:

```json
{
  "success": false,
  "steps": [
    {"step": "Step 1", "success": true, "output": "..."},
    {"step": "Step 2", "success": false, "error": "Failed: reason"}
  ],
  "error_count": 1
}
```

---

## Authentication

SLATE runs locally and does not require authentication for local access.

### Security Model

1. **Local Binding Only**: All servers bind to `127.0.0.1` - never `0.0.0.0`
2. **ActionGuard**: Validates all commands before execution
3. **SDK Source Guard**: Only trusted package publishers
4. **PII Scanner**: Blocks credential exposure
5. **Container Isolation**: K8s/Docker sandboxing

### GitHub Authentication

For GitHub-related endpoints, ensure the GitHub CLI is authenticated:

```bash
gh auth login
gh auth status
```

### K8s Authentication

When running in Kubernetes, service accounts provide authentication:

```yaml
# Pod automatically gets mounted service account token
# at /var/run/secrets/kubernetes.io/serviceaccount/token
```

---

## Next Steps

- [Architecture](Architecture) - System design
- [Development](Development) - Contributing guide
- [CLI Reference](CLI-Reference) - Command line tools
- [Schematic SDK](Schematic-SDK) - Diagram generation
- [Kubernetes Deployment](Kubernetes-Deployment) - K8s setup
