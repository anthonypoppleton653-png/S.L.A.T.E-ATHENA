# Development Guide
<!-- Modified: 2026-02-08T12:00:00Z | Author: Claude Opus 4.5 | Change: Comprehensive developer documentation -->

Contributing to SLATE - guidelines, workflows, and best practices.

## Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [Project Structure Overview](#project-structure-overview)
3. [Adding New Features (Spec-Driven Approach)](#adding-new-features-spec-driven-approach)
4. [Spec-Kit Workflow](#spec-kit-workflow)
5. [Testing Guidelines](#testing-guidelines)
6. [Code Style](#code-style)
7. [Creating New MCP Tools](#creating-new-mcp-tools)
8. [Adding Slash Commands](#adding-slash-commands)
9. [Contributing to Vendor SDK Integrations](#contributing-to-vendor-sdk-integrations)
10. [Creating Custom Ollama Models](#creating-custom-ollama-models)
11. [Debug and Development Modes](#debug-and-development-modes)
12. [Running Local Tests](#running-local-tests)
13. [Container and Kubernetes Development](#container-and-kubernetes-development)

---

## Development Environment Setup

### Prerequisites

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.11+ | Backend runtime |
| Git | 2.x+ | Version control |
| Ollama | Latest | Local LLM inference |
| NVIDIA GPU | Optional | Accelerated inference (dual RTX 5070 Ti recommended) |
| Docker | Latest | Container builds |
| kubectl | Latest | Kubernetes deployment |

### Clone and Install

```bash
# Clone the repository
git clone https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E.git
cd S.L.A.T.E

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.\.venv\Scripts\activate

# Activate (Linux/macOS)
source .venv/bin/activate

# Install dependencies with dev extras
pip install -e ".[dev]"
```

### Verify Installation

```bash
# Run tests
python -m pytest tests/ -v

# Check system status (auto-detects GPU, services, Python)
python slate/slate_status.py --quick

# Check all runtime integrations
python slate/slate_runtime.py --check-all

# Verify vendor SDK availability
python slate/vendor_integration.py --json
```

### IDE Configuration

**VS Code (Recommended)**

Install required extensions:
| Extension | ID | Purpose |
|-----------|-----|---------|
| Python | `ms-python.python` | Python language support |
| Pylance | `ms-python.vscode-pylance` | Type checking |
| Ruff | `charliermarsh.ruff` | Linting |
| Docker | `ms-azuretools.vscode-docker` | Container management |
| Kubernetes | `ms-kubernetes-tools.vscode-kubernetes-tools` | K8s deployment |

Apply SLATE Dark theme for the evolving schematic background:
```
> SLATE: Apply SLATE Dark Theme
```

---

## Project Structure Overview

```
slate/                    # Core SLATE engine modules
  __init__.py             # Package exports
  action_guard.py         # Security enforcement (blocks dangerous patterns)
  mcp_server.py           # MCP server for Claude Code integration
  ollama_client.py        # Ollama LLM client
  foundry_local.py        # Foundry Local + Ollama unified client
  unified_ai_backend.py   # AI task routing (FREE local backends)
  slate_status.py         # System status checker
  slate_workflow_manager.py  # Task queue management
  slate_runner_manager.py    # GitHub Actions runner
  slate_spec_kit.py       # Spec-Kit wiki integration
  claude_code_validator.py   # Claude Code settings validator
  vendor_integration.py   # Vendor SDK status checker
  vendor_agents_sdk.py    # OpenAI Agents Python integration
  vendor_autogen_sdk.py   # Microsoft AutoGen integration
  slate_semantic_kernel.py   # Semantic Kernel integration

agents/                   # Dashboard server and legacy agent code
  slate_dashboard_server.py  # FastAPI dashboard (port 8080)

slate_core/               # Shared infrastructure
  file_lock.py            # FileLock for atomic JSON access
  gpu_scheduler.py        # Multi-GPU task scheduling

specs/                    # Feature specifications
  001-*/                  # Numbered spec directories
  002-*/
  ...

tests/                    # Test suite
  unit/                   # Unit tests
  integration/            # Integration tests
  contract/               # Contract tests
  test_*.py               # Top-level tests

.claude/                  # Claude Code configuration
  commands/               # Slash commands
  behaviors/              # Behavior profiles
  settings.json           # Main configuration
  hooks.json              # ActionGuard hook integration

.claude-plugin/           # Plugin manifest
  plugin.json             # Plugin definition
  marketplace.json        # Distribution catalog

skills/                   # Agent skills (skills/*/SKILL.md)

vendor/                   # Vendored SDK submodules
  openai-agents-python/
  autogen/
  semantic-kernel/

docs/                     # Documentation
  wiki/                   # Wiki pages
  pages/                  # GitHub Pages

k8s/                      # Kubernetes manifests
  overlays/               # Environment-specific configs

.slate_tech_tree/         # Tech tree state
.slate_changes/           # Detected code changes
.slate_errors/            # Error logs with context
.slate_index/             # ChromaDB vector index
```

---

## Adding New Features (Spec-Driven Approach)

SLATE follows a **specification-driven development** model. Every significant feature goes through the Spec-Kit workflow before implementation.

### Feature Lifecycle

```
IDEA → /speckit.specify → /speckit.plan → /speckit.tasks → /speckit.implement → COMPLETE
         ↓                    ↓                ↓                  ↓
       spec.md            plan.md          tasks.md        Implementation
```

### 1. Create Specification

Use the `/speckit.specify` command with a natural language feature description:

```
/speckit.specify Add dark mode toggle to the dashboard
```

This creates:
- Feature branch: `NNN-dark-mode-toggle`
- Spec directory: `specs/NNN-dark-mode-toggle/`
- Initial spec file: `specs/NNN-dark-mode-toggle/spec.md`
- Quality checklist: `specs/NNN-dark-mode-toggle/checklists/requirements.md`

### 2. Write Tests First (TDD Mandate)

Before implementing, write failing tests:

```python
# tests/test_dark_mode.py
import pytest

def test_dark_mode_toggle_exists():
    """Test dark mode toggle component exists."""
    from slate.dashboard import get_theme_toggle
    assert get_theme_toggle() is not None

def test_dark_mode_applies_theme():
    """Test dark mode applies correct CSS variables."""
    from slate.dashboard import apply_theme
    result = apply_theme("dark")
    assert result["--bg-color"] == "#0D1B2A"
```

### 3. Implement Feature

```python
# slate/dashboard.py
"""Dashboard theme management."""
# Modified: 2026-02-08T12:00:00Z | Author: Developer | Change: Add dark mode toggle

def get_theme_toggle() -> dict:
    """Get theme toggle component.

    Returns:
        Dictionary containing toggle configuration.
    """
    return {"id": "theme-toggle", "default": "light"}

def apply_theme(theme: str) -> dict:
    """Apply the specified theme.

    Args:
        theme: Theme name ("light" or "dark").

    Returns:
        Dictionary of CSS variables for the theme.

    Raises:
        ValueError: If theme name is invalid.
    """
    themes = {
        "light": {"--bg-color": "#FFFFFF"},
        "dark": {"--bg-color": "#0D1B2A"},
    }
    if theme not in themes:
        raise ValueError(f"Invalid theme: {theme}")
    return themes[theme]
```

### 4. Export from Package

```python
# slate/__init__.py
from .dashboard import get_theme_toggle, apply_theme

__all__ = [
    # ... existing exports
    "get_theme_toggle",
    "apply_theme",
]
```

### 5. Update Documentation

- Update `CLAUDE.md` if the feature is significant
- Add to relevant wiki pages
- Update CLI documentation if applicable
- Mark spec as `complete` when done

---

## Spec-Kit Workflow

Spec-Kit provides a complete specification-to-implementation workflow using Claude Code slash commands.

### Command Sequence

| Step | Command | Output | Purpose |
|------|---------|--------|---------|
| 1 | `/speckit.specify <description>` | `spec.md` | Define WHAT and WHY |
| 2 | `/speckit.clarify` | Updated spec | Resolve ambiguities |
| 3 | `/speckit.plan` | `plan.md`, `research.md`, `data-model.md` | Define HOW |
| 4 | `/speckit.tasks` | `tasks.md` | Break into actionable tasks |
| 5 | `/speckit.implement` | Implementation | Execute the plan |
| 6 | `/speckit.analyze` | Consistency report | Verify alignment |
| 7 | `/speckit.checklist` | Domain checklist | Validate completeness |

### Spec-Kit Principles

**Specifications focus on WHAT and WHY, not HOW:**

| DO (Specification) | DON'T (Implementation) |
|--------------------|------------------------|
| "Users can search products" | "Use Elasticsearch with React" |
| "System handles 10,000 users" | "Deploy on 3 Kubernetes pods" |
| "Response time under 2 seconds" | "Use Redis caching layer" |

**Success Criteria must be:**
- Measurable (specific metrics)
- Technology-agnostic (no framework references)
- User-focused (business outcomes)
- Verifiable (testable without implementation details)

### Example Workflow

```bash
# 1. Create specification from idea
/speckit.specify I want to add user authentication with OAuth2

# 2. Clarify any ambiguities (interactive Q&A)
/speckit.clarify

# 3. Create technical plan
/speckit.plan I am building with Python/FastAPI and PostgreSQL

# 4. Generate task breakdown
/speckit.tasks

# 5. Start implementation (phase by phase)
/speckit.implement
```

---

## Testing Guidelines

### Test-Driven Development (Constitution Mandate)

SLATE follows strict TDD as mandated by the constitution:

```
1. WRITE TEST → Define expected behavior (failing test)
2. RUN TEST   → Verify it fails (red)
3. IMPLEMENT  → Minimum code to pass
4. RUN TEST   → Verify it passes (green)
5. REFACTOR   → Clean up while keeping tests green
```

### Running Tests

```bash
# All tests
python -m pytest tests/ -v

# Specific test file
python -m pytest tests/test_greeting.py -v

# Specific test function
python -m pytest tests/test_greeting.py::test_greet_default -v

# With coverage
python -m pytest tests/ --cov=slate -q

# HTML coverage report
python -m pytest tests/ --cov=slate --cov-report=html

# Run only unit tests
python -m pytest tests/unit/ -v

# Run integration tests
python -m pytest tests/integration/ -v

# Parallel execution
python -m pytest tests/ -n auto
```

### Test Structure

```
tests/
  unit/              # Isolated unit tests (no external dependencies)
  integration/       # Tests requiring services (Ollama, DB, etc.)
  contract/          # API contract tests
  fixtures/          # Shared test fixtures
  conftest.py        # pytest configuration
  test_*.py          # Top-level tests
```

### Writing Tests

```python
import pytest
from slate.greeting import greet

class TestGreeting:
    """Tests for greeting module."""

    def test_greet_default(self):
        """Test greeting with default name."""
        result = greet()
        assert result == "Hello, World!"

    def test_greet_custom_name(self):
        """Test greeting with custom name."""
        result = greet("SLATE")
        assert result == "Hello, SLATE!"

    @pytest.mark.parametrize("name,expected", [
        ("Alice", "Hello, Alice!"),
        ("Bob", "Hello, Bob!"),
        ("", "Hello, World!"),  # Edge case: empty string
    ])
    def test_greet_parametrized(self, name, expected):
        """Test greeting with various names."""
        assert greet(name) == expected

    def test_greet_raises_on_invalid_type(self):
        """Test that non-string input raises TypeError."""
        with pytest.raises(TypeError):
            greet(123)

# Fixtures for common setup
@pytest.fixture
def mock_ollama_client(mocker):
    """Mock Ollama client for unit tests."""
    return mocker.patch("slate.ollama_client.OllamaClient")
```

### Coverage Requirements

| Module | Target Coverage |
|--------|----------------|
| `slate/` | 50%+ |
| `slate_core/` | 50%+ |
| Critical paths | 80%+ |

All new code must include tests. PRs without tests will be rejected.

---

## Code Style

### Python Guidelines

| Rule | Example |
|------|---------|
| Type hints required | `def process(task_id: str) -> dict:` |
| Google-style docstrings | See example below |
| Use `Annotated` for tool parameters | `priority: Annotated[int, "Priority 1-5"]` |
| Maximum line length | 100 characters |
| Modification timestamps | `# Modified: 2026-02-08T12:00:00Z` |

### Docstring Format

```python
def process_task(
    task_id: str,
    priority: Annotated[int, "Priority level 1-5"] = 3,
) -> dict:
    """Process a task with the given priority.

    Args:
        task_id: Unique task identifier.
        priority: Priority level (1=lowest, 5=highest).

    Returns:
        Dictionary containing task results with keys:
        - status: Task completion status
        - duration: Processing time in seconds
        - result: Task output data

    Raises:
        ValueError: If task_id is invalid or empty.
        TaskNotFoundError: If task does not exist.

    Example:
        >>> result = process_task("task-123", priority=5)
        >>> print(result["status"])
        "completed"
    """
    ...
```

### Modification Timestamps

Every file modification should include a timestamp comment:

```python
#!/usr/bin/env python3
# Modified: 2026-02-08T12:00:00Z | Author: Developer | Change: Add new feature
```

For updates within a file:

```python
# Modified: 2026-02-08T12:00:00Z | Author: Developer | Change: Fix edge case handling
def existing_function():
    ...
```

### Import Organization

```python
# Standard library
import os
import sys
from pathlib import Path

# Third-party
import httpx
from fastapi import FastAPI

# Local imports - add workspace root to path
WORKSPACE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from slate import get_status
from slate_core.file_lock import FileLock
```

### File Locking

Always use `FileLock` when accessing shared files like `current_tasks.json`:

```python
from slate_core.file_lock import FileLock
import json

with FileLock("current_tasks.json"):
    with open("current_tasks.json", "r") as f:
        tasks = json.load(f)
    # Modify tasks...
    tasks["new_task"] = {"status": "pending"}
    with open("current_tasks.json", "w") as f:
        json.dump(tasks, f, indent=2)
```

### Linting

```bash
# Check with ruff
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .
```

---

## Creating New MCP Tools

MCP (Model Context Protocol) tools enable Claude Code to interact with SLATE services.

### Tool Definition Structure

Tools are defined in `slate/mcp_server.py`:

```python
Tool(
    name="slate_example",
    description="Brief description of what the tool does",
    inputSchema={
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["status", "run", "stop"],
                "description": "Action to perform",
                "default": "status"
            },
            "target": {
                "type": "string",
                "description": "Target for the action"
            }
        },
        "required": ["action"]  # Optional: specify required fields
    }
)
```

### Adding a New Tool

1. **Define the tool in `list_tools()`:**

```python
@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        # ... existing tools ...
        Tool(
            name="slate_new_feature",
            description="Manage the new feature - status, configure, or reset",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["status", "configure", "reset"],
                        "description": "Action to perform",
                        "default": "status"
                    },
                    "config": {
                        "type": "object",
                        "description": "Configuration options (for configure action)"
                    }
                }
            }
        ),
    ]
```

2. **Implement the handler in `call_tool()`:**

```python
@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "slate_new_feature":
        action = arguments.get("action", "status")

        if action == "status":
            result = run_slate_command("slate_new_feature.py", "--status")
        elif action == "configure":
            config = json.dumps(arguments.get("config", {}))
            result = run_slate_command("slate_new_feature.py", "--configure", config)
        elif action == "reset":
            result = run_slate_command("slate_new_feature.py", "--reset")
        else:
            return [TextContent(type="text", text=f"Unknown action: {action}")]

        return [TextContent(
            type="text",
            text=result["stdout"] if result["success"] else f"Error: {result['stderr']}"
        )]
```

3. **Create the backing module:**

```python
# slate/slate_new_feature.py
#!/usr/bin/env python3
# Modified: 2026-02-08T12:00:00Z | Author: Developer | Change: Add new feature module
"""
SLATE New Feature - Description of what it does.
"""

import argparse
import json
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))


def get_status() -> dict:
    """Get current status of the new feature."""
    return {"status": "active", "version": "1.0.0"}


def configure(config: dict) -> dict:
    """Configure the new feature."""
    # Implementation...
    return {"success": True, "applied": config}


def reset() -> dict:
    """Reset to default configuration."""
    return {"success": True, "message": "Reset complete"}


def main():
    parser = argparse.ArgumentParser(description="SLATE New Feature")
    parser.add_argument("--status", action="store_true", help="Show status")
    parser.add_argument("--configure", type=str, help="Apply configuration (JSON)")
    parser.add_argument("--reset", action="store_true", help="Reset to defaults")
    parser.add_argument("--json", action="store_true", help="JSON output")

    args = parser.parse_args()

    if args.status:
        result = get_status()
    elif args.configure:
        config = json.loads(args.configure)
        result = configure(config)
    elif args.reset:
        result = reset()
    else:
        parser.print_help()
        sys.exit(1)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for key, value in result.items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
```

4. **Update `.mcp.json` if needed:**

The MCP server is already configured in `.mcp.json`. New tools are automatically available.

5. **Write tests:**

```python
# tests/test_new_feature.py
import pytest
from slate.slate_new_feature import get_status, configure, reset


class TestNewFeature:
    def test_get_status(self):
        result = get_status()
        assert "status" in result
        assert result["status"] == "active"

    def test_configure(self):
        result = configure({"option": "value"})
        assert result["success"] is True

    def test_reset(self):
        result = reset()
        assert result["success"] is True
```

---

## Adding Slash Commands

Slash commands are markdown files in `.claude/commands/` that define Claude Code interactions.

### Command File Structure

```markdown
---
description: Brief description shown in command list
handoffs:
  - label: Next Step Label
    agent: speckit.next
    prompt: Transition prompt
    send: true
scripts:
  sh: scripts/bash/command-script.sh --json
  ps: scripts/powershell/command-script.ps1 -Json
---

# /command-name

Full description of what the command does.

## Usage
/command-name [options]

## Instructions

Steps Claude should follow when this command is invoked.

```powershell
# Example command to run
.\.venv\Scripts\python.exe slate/some_module.py --action
```

Report the results showing:
1. First thing to report
2. Second thing to report
```

### Creating a New Command

1. **Create the command file:**

```markdown
# .claude/commands/slate-example.md

---
description: Example command demonstrating the pattern
---

# /slate-example

Perform an example action with status reporting.

## Usage
/slate-example [--verbose]

## Instructions

Run the SLATE example command:

```powershell
.\.venv\Scripts\python.exe slate/slate_example.py --status
```

For verbose output:
```powershell
.\.venv\Scripts\python.exe slate/slate_example.py --verbose
```

Report the results showing:
1. Current status
2. Any warnings or issues
3. Recommendations if applicable
```

2. **For commands with scripts:**

```markdown
---
description: Command with automated script execution
scripts:
  sh: scripts/bash/example.sh --json "{ARGS}"
  ps: scripts/powershell/example.ps1 -Json "{ARGS}"
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding.

## Outline

1. Run `{SCRIPT}` from repo root and parse JSON output.
2. Process the results...
3. Report completion.
```

3. **For commands with handoffs:**

```markdown
---
description: Multi-step workflow command
handoffs:
  - label: Continue to Next Step
    agent: slate-next
    prompt: Proceed with the next phase
    send: true
  - label: Go Back
    agent: slate-previous
    prompt: Return to previous step
---
```

### Command Naming Conventions

| Pattern | Example | Purpose |
|---------|---------|---------|
| `slate-<action>` | `slate-status` | Core SLATE operations |
| `slate-<noun>` | `slate-runner` | Resource management |
| `speckit.<phase>` | `speckit.specify` | Spec-Kit workflow |

---

## Contributing to Vendor SDK Integrations

SLATE integrates 5 vendor SDKs through the `vendor/` directory and integration modules in `slate/`.

### Integrated Vendors

| Vendor | Integration File | Purpose |
|--------|------------------|---------|
| openai-agents-python | `slate/vendor_agents_sdk.py` | Agent/Tool/Guardrail abstractions |
| autogen | `slate/vendor_autogen_sdk.py` | Multi-agent conversation framework |
| semantic-kernel | `slate/slate_semantic_kernel.py` | LLM orchestration and skills |
| copilot-sdk | `slate/copilot_sdk_tools.py` | GitHub Copilot integration |
| spec-kit | `slate/slate_spec_kit.py` | Specification-driven development |

### Adding a New Vendor Integration

1. **Add the SDK as a git submodule:**

```bash
git submodule add https://github.com/vendor/sdk.git vendor/sdk-name
```

2. **Create an integration module:**

```python
# slate/vendor_new_sdk.py
#!/usr/bin/env python3
# Modified: 2026-02-08T12:00:00Z | Author: Developer | Change: Add new SDK integration
"""
SLATE New SDK Integration
=========================
Provides type-safe imports from the vendor SDK.
"""

import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).parent.parent.resolve()
VENDOR_SDK_PATH = WORKSPACE_ROOT / "vendor" / "sdk-name" / "src"

# Track availability
SDK_AVAILABLE = False

# Exported types (None if SDK not available)
SomeType = None
AnotherType = None

def _import_sdk():
    """Import SDK using sys.path manipulation."""
    global SDK_AVAILABLE, SomeType, AnotherType

    if not VENDOR_SDK_PATH.exists():
        return False

    # Stash any conflicting modules
    original_path = sys.path[:]
    stashed = {}
    for key in list(sys.modules.keys()):
        if key.startswith("sdk"):
            stashed[key] = sys.modules.pop(key)

    try:
        sys.path.insert(0, str(VENDOR_SDK_PATH))
        from sdk import SomeType as _SomeType, AnotherType as _AnotherType

        SomeType = _SomeType
        AnotherType = _AnotherType
        SDK_AVAILABLE = True
        return True
    except ImportError:
        return False
    finally:
        sys.path[:] = original_path
        sys.modules.update(stashed)


# Import on module load
_import_sdk()
```

3. **Add to vendor integration status:**

Update `slate/vendor_integration.py`:

```python
def check_new_sdk() -> dict[str, Any]:
    """Check new SDK integration."""
    try:
        from slate.vendor_new_sdk import SDK_AVAILABLE, SomeType
        return {
            "name": "new-sdk",
            "available": SDK_AVAILABLE,
            "path": str(WORKSPACE_ROOT / "vendor" / "sdk-name"),
            "types": {"SomeType": SomeType is not None},
            "integration_file": "slate/vendor_new_sdk.py",
        }
    except ImportError as e:
        return {"name": "new-sdk", "available": False, "error": str(e)}


def get_all_vendors() -> list[dict]:
    return [
        check_openai_agents(),
        check_autogen(),
        check_semantic_kernel(),
        check_copilot(),
        check_speckit(),
        check_new_sdk(),  # Add here
    ]
```

4. **Write integration tests:**

```python
# tests/test_vendor_new_sdk.py
import pytest

class TestNewSDKIntegration:
    def test_sdk_available(self):
        from slate.vendor_new_sdk import SDK_AVAILABLE
        assert SDK_AVAILABLE is True

    def test_types_exported(self):
        from slate.vendor_new_sdk import SomeType
        assert SomeType is not None

    def test_create_instance(self):
        from slate.vendor_new_sdk import SomeType
        instance = SomeType()
        assert instance is not None
```

5. **Update .gitmodules:**

```ini
[submodule "vendor/sdk-name"]
    path = vendor/sdk-name
    url = https://github.com/vendor/sdk.git
    branch = main
```

---

## Creating Custom Ollama Models

SLATE uses custom Ollama models optimized for different task types.

### Existing Models

| Model | Base | Parameters | Purpose |
|-------|------|------------|---------|
| slate-coder | mistral-nemo | 12.2B | Code generation, review |
| slate-fast | llama3.2:3b | 3B | Classification, triage |
| slate-planner | mistral:latest | 7.2B | Planning, analysis |

### Creating a New Model

1. **Create Modelfile:**

```dockerfile
# modelfiles/slate-reviewer.modelfile
FROM mistral-nemo

# Lower temperature for consistent analysis
PARAMETER temperature 0.2
PARAMETER top_p 0.85
PARAMETER top_k 35
PARAMETER num_predict 2048
PARAMETER repeat_penalty 1.15
PARAMETER num_ctx 8192

SYSTEM """
You are SLATE-REVIEWER, a specialized code review agent for the S.L.A.T.E. project.

IDENTITY:
- You perform thorough code reviews focusing on security, performance, and maintainability
- You know SLATE architecture (slate/, agents/, slate_core/ modules)
- You follow SLATE conventions: localhost bindings, type hints, modification timestamps

REVIEW FOCUS:
1. Security: No 0.0.0.0 bindings, no hardcoded secrets, ActionGuard compliance
2. Performance: Efficient algorithms, proper caching, GPU utilization
3. Maintainability: Clear naming, documentation, test coverage
4. Conventions: Type hints, Google docstrings, modification timestamps

OUTPUT FORMAT:
Provide structured review with severity levels: CRITICAL, WARNING, INFO, SUGGESTION
"""
```

2. **Build the model:**

```bash
ollama create slate-reviewer -f modelfiles/slate-reviewer.modelfile
```

3. **Test the model:**

```bash
ollama run slate-reviewer "Review this Python function: def process(x): return x*2"
```

4. **Add to unified backend:**

Update `slate/unified_ai_backend.py`:

```python
TASK_ROUTING = {
    # ... existing routes ...
    "code_review": "slate-reviewer",  # Add new model
}

MODEL_CONFIGS = {
    # ... existing configs ...
    "slate-reviewer": {
        "base": "mistral-nemo",
        "parameters": "12.2B",
        "gpu": "auto",
        "context": 8192,
        "use_case": "Code review and security analysis",
    },
}
```

5. **Add to GPU manager:**

Update model preloading in `slate/slate_gpu_manager.py`:

```python
MODELS_TO_PRELOAD = [
    "slate-coder",
    "slate-fast",
    "slate-planner",
    "slate-reviewer",  # Add here
]
```

### Model Configuration Reference

| Parameter | Purpose | Typical Range |
|-----------|---------|---------------|
| temperature | Output randomness | 0.1-0.4 for code, 0.7-1.0 for creative |
| top_p | Nucleus sampling | 0.8-0.95 |
| top_k | Vocabulary diversity | 30-50 |
| num_predict | Max output tokens | 512-4096 |
| repeat_penalty | Reduce repetition | 1.05-1.2 |
| num_ctx | Context window | 4096-8192 |

---

## Debug and Development Modes

### Enable Debug Logging

```python
import logging

# Set global log level
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Or per-module
logging.getLogger("slate.mcp_server").setLevel(logging.DEBUG)
```

### Check System State

```bash
# Full system status (auto-detects everything)
python slate/slate_status.py --quick

# JSON output for automation
python slate/slate_status.py --json

# Check specific integration
python slate/slate_runtime.py --check ollama
python slate/slate_runtime.py --check pytorch
python slate/slate_runtime.py --check-all

# Workflow health (stale tasks, abandoned, duplicates)
python slate/slate_workflow_manager.py --status

# GPU status and memory
python slate/slate_gpu_manager.py --status

# Vendor SDK availability
python slate/vendor_integration.py
python slate/vendor_integration.py --test  # Run integration tests
```

### Common Debug Locations

| Location | Contents |
|----------|----------|
| `current_tasks.json` | Task queue state |
| `.slate_errors/` | Error logs with context |
| `slate_cache/` | LLM response cache |
| `.slate_changes/` | Detected code changes |
| `.slate_tech_tree/tech_tree.json` | Feature completion state |

### Development Environment Variables

```bash
# Enable verbose MCP logging
export SLATE_MCP_DEBUG=1

# Force specific GPU
export CUDA_VISIBLE_DEVICES=0

# Skip ActionGuard (DANGEROUS - dev only)
export SLATE_ACTIONGUARD=disabled

# Use development Ollama endpoint
export OLLAMA_HOST=http://localhost:11434
```

### Interactive Debugging

```python
# Add breakpoints in code
import pdb; pdb.set_trace()

# Or use IPython for richer debugging
from IPython import embed; embed()

# Remote debugging with debugpy (VS Code)
import debugpy
debugpy.listen(5678)
debugpy.wait_for_client()
```

---

## Running Local Tests

### Quick Test Commands

```bash
# All tests
python -m pytest tests/ -v

# Fast smoke test (unit tests only)
python -m pytest tests/unit/ -v --tb=short

# Single test file
python -m pytest tests/test_greeting.py -v

# Pattern matching
python -m pytest tests/ -k "test_greet" -v

# Stop on first failure
python -m pytest tests/ -x

# Show print statements
python -m pytest tests/ -s

# Parallel execution
python -m pytest tests/ -n auto
```

### Coverage Analysis

```bash
# Run with coverage
python -m pytest tests/ --cov=slate --cov=slate_core -v

# Generate HTML report
python -m pytest tests/ --cov=slate --cov-report=html
# Open htmlcov/index.html in browser

# Fail if coverage below threshold
python -m pytest tests/ --cov=slate --cov-fail-under=50
```

### Test Categories

```bash
# Run only unit tests (no external dependencies)
python -m pytest tests/unit/ -v

# Run integration tests (requires Ollama, etc.)
python -m pytest tests/integration/ -v

# Run contract tests
python -m pytest tests/contract/ -v

# Skip slow tests
python -m pytest tests/ -v -m "not slow"

# Run only GPU tests
python -m pytest tests/ -v -m gpu
```

### Pre-Commit Checks

```bash
# Run before committing
ruff check .
python -m pytest tests/unit/ -v --tb=short
python slate/slate_status.py --quick
```

### CI Test Commands

These are run by GitHub Actions:

```bash
# Smoke test (fast, always runs)
python -m pytest tests/ -x -v --tb=short -m "not slow"

# Full test suite (nightly)
python -m pytest tests/ -v --cov=slate --cov-report=xml

# Security scan
python slate/action_guard.py --scan
python slate/sdk_source_guard.py --check-requirements
```

---

## Container and Kubernetes Development

SLATE runs as a **local cloud** using Kubernetes. Local development improves the codebase, then builds the release image that K8s deploys.

### Development Workflow (Local Cloud)

```
1. Edit code locally (slate/, agents/, etc.)
2. Build release image:  docker build -t slate:local .
3. Deploy to K8s:        kubectl apply -k k8s/overlays/local/
4. Verify in VS Code:    Kubernetes sidebar -> slate namespace -> pods
5. View logs:            Right-click pod -> Logs
6. Port forward:         Right-click service -> Port Forward
7. Iterate:              Repeat from step 1
```

### Required VS Code Extensions

| Extension | ID | Purpose |
|-----------|-----|---------|
| Docker | `ms-azuretools.vscode-docker` | Build, manage, inspect containers |
| Kubernetes | `ms-kubernetes-tools.vscode-kubernetes-tools` | K8s cluster management |
| Helm Intellisense | `tim-koehler.helm-intellisense` | Helm chart editing |
| YAML | `redhat.vscode-yaml` | K8s schema validation |

### K8s CLI Commands

```bash
# Cluster overview
python slate/slate_k8s_deploy.py --status

# Deploy manifests
python slate/slate_k8s_deploy.py --deploy

# Health check
python slate/slate_k8s_deploy.py --health

# Component logs
python slate/slate_k8s_deploy.py --logs dashboard

# Remove from cluster
python slate/slate_k8s_deploy.py --teardown

# Port forwarding
kubectl port-forward -n slate svc/slate-dashboard-svc 8080:8080
```

### Docker Compose (Alternative)

```bash
# Development mode (with hot reload)
docker-compose -f docker-compose.dev.yml up

# Production mode (detached)
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f slate-dashboard
```

### Building Images

```bash
# Build main image
docker build -t slate:local .

# Build with specific target
docker build --target development -t slate:dev .

# Push to registry (if configured)
docker tag slate:local registry.example.com/slate:latest
docker push registry.example.com/slate:latest
```

---

## Git Workflow

### Branch Naming

```
feature/short-description
bugfix/issue-number-description
refactor/component-name
docs/what-is-being-documented
spec/NNN-feature-name
```

### Commit Messages

Follow conventional commits:

```
feat: Add new task routing algorithm
fix: Resolve GPU memory leak in batch processing
docs: Update CLI reference documentation
refactor: Simplify agent dispatcher logic
test: Add unit tests for greeting module
chore: Update dependencies
```

### Pull Request Process

1. Create feature branch from `main`
2. Make changes with tests (TDD)
3. Run full test suite
4. Update documentation if needed
5. Create PR with description
6. Address review feedback
7. Squash and merge

---

## Security Guidelines

### Never Do

- Bind servers to `0.0.0.0` (use `127.0.0.1`)
- Call external paid APIs (only free local LLMs)
- Store secrets in code
- Disable ActionGuard in production
- Commit `.env` or credential files

### Always Do

- Use localhost binding for all services
- Validate all inputs
- Use file locks for shared state
- Follow CSP guidelines
- Run `action_guard.py --scan` before commits

---

## Getting Help

- Check [Troubleshooting](Troubleshooting) for common issues
- Review existing specs in `specs/`
- Read the constitution at `.specify/memory/constitution.md`
- Check CLAUDE.md for current guidelines
- Run `/slate-help` for command reference

---

## Next Steps

- [Troubleshooting](Troubleshooting) - Common issues and solutions
- [API Reference](API-Reference) - Module documentation
- [Architecture](Architecture) - System design
- [Security](Security) - Security architecture
