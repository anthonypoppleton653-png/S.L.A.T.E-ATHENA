# Vendor SDKs
<!-- Modified: 2026-02-08T12:00:00Z | Author: Claude Opus 4.5 | Change: Create comprehensive vendor SDK integration documentation -->

SLATE integrates multiple vendor SDKs to provide unified agent orchestration, LLM management, and workflow automation. All integrations are **local-first** with no mandatory cloud dependencies.

## Overview

<table>
<tr>
<th colspan="5" align="center">Vendor SDK Integration Matrix</th>
</tr>
<tr>
<td align="center"><strong>OpenAI Agents</strong><br><sub>Multi-agent workflows</sub><br><code>vendor/openai-agents-python</code></td>
<td align="center"><strong>AutoGen</strong><br><sub>Agentic conversations</sub><br><code>vendor/autogen</code></td>
<td align="center"><strong>Semantic Kernel</strong><br><sub>LLM orchestration</sub><br><code>vendor/semantic-kernel</code></td>
<td align="center"><strong>Copilot SDK</strong><br><sub>GitHub Copilot bridge</sub><br><code>vendor/copilot-sdk</code></td>
<td align="center"><strong>Spec-Kit</strong><br><sub>Spec-driven workflow</sub><br><code>vendor/spec-kit</code></td>
</tr>
</table>

---

## Supported Vendors

| Vendor | SDK | Purpose | Integration File |
|:-------|:----|:--------|:-----------------|
| **OpenAI Agents** | `openai-agents-python` | Agent, function_tool, Guardrails, Handoffs | `slate/vendor_agents_sdk.py` |
| **Microsoft AutoGen** | `autogen-core` | Multi-agent conversations, AgentRuntime | `slate/vendor_autogen_sdk.py` |
| **Microsoft Semantic Kernel** | `semantic-kernel` | LLM orchestration, SK plugins, ChromaDB RAG | `slate/slate_semantic_kernel.py` |
| **GitHub Copilot** | `github-copilot-sdk` | define_tool, SessionHooks, MCP bridge | `slate/slate_copilot_sdk.py` |
| **Spec-Kit** | `spec-kit` | Specification-driven development | `slate/slate_spec_kit.py` |

### Check Integration Status

```powershell
# Full vendor status
python slate/vendor_integration.py

# JSON output for automation
python slate/vendor_integration.py --json

# Run integration tests
python slate/vendor_integration.py --test
```

---

## Import Helpers

SLATE's `vendor/` directory shadows pip-installed packages. Import helpers solve this by using **sys.path swap** technique.

### The Problem

```python
# This fails because SLATE has an agents/ directory
import agents  # Imports SLATE's agents/, not openai-agents-python
```

### The Solution

```python
# Use SLATE's import helper instead
from slate.vendor_agents_sdk import (
    Agent, function_tool, FunctionTool,
    InputGuardrail, OutputGuardrail,
    Runner, Handoff, SDK_AVAILABLE,
)

if SDK_AVAILABLE:
    print("OpenAI Agents SDK ready")
```

### How It Works

1. **Stash** SLATE's conflicting modules from `sys.modules`
2. **Insert** vendor path at front of `sys.path`
3. **Import** SDK classes from vendored fork
4. **Restore** original `sys.path` and SLATE modules
5. **Expose** SDK classes as module-level globals

---

## Type Bridges

Each vendor SDK provides type bridges that map their abstractions to SLATE's internal types.

### OpenAI Agents SDK Types

| SDK Type | SLATE Use |
|:---------|:----------|
| `Agent` | Multi-agent workflow orchestration |
| `function_tool` | Tool decorator for function registration |
| `FunctionTool` | Tool class for programmatic creation |
| `InputGuardrail` | Pre-execution validation (maps to ActionGuard) |
| `OutputGuardrail` | Post-execution validation |
| `Runner` | Agent execution context |
| `Handoff` | Agent-to-agent task transfer |

### AutoGen SDK Types

| SDK Type | SLATE Use |
|:---------|:----------|
| `Agent` | Protocol for agent interface |
| `BaseAgent` | Base class for custom agents |
| `AgentRuntime` | Multi-agent execution runtime |
| `ClosureAgent` | Function-based agent creation |
| `MessageContext` | Message passing context |
| `TopicId` | Pub/sub topic addressing |

### Semantic Kernel Types

| SDK Type | SLATE Use |
|:---------|:----------|
| `Kernel` | Central orchestration object |
| `kernel_function` | SK plugin function decorator |
| `OpenAIChatCompletion` | Chat service (uses Ollama endpoint) |
| `ChatHistory` | Conversation memory |

---

## Configuration

### Vendor Paths

Vendors are installed as Git submodules in `vendor/`:

```
vendor/
  openai-agents-python/src/   # OpenAI Agents SDK
  autogen/python/packages/    # Microsoft AutoGen
  semantic-kernel/python/     # Microsoft Semantic Kernel
  copilot-sdk/python/         # GitHub Copilot SDK
  spec-kit/                   # Spec-Kit workflow
```

### Initialize Submodules

```bash
# Clone with submodules
git clone --recurse-submodules https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E.git

# Or initialize after clone
git submodule update --init --recursive
```

### Environment Variables

| Variable | Default | Description |
|:---------|:--------|:------------|
| `OLLAMA_HOST` | `127.0.0.1:11434` | Ollama endpoint for SK |
| `CHROMADB_HOST` | (local) | ChromaDB for SK memory |
| `COPILOT_CLI_PATH` | (auto-detect) | Path to Copilot CLI |
| `GITHUB_TOKEN` | (git credential) | GitHub auth for Copilot |

---

## Usage Examples

### OpenAI Agents SDK

Create multi-agent workflows with function tools and guardrails:

```python
from slate.vendor_agents_sdk import (
    Agent, function_tool, InputGuardrail,
    Runner, SDK_AVAILABLE,
)

if not SDK_AVAILABLE:
    raise ImportError("OpenAI Agents SDK not available")

# Define a function tool
@function_tool
def slate_status() -> str:
    """Check SLATE system status."""
    import subprocess
    result = subprocess.run(
        ["python", "slate/slate_status.py", "--quick"],
        capture_output=True, text=True
    )
    return result.stdout

# Create an agent with the tool
agent = Agent(
    name="slate-operator",
    instructions="You are a SLATE system operator.",
    tools=[slate_status],
)

# Run with guardrails
async def run():
    runner = Runner()
    result = await runner.run(agent, "Check system status")
    return result
```

### Microsoft AutoGen

Create multi-agent conversations with the AutoGen framework:

```python
from slate.vendor_autogen_sdk import (
    ClosureAgent, AgentRuntime, MessageContext,
    SDK_AVAILABLE, create_slate_agent,
)

if not SDK_AVAILABLE:
    raise ImportError("AutoGen SDK not available")

# Create a SLATE-compatible agent
async def task_handler(context: MessageContext, message: str) -> str:
    """Handle incoming task messages."""
    return f"Processed: {message}"

agent = create_slate_agent(
    name="task-processor",
    description="Processes SLATE tasks",
    handler=task_handler,
)

# Use with AgentRuntime (if available)
# runtime = AgentRuntime()
# await runtime.register(agent)
```

### Microsoft Semantic Kernel

Use SK for LLM orchestration with Ollama and ChromaDB:

```python
import asyncio
from slate.slate_semantic_kernel import (
    create_slate_kernel,
    invoke_sk,
    get_sk_status,
)

# Check status
status = get_sk_status()
print(f"SK Available: {status['semantic_kernel']['available']}")
print(f"Ollama: {status['ollama']['available']}")
print(f"Models: {status['ollama']['models_count']}")

# Invoke with model role
async def run():
    # Simple invocation
    result = await invoke_sk(
        prompt="What is SLATE?",
        model_role="general",  # code, fast, planner, general
        enable_memory=True,    # ChromaDB RAG
        enable_plugins=True,   # SLATE SK plugins
    )
    print(result)

asyncio.run(run())
```

#### SK Plugins

SLATE registers three SK plugins automatically:

| Plugin | Functions |
|:-------|:----------|
| `slate_system` | `get_system_status`, `get_runtime_integrations`, `get_workflow_status`, `get_gpu_status` |
| `slate_search` | `search_codebase` (ChromaDB semantic search) |
| `slate_agents` | `route_task` (agent-based task routing) |

```powershell
# List SK plugins
python slate/slate_semantic_kernel.py --plugins

# Run SK benchmark
python slate/slate_semantic_kernel.py --benchmark

# Invoke with function calling
python slate/slate_semantic_kernel.py --invoke "Check GPU status" --function-calling
```

### GitHub Copilot SDK

Connect SLATE to GitHub Copilot with full tool definitions:

```python
from slate.slate_copilot_sdk import (
    SlateCopilotPlugin,
    create_session_config,
    SLATE_TOOLS,
)

# Check integration
plugin = SlateCopilotPlugin()
status = plugin.get_status()
print(f"SDK: {status['copilot_sdk']['installed']}")
print(f"CLI: {status['copilot_cli']['found']}")
print(f"Tools: {status['tools']['count']}")

# Execute tool directly (no Copilot CLI needed)
result = plugin.execute_tool("slate_status", {"format": "quick"})
print(result)
```

#### SessionHooks (ActionGuard)

SLATE implements all 6 Copilot SDK hooks:

| Hook | Purpose |
|:-----|:--------|
| `PreToolUse` | ActionGuard - blocks dangerous patterns |
| `PostToolUse` | Audit log - timestamps every tool call |
| `UserPromptSubmitted` | PII scanner - redacts tokens/emails/keys |
| `SessionStart` | Health check - injects system state |
| `SessionEnd` | Cleanup - logs session reason |
| `ErrorOccurred` | Recovery - retries recoverable errors |

```powershell
# Verify full integration
python slate/slate_copilot_sdk.py --verify

# List all tools
python slate/slate_copilot_sdk.py --list-tools

# Run as agent server
python slate/slate_copilot_sdk.py --server
```

### Spec-Kit

Use specification-driven development:

```python
from slate.slate_spec_kit import SpecKit

kit = SpecKit()

# Check status
status = kit.get_status()
print(f"Specs: {status['spec_count']}")

# Process all specs
kit.process_all()

# Generate wiki
kit.generate_wiki()
```

```powershell
# Process specs with AI analysis
python slate/slate_spec_kit.py --process-all

# Generate wiki from specs
python slate/slate_spec_kit.py --wiki

# Analyze single spec
python slate/slate_spec_kit.py --analyze specs/001-dashboard/spec.md
```

---

## Fork Sync System

SLATE maintains forks of vendor SDKs to ensure stability and enable customization.

### Registered Forks

| Fork | Upstream | Purpose |
|:-----|:---------|:--------|
| `openai-agents-python` | `openai/openai-agents-python` | Multi-agent workflow patterns |
| `semantic-kernel` | `microsoft/semantic-kernel` | LLM orchestration and skills |
| `autogen` | `microsoft/autogen` | Multi-agent conversations |
| `copilot-sdk` | `github/copilot-sdk` | GitHub Copilot integration |
| `spec-kit` | `speckit/spec-kit` | Specification workflow |

### Fork Management Commands

```powershell
# Check all fork status
python slate/slate_fork_sync.py --status

# List registered forks
python slate/slate_fork_sync.py --list

# Sync all forks with upstream
python slate/slate_fork_sync.py --sync-all

# Check upstream commits
python slate/slate_fork_sync.py --upstream openai-agents-python

# AI analysis of integration opportunities
python slate/slate_fork_sync.py --analyze
```

### Sync Workflow

```
Upstream Repository
       |
       v (gh repo sync)
SLATE Fork (SynchronizedLivingArchitecture/*)
       |
       v (git submodule update --remote)
Local Submodule (vendor/*)
       |
       v (import helper)
SLATE Integration (slate/vendor_*.py)
```

---

## Security

All vendor SDK integrations are protected by SLATE's security layers:

| Layer | Protection |
|:------|:-----------|
| **ActionGuard** | Blocks dangerous patterns (`rm -rf`, `eval()`, external APIs) |
| **SDK Source Guard** | Only trusted publishers (Microsoft, OpenAI, GitHub) |
| **PII Scanner** | Redacts tokens, emails, API keys before processing |
| **Local Only** | All services bind to `127.0.0.1` |

### Trusted Publishers

Vendor SDKs must come from these organizations:

- Microsoft (AutoGen, Semantic Kernel)
- OpenAI (Agents SDK)
- GitHub (Copilot SDK)
- NVIDIA (TensorRT-LLM, NeMo)

---

## Troubleshooting

### SDK Not Available

```powershell
# Check which SDKs are loaded
python slate/vendor_integration.py

# Check specific vendor
python -c "from slate.vendor_agents_sdk import SDK_AVAILABLE; print(SDK_AVAILABLE)"
```

### Submodule Not Initialized

```bash
# Initialize all submodules
git submodule update --init --recursive

# Check submodule status
git submodule status
```

### Import Conflicts

If you see module conflicts:

```python
# Clear cached modules before import
import sys
for key in list(sys.modules.keys()):
    if key.startswith('agents'):
        del sys.modules[key]

# Then use import helper
from slate.vendor_agents_sdk import Agent
```

### Copilot CLI Not Found

```powershell
# Install Copilot CLI globally
npm install -g @github/copilot

# Or set path manually
$env:COPILOT_CLI_PATH = "C:\path\to\copilot\index.js"
```

---

## Related Documentation

- [AI Backends](AI-Backends) - Ollama, Foundry Local, ChromaDB
- [Architecture](Architecture) - System design and components
- [CLI Reference](CLI-Reference) - Command-line tools
- [Configuration](Configuration) - Settings and customization
- [Contributor Guide](Contributor-Guide) - Fork and PR workflow

---

## Quick Reference

```powershell
# Check all vendor status
python slate/vendor_integration.py

# Run vendor tests
python slate/vendor_integration.py --test

# Check SK status
python slate/slate_semantic_kernel.py --status

# Check Copilot SDK status
python slate/slate_copilot_sdk.py --status

# Verify Copilot integration
python slate/slate_copilot_sdk.py --verify

# Check fork sync status
python slate/slate_fork_sync.py --status
```
