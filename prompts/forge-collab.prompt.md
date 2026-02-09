---
name: forge-collab
agent: 'agent'
description: 'Meta-prompt for AI-to-AI collaboration — coordinate Copilot and Antigravity via FORGE.md, Docker volumes, and MCP'
tags: [collaboration, forge, meta-prompt, agents, mcp, docker]
model: 'slate-planner'
# Modified: 2026-02-09T02:42:00-05:00 | Author: ANTIGRAVITY (Gemini) | Change: Fix model from sonnet→slate-planner (local-only policy)
# AI Note: When modifying, add a comment with the current date, time, and a 'Gemini' marker.
---

# FORGE Collaboration Protocol

Meta-prompt for coordinating AI team members (Copilot CLI, Antigravity, autonomous agents) via shared state in FORGE.md, Docker volumes, and MCP tools.

## Architecture

```
┌──────────────┐     FORGE.md      ┌──────────────────┐
│   COPILOT    │◄──────────────────►│   ANTIGRAVITY    │
│  (Analysis)  │                    │  (Execution)     │
│              │     Docker Vol     │                  │
│  Prompts/    │◄──────────────────►│  Code changes/   │
│  Planning    │                    │  CI/CD           │
│              │       MCP          │                  │
│  slate_ai    │◄──────────────────►│  slate_runner    │
└──────────────┘                    └──────────────────┘
       │                                    │
       ▼                                    ▼
┌──────────────────────────────────────────────┐
│              SLATE Autonomous Loop           │
│  slate_unified_autonomous.py                 │
│  Task discovery → Classification → Execution │
└──────────────────────────────────────────────┘
```

## Collaboration Workflow

### Phase 1: Sync (Every session start)

```powershell
# Both agents read FORGE.md for teammate updates
python -c "
with open('FORGE.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Find latest entries
lines = content.split('\n')
recent = [l for l in lines if l.startswith('### [')]
for entry in recent[-5:]:
    print(entry)
"
```

### Phase 2: Divide work

Use slate-planner (7B) to analyze the task and propose division:

```powershell
python -c "
import subprocess

task = '{{USER_TASK}}'

prompt = f'''You are a work coordinator for two AI agents:

COPILOT: Expert at analysis, prompt engineering, code review, planning.
  Tools: read files, search code, generate prompts, review PRs
  Strengths: Deep analysis, documentation, quality gates

ANTIGRAVITY: Expert at execution, refactoring, architecture, deployment.
  Tools: write/edit files, run terminal commands, git operations, CI/CD
  Strengths: Code generation, testing, deployment, GPU operations

Task from boss: {task}

Divide into parallel workstreams:
1. What should COPILOT do? (analysis/prompts)
2. What should ANTIGRAVITY do? (execution/code)
3. What is the sync point? (where they merge results)
4. What goes in FORGE.md?

Output as structured plan with clear handoff points.'''

result = subprocess.run(
    ['ollama', 'run', 'slate-planner', prompt],
    capture_output=True, text=True, timeout=60
)
print(result.stdout)
"
```

### Phase 3: Execute in parallel

**COPILOT stream** (analysis):
```powershell
# Analyze codebase, generate prompts, review changes
python slate/slate_chromadb.py --search "{{RELEVANT_QUERY}}"
# Generate targeted prompts in prompts/
# Write analysis to FORGE.md
```

**ANTIGRAVITY stream** (execution):
```powershell
# Implement changes, run tests, deploy
# Read COPILOT's analysis from FORGE.md
# Execute code changes per analysis
# Push results back to FORGE.md
```

### Phase 4: Merge & validate

```powershell
# Both agents validate the combined output
python slate/slate_workflow_manager.py --status
python -c "
import subprocess
result = subprocess.run(
    ['ollama', 'run', 'slate-planner',
     'Review FORGE.md for consistency. Are both agents aligned? Any conflicts?'],
    capture_output=True, text=True, timeout=30
)
print(result.stdout)
"
```

### Phase 5: Report to boss

```powershell
python -c "
import datetime

timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
report = f'''
### [TEAM] {timestamp} | OUTPUT: Task complete

**Task**: {{USER_TASK}}
**COPILOT contribution**: {{COPILOT_WORK}}
**ANTIGRAVITY contribution**: {{ANTIGRAVITY_WORK}}
**Result**: {{OUTCOME}}
**Next steps**: {{RECOMMENDATIONS}}
'''

with open('FORGE.md', 'a', encoding='utf-8') as f:
    f.write(report)

print(report)
"
```

## MCP Integration

Use MCP tools for cross-agent communication:

| MCP Tool | Purpose | Used By |
|----------|---------|---------|
| `slate_ai` | Prompt generation, inference | Both |
| `slate_spec_kit` | Spec processing, wiki gen | COPILOT |
| `slate_workflow` | Task management | Both |
| `slate_runner` | CI/CD dispatch | ANTIGRAVITY |
| `slate_kubernetes` | K8s deploy/status | ANTIGRAVITY |
| `slate_benchmark` | Performance validation | Both |

## Docker Volume Sharing

When running in containers, FORGE.md is shared via volume:

```yaml
# docker-compose.yml addition
volumes:
  - ./FORGE.md:/app/FORGE.md
  - ./prompts:/app/prompts
  - ./current_tasks.json:/app/current_tasks.json
```

Both containers read/write to the same FORGE.md for real-time coordination.

## Conflict Resolution

If both agents edit the same file:
1. FORGE.md → append-only, no conflicts
2. Code files → ANTIGRAVITY has write priority
3. Prompts → COPILOT has write priority
4. Config/YAML → Requires explicit handoff in FORGE.md

## FORGE Log Entry

```
[TEAM] TIMESTAMP | MAGIC: forge-collab
  Task: {{USER_TASK}}
  Division: COPILOT=[analysis] / ANTIGRAVITY=[execution]
  Sync point: {{MERGE_POINT}}
  Status: in-progress / complete
```
