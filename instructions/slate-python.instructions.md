---
name: slate-python
description: 'Coding standards and best practices for SLATE Python modules'
applyTo: 'slate/**/*.py, agents/**/*.py, slate_core/**/*.py, tests/**/*.py'
tags: [python, coding-standards, slate]
---

# SLATE Python Coding Standards

These instructions apply to all Python files in the SLATE codebase.

## Code Modification Header

**Every code edit MUST include a timestamp + author comment:**

```python
# Modified: YYYY-MM-DDTHH:MM:SSZ | Author: COPILOT | Change: description
```

Place this comment at the top of the file after the docstring, or near the modified code block.

## Type Hints (Required)

All functions must include type hints:

```python
def process_task(task_id: str, options: dict[str, Any] | None = None) -> bool:
    """Process a task with optional configuration."""
    ...
```

Use `Annotated` for tool parameters:

```python
from typing import Annotated

def slate_status(
    format: Annotated[str, "Output format: quick, json, full"] = "quick"
) -> dict:
    ...
```

## Docstrings (Google Style)

Use Google-style docstrings:

```python
def detect_gpus() -> list[GPUInfo]:
    """Detect all NVIDIA GPUs in the system.

    Scans for GPUs using nvidia-smi and returns detailed information
    including compute capability, memory, and architecture.

    Returns:
        List of GPUInfo objects for each detected GPU.

    Raises:
        GPUDetectionError: If nvidia-smi is not available.
    """
    ...
```

## Imports

Add `WORKSPACE_ROOT` to `sys.path` when importing cross-module:

```python
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))
```

## File Operations

Always use `encoding='utf-8'` on Windows:

```python
with open(path, "r", encoding="utf-8") as f:
    content = f.read()
```

Use FileLock for shared resources like `current_tasks.json`:

```python
from slate_core.file_lock import FileLock

with FileLock("current_tasks.json"):
    # Safe to read/write
    ...
```

## Network Bindings

**NEVER bind to `0.0.0.0`** — always use `127.0.0.1`:

```python
# CORRECT
app.run(host="127.0.0.1", port=8080)

# WRONG - ActionGuard will block this
app.run(host="0.0.0.0", port=8080)
```

## HTTP Requests

Never use `curl.exe` — it freezes on this system. Use Python:

```python
import urllib.request

with urllib.request.urlopen(url) as response:
    data = json.loads(response.read())
```

## Blocked Patterns (ActionGuard)

These patterns are blocked and will fail security checks:

- `eval(` — Dynamic code execution
- `exec(os` — OS command injection
- `rm -rf /` — Destructive commands
- `base64.b64decode` — Obfuscation attempts
- `subprocess.call(shell=True)` — Shell injection risk

## Testing

Tests must follow the test-driven development pattern:

```python
# tests/test_feature.py

def test_feature_happy_path():
    """Test expected behavior."""
    result = feature_function(valid_input)
    assert result.success is True

def test_feature_error_handling():
    """Test error conditions."""
    with pytest.raises(ExpectedError):
        feature_function(invalid_input)
```

## Error Handling

Use specific exceptions, not bare `except`:

```python
try:
    result = risky_operation()
except FileNotFoundError:
    logger.warning("File not found, using defaults")
    result = defaults
except PermissionError as e:
    raise SLATEConfigError(f"Cannot access file: {e}") from e
```
