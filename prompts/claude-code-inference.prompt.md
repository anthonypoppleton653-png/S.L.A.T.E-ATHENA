---
name: claude-code-inference
agent: 'agent'
description: 'Route complex AI tasks to Claude Code via the unified backend — agentic code generation, refactoring, prompt engineering, and multi-step reasoning'
tags: [claude-code, inference, agentic, code-generation, refactoring, reasoning, mcp]
model: 'slate-planner'
# Modified: 2026-02-09T14:00:00Z | Author: ClaudeCode (Opus 4.6) | Change: Create Claude Code inference super prompt
---

# Claude Code Inference Pipeline

Route complex AI tasks through SLATE's unified AI backend to Claude Code (Opus 4.6) for agentic execution via the copilot agent bridge.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Task Input                                 │
│  (GitHub issue, PR review, code request, prompt request)     │
└──────────────┬───────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│              Unified AI Backend                               │
│  slate/unified_ai_backend.py                                 │
│                                                              │
│  1. Classify task type (keyword matching)                    │
│  2. Route to provider (Claude Code / Ollama / Foundry)       │
│  3. Select model (opus-4.6 / sonnet-4.5 / slate-coder)     │
│  4. Execute with failover                                    │
└──────────────┬───────────────────────────────────────────────┘
               │
     ┌─────────┼─────────┐
     │         │         │
     ▼         ▼         ▼
┌─────────┐ ┌────────┐ ┌────────┐
│ Claude  │ │ Ollama │ │Foundry │
│ Code    │ │ Local  │ │ Local  │
│ (MCP)   │ │(11434) │ │(5272)  │
└─────────┘ └────────┘ └────────┘
```

## When to Route to Claude Code

Claude Code is the preferred provider for tasks requiring:

1. **Multi-step reasoning** — tasks that need planning, then execution, then verification
2. **Complex code generation** — new modules, architectural changes, cross-file refactoring
3. **Prompt engineering** — creating or evolving super prompts for Ollama
4. **Code review augmentation** — when slate-coder (12B) needs a second opinion
5. **Cross-system orchestration** — tasks touching multiple SLATE subsystems

## Execution Flow

### Step 1: Task Classification

```powershell
python slate/unified_ai_backend.py --route "{{TASK_TYPE}}"
```

Task types that prefer Claude Code:
- `bug_fix` — complex debugging and fix generation
- `refactoring` — architectural restructuring
- `analysis` — deep code analysis and investigation
- `research` — exploration and discovery
- `prompt_engineering` — super prompt creation

### Step 2: Dispatch via Unified Backend

```powershell
# Direct execution (auto-routes to Claude Code for complex tasks)
python slate/unified_ai_backend.py --task "{{TASK_DESCRIPTION}}"

# Force Claude Code provider
python slate/unified_ai_backend.py --task "{{TASK_DESCRIPTION}}" --provider claude_code

# Force specific model
python slate/unified_ai_backend.py --task "{{TASK_DESCRIPTION}}" --provider claude_code --model opus-4.6
```

### Step 3: Bridge-Based Execution

For agentic tasks, the unified backend dispatches through the copilot agent bridge:

```powershell
# Check bridge status
python slate/copilot_agent_bridge.py --status

# View pending tasks (dispatched to Claude Code)
python slate/copilot_agent_bridge.py --pending

# View results
python slate/copilot_agent_bridge.py --results
```

### Step 4: Result Integration

Results flow back through the bridge and are:
1. Written to `.slate_copilot_bridge_results.json`
2. Available for polling by the unified backend
3. Logged in FORGE.md for team coordination

## MCP Tool Integration

Claude Code has access to all 12 SLATE MCP tools:

| Tool | Use Case |
|------|----------|
| `slate_status` | Check system health before/after execution |
| `slate_workflow` | Manage task lifecycle |
| `slate_ai` | Route sub-tasks to Ollama |
| `slate_runner` | Dispatch CI/CD workflows |
| `slate_gpu` | Check GPU availability for model placement |
| `slate_claude_code` | Self-validation of integration |
| `slate_spec_kit` | Process specifications |
| `slate_schematic` | Generate system diagrams |

## FORGE.md Coordination

All Claude Code inference results are logged to FORGE.md:

```
[CLAUDECODE] TIMESTAMP | OUTPUT: Task complete
  Task: {{TASK_DESCRIPTION}}
  Provider: claude_code (opus-4.6)
  Result: {{RESULT_SUMMARY}}
  Duration: {{DURATION_MS}}ms
  Tokens: {{TOKEN_COUNT}}
```

## Security

- All tasks validated by ActionGuard before execution
- No external API calls (Claude Code runs as local CLI)
- Bridge files use file-based IPC (127.0.0.1 only)
- PII scanner checks all task inputs/outputs

## FORGE Log Entry

```
[CLAUDECODE] TIMESTAMP | MAGIC: claude-code-inference
  Task: {{TASK_DESCRIPTION}}
  Type: {{TASK_TYPE}}
  Provider: claude_code → opus-4.6
  Status: dispatched / completed / failed
```
