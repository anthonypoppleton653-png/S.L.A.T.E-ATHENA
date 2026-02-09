---
name: task-router
agent: 'agent'
description: 'Classify and route incoming tasks to the correct SLATE agent using Ollama for intent detection'
tags: [routing, agents, classification, ollama, automation]
model: 'slate-fast'
# Modified: 2026-02-09T02:42:00-05:00 | Author: ANTIGRAVITY (Gemini) | Change: Fix model from haiku→slate-fast (local-only policy)
# AI Note: When modifying, add a comment with the current date, time, and a 'Gemini' marker.
---

# SLATE Task Router

Classify incoming tasks by intent and route them to the appropriate SLATE agent for execution.

## Agent Registry

| Agent | Patterns | Role | GPU | Model |
|-------|----------|------|-----|-------|
| ALPHA | implement, code, build, fix | Coding | Yes | slate-coder (12B) |
| BETA | test, validate, verify, coverage | Testing | Yes | slate-coder (12B) |
| GAMMA | analyze, plan, research, document | Planning | No | slate-planner (7B) |
| DELTA | claude, mcp, sdk, integration | External Bridge | No | slate-planner (7B) |
| COPILOT_CHAT | diagnose, investigate, troubleshoot | Chat Participant | No | slate-fast (3B) |
| COPILOT | complex, multi-step | Full Orchestration | Yes | slate-coder (12B) |
| ANTIGRAVITY | architect, refactor, master | Primary Developer | Yes | slate-coder (12B) |

## Pipeline

### Step 1: Classify task intent

Use slate-fast (3B) for rapid classification (~308 tok/s):

```powershell
python -c "
import subprocess, json

task = '{{TASK_DESCRIPTION}}'

prompt = f'''Classify this task into exactly ONE agent category.

Task: {task}

Categories (pick ONE):
- ALPHA: Code implementation, bug fixes, feature building
- BETA: Testing, validation, coverage, verification
- GAMMA: Analysis, planning, research, documentation
- DELTA: External integrations (Claude, MCP, SDK)
- COPILOT_CHAT: Diagnostics, troubleshooting, investigation
- COPILOT: Complex multi-step orchestration
- ANTIGRAVITY: Architecture, refactoring, mastery-level work

Output JSON:
{{\"agent\": \"AGENT_NAME\", \"confidence\": 0.0-1.0, \"reasoning\": \"one line\"}}'''

result = subprocess.run(
    ['ollama', 'run', 'slate-fast', prompt],
    capture_output=True, text=True, timeout=20
)
print(result.stdout.strip())
"
```

### Step 2: Load task into workflow manager

```powershell
# Add task to SLATE workflow with agent assignment
python -c "
import json, datetime

task = {
    'description': '{{TASK_DESCRIPTION}}',
    'agent': '{{CLASSIFIED_AGENT}}',
    'confidence': {{CONFIDENCE}},
    'status': 'pending',
    'created': datetime.datetime.utcnow().isoformat() + 'Z',
    'source': 'task-router-prompt'
}

with open('current_tasks.json', 'r', encoding='utf-8') as f:
    tasks = json.load(f)

tasks['tasks'].append(task)

with open('current_tasks.json', 'w', encoding='utf-8') as f:
    json.dump(tasks, f, indent=2, ensure_ascii=False)

print(f'Task routed to {task[\"agent\"]} (confidence: {task[\"confidence\"]})')
"
```

### Step 3: Execute or queue

Based on classification confidence:

| Confidence | Action |
|-----------|--------|
| >= 0.8 | Auto-execute via agent |
| 0.5 - 0.8 | Queue for review, suggest agent |
| < 0.5 | Escalate to COPILOT for multi-step analysis |

```powershell
# High confidence — execute directly
python slate/slate_workflow_manager.py --status

# Queue for autonomous loop
python slate/slate_unified_autonomous.py --single
```

### Batch Routing

Route multiple tasks from a source (GitHub issues, project board, FORGE.md):

```powershell
python -c "
import subprocess, json

# Discover pending tasks
result = subprocess.run(
    ['.venv/Scripts/python.exe', 'slate/slate_unified_autonomous.py', '--discover'],
    capture_output=True, text=True
)
print('Discovered tasks:')
print(result.stdout)
"
```

## FORGE Log Entry

```
[COPILOT] TIMESTAMP | MAGIC: task-router
  Task: {{TASK_DESCRIPTION}}
  Agent: {{CLASSIFIED_AGENT}}
  Confidence: {{CONFIDENCE}}
  Action: auto-execute / queued / escalated
```
