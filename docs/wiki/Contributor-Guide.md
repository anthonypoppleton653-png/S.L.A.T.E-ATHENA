# Contributor Guide

Comprehensive guide for contributing to SLATE as an external user or maintainer.

**Last Updated**: 2026-02-08
**Version**: 2.0.0

---

## Table of Contents

1. [Repository Structure](#repository-structure)
2. [Getting Started](#getting-started)
3. [Dual-Repository System](#dual-repository-system)
4. [Branch Naming Conventions](#branch-naming-conventions)
5. [Commit Message Format](#commit-message-format)
6. [Pull Request Requirements](#pull-request-requirements)
7. [Security Requirements](#security-requirements)
8. [Testing Requirements](#testing-requirements)
9. [Code Review Process](#code-review-process)
10. [Documentation Requirements](#documentation-requirements)
11. [Working with Specs](#working-with-specs)
12. [Community Guidelines](#community-guidelines)
13. [Troubleshooting](#troubleshooting)

---

## Repository Structure

SLATE uses a dual-repository model for development and distribution:

```
SLATE-BETA (Development)     SLATE (Public)           User Forks
         |                         |                       |
         |    sync-to-public       |                       |
         +----------------------->>|                       |
         |                         |      fork             |
         |                         +----------------------->>
         |                         |                       |
         |                         |      contribute       |
         |                         |<<---------------------+
         |                         |                       |
```

| Repository | Purpose | Access |
|------------|---------|--------|
| **S.L.A.T.E.-BETA** | Development repo | Maintainers only |
| **S.L.A.T.E.** | Public installer | Everyone |
| **Your Fork** | Your personal SLATE | You |

### Key Directories

```
slate/             # Core SLATE engine modules
slate_core/        # Shared infrastructure (locks, memory, GPU scheduler)
agents/            # Dashboard server and legacy agent code
specs/             # Active specifications (draft -> complete lifecycle)
tests/             # Test suite (pytest)
.claude/           # Claude Code configuration
  commands/        # Slash commands (/slate-*)
  behaviors/       # Behavior profiles
.claude-plugin/    # Plugin manifest
skills/            # Agent skills (skills/*/SKILL.md)
.github/           # GitHub workflows and configuration
docs/              # Documentation and wiki
k8s/               # Kubernetes deployment manifests
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Git
- (Optional) NVIDIA GPU with CUDA support
- (Optional) Docker/Kubernetes for containerized deployment

### 1. Fork the Public Repository

Fork from: https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E

### 2. Clone Your Fork

```bash
git clone https://github.com/YOUR-USERNAME/S.L.A.T.E.git
cd S.L.A.T.E
```

### 3. Set Up Remotes

```bash
# Add upstream (public SLATE)
git remote add upstream https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E.git

# Verify remotes
git remote -v
# origin    https://github.com/YOUR-USERNAME/S.L.A.T.E.git (fetch)
# origin    https://github.com/YOUR-USERNAME/S.L.A.T.E.git (push)
# upstream  https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E.git (fetch)
```

### 4. Initialize Your SLATE Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.\.venv\Scripts\activate

# Activate (Linux/macOS)
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Initialize fork manager
python slate/slate_fork_manager.py --init --name "Your Name" --email "your@email.com"

# Set up your fork URL
python slate/slate_fork_manager.py --setup-fork https://github.com/YOUR-USERNAME/S.L.A.T.E.git
```

### 5. Verify Installation

```bash
# Full system status (auto-detects GPU, services)
python slate/slate_status.py --quick

# Run tests to verify setup
python -m pytest tests/ -v --maxfail=3
```

---

## Dual-Repository System

SLATE uses a dual-repository model to separate development from the public release.

### For Maintainers (BETA -> SLATE)

```bash
# Check remotes
git remote -v
# origin  https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E.git
# beta    https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E-BETA.git

# Development Workflow
git checkout -b feature/my-feature

# Sync BETA with SLATE main (get latest)
git fetch origin
git merge origin/main

# Push to BETA
git push beta HEAD:main

# Contribute to SLATE main
# Option 1: Run contribute-to-main.yml workflow on BETA
# Option 2: Direct push (if you have access)
git push origin HEAD:main
```

### Required Setup for Maintainers

1. **MAIN_REPO_TOKEN** secret on BETA repo
   - Settings -> Secrets -> Actions -> Add `MAIN_REPO_TOKEN`
   - Use a PAT with `repo` and `workflow` scope

2. **GitHub CLI with workflow scope**
   ```bash
   gh auth login --scopes workflow
   ```

### For External Contributors (Fork -> SLATE)

```bash
# Always sync before starting work
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch
git checkout -b feature/your-feature-name

# Make changes, commit, push to your fork
git push origin feature/your-feature-name

# Create PR via GitHub UI or CLI
gh pr create --title "Add feature X" --body "Description of changes"
```

---

## Branch Naming Conventions

Use descriptive branch names with a prefix indicating the type of change:

| Prefix | Usage | Example |
|--------|-------|---------|
| `feature/` | New features or enhancements | `feature/gpu-load-balancing` |
| `fix/` | Bug fixes | `fix/stale-task-cleanup` |
| `docs/` | Documentation updates | `docs/contributor-guide` |
| `refactor/` | Code refactoring (no behavior change) | `refactor/action-guard-patterns` |
| `test/` | Test additions or improvements | `test/sdk-integration-coverage` |
| `chore/` | Maintenance tasks | `chore/update-dependencies` |
| `spec/` | Specification changes | `spec/017-claude-agent-sdk` |
| `hotfix/` | Urgent production fixes | `hotfix/security-patch` |

### Branch Name Rules

1. Use lowercase with hyphens (kebab-case)
2. Keep names concise but descriptive
3. Include issue number if applicable: `fix/123-memory-leak`
4. Avoid special characters except hyphens

### Examples

```bash
# Good branch names
git checkout -b feature/dual-gpu-inference
git checkout -b fix/421-workflow-timeout
git checkout -b docs/api-reference-update
git checkout -b spec/020-custom-slate-models

# Poor branch names (avoid these)
git checkout -b my-branch          # Not descriptive
git checkout -b Feature_NewThing   # Wrong case, underscore
git checkout -b fix                # Too generic
```

---

## Commit Message Format

SLATE follows a structured commit message format to maintain clear history.

### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer]
Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

### Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting, no code change |
| `refactor` | Code restructuring |
| `test` | Adding/updating tests |
| `chore` | Maintenance, dependencies |
| `perf` | Performance improvement |
| `ci` | CI/CD changes |
| `build` | Build system changes |

### Scopes

Common scopes include:
- `slate` - Core SLATE modules
- `dashboard` - Dashboard server
- `workflow` - Task workflow system
- `gpu` - GPU management
- `k8s` - Kubernetes deployment
- `mcp` - MCP server/tools
- `sdk` - SDK integrations
- `docs` - Documentation
- `tests` - Test suite

### Examples

```bash
# Feature
git commit -m "feat(gpu): Add dual-GPU load balancing for Ollama

Implements round-robin distribution of inference tasks across
GPU 0 and GPU 1 with affinity-based scheduling.

Closes #234

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"

# Bug fix
git commit -m "fix(workflow): Reset stale tasks after 4h timeout

Tasks stuck in in-progress state for over 4 hours are now
automatically reset to pending status.

Fixes #456

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"

# Documentation
git commit -m "docs(wiki): Update contributor guide with commit format

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"

# Chore
git commit -m "chore(deps): Update FastAPI to 0.109.0

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

### Co-Authored-By Requirement

All commits that involve AI assistance **MUST** include the Co-Authored-By footer:

```
Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

This ensures transparency about AI involvement in contributions.

---

## Pull Request Requirements

### PR Checklist

Before submitting a PR, verify all items:

- [ ] Branch is up-to-date with `upstream/main`
- [ ] All tests pass locally (`python -m pytest tests/ -v`)
- [ ] Lint passes (`ruff check .`)
- [ ] Validation passes (`python slate/slate_fork_manager.py --validate`)
- [ ] No modifications to protected files (see below)
- [ ] Code binds to `127.0.0.1` only (never `0.0.0.0`)
- [ ] No secrets or credentials in code
- [ ] Documentation updated if needed
- [ ] Commit messages follow format

### PR Title Format

```
<type>(<scope>): <short description>
```

Examples:
- `feat(dashboard): Add real-time GPU metrics display`
- `fix(workflow): Handle concurrent task updates`
- `docs(wiki): Add API reference section`

### PR Description Template

```markdown
## Summary
<!-- 1-3 bullet points describing the change -->
- Added X feature
- Fixed Y bug
- Updated Z documentation

## Motivation
<!-- Why is this change needed? Link to issue if applicable -->
Resolves #123

## Changes
<!-- Detailed list of changes -->
- Modified `slate/module.py` to add...
- Updated tests in `tests/test_module.py`
- Added documentation for new feature

## Test Plan
<!-- How was this tested? -->
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing performed
- [ ] Tested on Windows/Linux/macOS

## Breaking Changes
<!-- Any breaking changes? How to migrate? -->
None / [Describe breaking changes and migration path]

## Screenshots
<!-- If UI changes, include before/after screenshots -->

---
Generated with Claude Code
```

### Protected Files

These files **CANNOT** be modified by external contributors:

| File | Reason |
|------|--------|
| `.github/workflows/*` | Security-critical automation |
| `.github/CODEOWNERS` | Access control |
| `slate/action_guard.py` | Security enforcement |
| `slate/sdk_source_guard.py` | Package validation |
| `pyproject.toml` | Build configuration (maintainer approval required) |
| `requirements.txt` | Dependencies (security review required) |

If you need changes to protected files, open an issue first to discuss.

### PR Labels

Labels are automatically applied based on validation:

| Label | Meaning |
|-------|---------|
| `external-contributor` | PR from a fork |
| `validation-passed` | All automated checks passed |
| `needs-fixes` | Issues found, requires changes |
| `security-review` | Needs security team review |
| `breaking-change` | Contains breaking changes |
| `ready-for-review` | Ready for maintainer review |

---

## Security Requirements

SLATE enforces strict security requirements through automated validation.

### SDK Source Guard

All packages must come from trusted publishers:

| Trusted Source | Examples |
|----------------|----------|
| Microsoft | azure-*, onnxruntime |
| NVIDIA | nvidia-cuda-*, triton |
| Anthropic | anthropic SDK |
| Meta/Facebook | torch, torchvision |
| Google | tensorflow, jax |
| Hugging Face | transformers, datasets |
| Python Foundation | pip, setuptools |

```bash
# Check SDK security status
python slate/sdk_source_guard.py --report

# Validate a specific package
python slate/sdk_source_guard.py --validate "some-package"

# Check all requirements.txt packages
python slate/sdk_source_guard.py --check-requirements
```

**Blocked Sources:**
- Unknown PyPI publishers
- Untrusted GitHub organizations
- Known typosquatting packages
- Suspicious naming patterns

### ActionGuard

ActionGuard validates all operations before execution:

```python
# Blocked patterns
BLOCKED = [
    r'rm\s+-rf\s+/',           # Recursive delete root
    r'0\.0\.0\.0',             # External network binding
    r'eval\s*\(',              # Dynamic code execution
    r'exec\s*\(.*input',       # Unsafe execution
    r'api\.openai\.com',       # External paid APIs
    r'api\.anthropic\.com',    # External paid APIs
]
```

### Network Binding

**CRITICAL**: All servers must bind to `127.0.0.1` only.

```python
# CORRECT
app.run(host="127.0.0.1", port=8080)

# BLOCKED (ActionGuard will reject)
app.run(host="0.0.0.0", port=8080)
```

### Credential Protection

Never commit:
- `.env` files
- API keys or tokens
- Passwords
- `credentials.json`
- Private keys (`.pem`, `.key`)
- OAuth secrets

The PII scanner will flag these in PRs.

### Validation Commands

```bash
# Full fork validation
python slate/slate_fork_manager.py --validate

# Security-specific checks
python slate/action_guard.py --check-file slate/your_module.py

# SDK source validation
python slate/sdk_source_guard.py --check-requirements
```

---

## Testing Requirements

SLATE follows Test-Driven Development (TDD) as mandated by the Constitution.

### TDD Cycle

```
1. WRITE TEST -> failing test defining expected behavior
2. RUN TEST   -> verify it fails (red)
3. IMPLEMENT  -> minimum code to pass
4. RUN TEST   -> verify it passes (green)
5. REFACTOR   -> clean up while keeping tests green
```

### Test Coverage Requirements

| Module | Minimum Coverage |
|--------|-----------------|
| `slate/` | 50%+ |
| `slate_core/` | 50%+ |
| Critical security paths | 100% |

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=slate --cov-report=term-missing

# Run specific test file
python -m pytest tests/test_slate_status.py -v

# Run specific test
python -m pytest tests/test_slate_status.py::test_gpu_detection -v

# Run tests matching pattern
python -m pytest tests/ -k "workflow" -v

# Stop on first failure
python -m pytest tests/ -x

# Parallel execution
python -m pytest tests/ -n auto
```

### Test File Structure

```
tests/
  conftest.py              # Shared fixtures
  test_slate_status.py     # Status module tests
  test_action_guard.py     # Security tests
  test_workflow_manager.py # Workflow tests
  test_integration/        # Integration tests
    test_mcp_server.py
    test_k8s_deploy.py
```

### Writing Tests

```python
"""Tests for slate/my_module.py"""
import pytest
from slate.my_module import MyClass

class TestMyClass:
    """Test cases for MyClass."""

    def test_initialization(self):
        """Test that MyClass initializes correctly."""
        obj = MyClass()
        assert obj is not None
        assert obj.status == "initialized"

    def test_process_with_valid_input(self):
        """Test processing with valid input returns expected result."""
        obj = MyClass()
        result = obj.process("valid input")
        assert result.success is True
        assert "processed" in result.message

    def test_process_with_invalid_input_raises(self):
        """Test processing with invalid input raises ValueError."""
        obj = MyClass()
        with pytest.raises(ValueError, match="Invalid input"):
            obj.process("")

    @pytest.mark.parametrize("input_val,expected", [
        ("a", "result_a"),
        ("b", "result_b"),
        ("c", "result_c"),
    ])
    def test_process_parameterized(self, input_val, expected):
        """Test processing with various inputs."""
        obj = MyClass()
        assert obj.process(input_val) == expected
```

### Fixtures

Use fixtures from `conftest.py`:

```python
# tests/conftest.py
import pytest
from pathlib import Path

@pytest.fixture
def temp_workspace(tmp_path):
    """Create a temporary SLATE workspace."""
    workspace = tmp_path / "slate_test"
    workspace.mkdir()
    (workspace / "current_tasks.json").write_text("[]")
    return workspace

@pytest.fixture
def mock_ollama(mocker):
    """Mock Ollama service responses."""
    return mocker.patch("slate.foundry_local.OllamaClient")
```

---

## Code Review Process

### Review Stages

1. **Automated Validation** (immediate)
   - Fork validation workflow runs
   - Security scans check for dangerous patterns
   - SLATE prerequisites verified
   - Tests executed

2. **Bot Comment** (automatic)
   - First-time contributors get a welcome message
   - Validation results posted as comment
   - Labels applied based on results

3. **Maintainer Review** (human)
   - Code quality assessment
   - Architecture alignment
   - Security review for sensitive paths
   - Documentation check

4. **Approval & Merge**
   - At least one maintainer approval required
   - All checks must pass
   - No unresolved conversations

### CODEOWNERS

Different paths require different reviewers:

| Path | Review Team |
|------|-------------|
| `/slate/` | @SynchronizedLivingArchitecture/slate-maintainers |
| `/slate/action_guard.py` | @SynchronizedLivingArchitecture/slate-security |
| `/slate/sdk_source_guard.py` | @SynchronizedLivingArchitecture/slate-security |
| `/.github/workflows/` | @SynchronizedLivingArchitecture/slate-security |
| `/docs/` | @SynchronizedLivingArchitecture/slate-docs |
| `/specs/` | @SynchronizedLivingArchitecture/slate-maintainers |

### Review Criteria

Reviewers check for:

1. **Correctness** - Does the code do what it claims?
2. **Security** - Any vulnerabilities introduced?
3. **Performance** - Any unnecessary overhead?
4. **Style** - Follows SLATE coding conventions?
5. **Testing** - Adequate test coverage?
6. **Documentation** - Code comments and docs updated?
7. **Architecture** - Aligns with SLATE patterns?

### Responding to Feedback

```bash
# Make requested changes
git add .
git commit -m "fix(scope): Address review feedback

- Fixed issue X
- Updated test Y
- Clarified documentation Z

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"

# Push to update PR
git push origin feature/my-feature
```

---

## Documentation Requirements

### Code Documentation

#### Python Docstrings

Use Google-style docstrings:

```python
def process_task(task_id: str, options: Dict[str, Any]) -> TaskResult:
    """Process a task with the given options.

    Validates the task, executes it through the workflow system,
    and returns the result with status information.

    Args:
        task_id: Unique identifier for the task.
        options: Configuration options including:
            - timeout: Maximum execution time in seconds.
            - retry: Number of retry attempts on failure.
            - priority: Task priority (1-10).

    Returns:
        TaskResult with status, output, and timing information.

    Raises:
        TaskNotFoundError: If task_id doesn't exist.
        ValidationError: If options are invalid.
        TimeoutError: If task exceeds timeout.

    Example:
        >>> result = process_task("task-123", {"timeout": 60})
        >>> print(result.status)
        'completed'
    """
```

#### Type Hints

Type hints are **required** for all functions:

```python
from typing import Dict, List, Optional, Any, Annotated
from pathlib import Path

def load_config(
    config_path: Path,
    defaults: Optional[Dict[str, Any]] = None,
    strict: bool = True,
) -> Dict[str, Any]:
    """Load configuration from file."""
    ...

def validate_items(
    items: List[Annotated[str, "Item identifier"]],
) -> List[bool]:
    """Validate a list of items."""
    ...
```

### Module Documentation

Each module should have a docstring:

```python
"""SLATE Workflow Manager.

This module provides task workflow management including:
- Task queue operations
- Stale task detection and cleanup
- Concurrent task enforcement
- Duplicate detection

Example:
    from slate.slate_workflow_manager import WorkflowManager

    manager = WorkflowManager()
    status = manager.get_status()
    manager.cleanup_stale_tasks()
"""
```

### Wiki Documentation

Update wiki pages when:
- Adding new features
- Changing existing behavior
- Adding new commands or tools
- Modifying configuration options

Wiki location: `docs/wiki/`

### Updating Existing Docs

1. Find the relevant file in `docs/wiki/`
2. Update content while preserving structure
3. Update any version numbers or dates
4. Add to Table of Contents if adding sections
5. Cross-reference related pages

---

## Working with Specs

Specifications define SLATE features before implementation.

### Spec Lifecycle

```
draft -> specified -> planned -> tasked -> implementing -> complete
```

| Status | Meaning |
|--------|---------|
| `draft` | Initial idea, incomplete |
| `specified` | Complete specification |
| `planned` | Approved for implementation |
| `tasked` | Tasks created in queue |
| `implementing` | Active development |
| `complete` | Fully implemented |

### Spec File Structure

```
specs/
  NNN-spec-name/
    spec.md       # Main specification
    diagrams/     # Architecture diagrams
    examples/     # Code examples
    tests/        # Spec-specific tests
```

### Creating a New Spec

1. **Choose Spec Number**
   ```bash
   # Find next available number
   ls specs/ | sort -n | tail -1
   # e.g., if last is 020, use 021
   ```

2. **Create Spec Directory**
   ```bash
   mkdir specs/021-your-spec-name
   ```

3. **Create spec.md**
   ```markdown
   # Specification: Your Feature Name

   **Spec ID**: 021-your-spec-name
   **Status**: draft
   **Created**: 2026-02-08
   **Author**: Your Name
   **Depends On**: 007-slate-design-system

   ## Overview

   Brief description of what this spec defines.

   ## Problem Statement

   What problem does this solve?

   ## Architecture

   ### High-Level Design

   ```
   [ASCII diagram]
   ```

   ## Core Components

   ### Component 1

   Description and interface.

   ## Implementation Plan

   1. Phase 1: ...
   2. Phase 2: ...

   ## Success Metrics

   | Metric | Target |
   |--------|--------|
   | ... | ... |

   ## References

   - Related specs
   - External documentation
   ```

4. **Submit for Review**
   ```bash
   git checkout -b spec/021-your-spec-name
   git add specs/021-your-spec-name/
   git commit -m "spec(021): Add your-spec-name specification

   Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
   git push origin spec/021-your-spec-name
   ```

### Updating Existing Specs

1. Update the `spec.md` file
2. Update the `Status` field if lifecycle changed
3. Add modification note at top:
   ```markdown
   <!-- Modified: 2026-02-08 | Author: Your Name | Change: Description -->
   ```

### Spec Examples

See existing specs for patterns:
- `specs/017-claude-agent-sdk/spec.md` - SDK integration
- `specs/012-watchmaker-3d-dashboard/spec.md` - UI design
- `specs/016-multi-runner-system/spec.md` - Infrastructure

---

## Community Guidelines

### Code of Conduct

1. **Be Respectful** - Treat all contributors with respect
2. **Be Constructive** - Provide helpful feedback
3. **Be Patient** - Not everyone has the same experience level
4. **Be Inclusive** - Welcome diverse perspectives

### Communication Channels

| Channel | Purpose |
|---------|---------|
| GitHub Issues | Bug reports, feature requests |
| GitHub Discussions | Questions, ideas, community |
| Pull Requests | Code contributions |

### Issue Templates

When creating issues:

**Bug Report:**
```markdown
## Bug Description
What happened?

## Expected Behavior
What should happen?

## Steps to Reproduce
1. ...
2. ...

## Environment
- OS: Windows 11 / Ubuntu 22.04 / macOS 14
- Python: 3.11.x
- GPU: RTX 5070 Ti (if applicable)

## Logs
```
Paste relevant logs
```
```

**Feature Request:**
```markdown
## Feature Description
What feature do you want?

## Use Case
Why do you need this?

## Proposed Solution
How would you implement it?

## Alternatives Considered
What other approaches did you consider?
```

### Discussion Categories

| Category | Routing |
|----------|---------|
| Announcements | Informational only |
| Ideas | Routes to ROADMAP board |
| Q&A | Monitored for response time |
| Show and Tell | Community showcase |
| General | Community discussion |

### Recognition

Active contributors may be:
- Added to CONTRIBUTORS.md
- Invited to maintainer team
- Featured in release notes

---

## Troubleshooting

### Common Issues

#### "Fork validation failed"

```bash
# Run locally to see errors
python slate/slate_fork_manager.py --validate

# Check specific validation
python slate/slate_fork_manager.py --check-prerequisites
```

#### "Protected file modified"

You cannot modify security-critical files. Revert those changes:

```bash
git checkout upstream/main -- .github/workflows/
git checkout upstream/main -- slate/action_guard.py
```

#### "Merge conflicts"

```bash
# Fetch latest
git fetch upstream

# Rebase your branch
git rebase upstream/main

# Resolve conflicts, then continue
git rebase --continue

# If things go wrong, abort and start over
git rebase --abort
```

#### "Tests failing on CI but passing locally"

```bash
# Ensure you have latest dependencies
pip install -e ".[dev]" --upgrade

# Run with same settings as CI
python -m pytest tests/ -v --tb=short

# Check if test requires specific environment
# (GPU, services, etc.)
```

#### "ActionGuard blocked my command"

```bash
# Check what pattern was matched
python -c "
from slate.action_guard import ActionGuard
guard = ActionGuard()
result = guard.validate_command('your command here')
print(f'Allowed: {result.allowed}')
print(f'Reason: {result.reason}')
"
```

#### "SDK Source Guard rejected package"

```bash
# Check package publisher
python slate/sdk_source_guard.py --validate "package-name"

# If legitimate, open an issue requesting allowlist addition
```

### Getting Help

1. **Search existing issues** - Your question may be answered
2. **Check the wiki** - Documentation may help
3. **Open a discussion** - For questions and ideas
4. **Open an issue** - For bugs and feature requests

### Useful Commands

```bash
# Full system status
python slate/slate_status.py --quick

# Workflow health
python slate/slate_workflow_manager.py --status

# Validate your changes
python slate/slate_fork_manager.py --validate

# Run tests
python -m pytest tests/ -v

# Lint check
ruff check .

# Format code
ruff format .
```

---

## Your SLATE as a Personal Development Environment

Your fork isn't just for contributing - it's your personal SLATE installation:

```
Your Fork (S.L.A.T.E.)
  +-- Your customizations
  +-- Your agents
  +-- Your tasks
  +-- Syncs with upstream for updates
```

### Keeping Your Fork Updated

```bash
# Fetch upstream changes
git fetch upstream

# Merge into your main branch
git checkout main
git merge upstream/main

# Push to your fork
git push origin main
```

### Personal Customizations

You can customize your SLATE without contributing back:

- Add personal agents to `agents/`
- Customize `CLAUDE.md` for your workflow
- Add project-specific specs to `specs/`

Just keep these on branches that you don't PR upstream.

---

## Feedback Loop Vision

The ultimate goal is a feedback loop:

```
Upstream SLATE
     |
     +--> User A's SLATE --> Improvements --+
     |                                       |
     +--> User B's SLATE --> Bug fixes ----->>---> Upstream SLATE
     |                                       |
     +--> User C's SLATE --> Features ------+
```

Each SLATE user:
1. Installs from the public repo
2. Customizes for their needs
3. Discovers improvements/fixes
4. Contributes back to benefit everyone

---

## Next Steps

- [Development Guide](Development) - Code style and testing details
- [Architecture](Architecture) - System design overview
- [API Reference](API-Reference) - Module documentation
- [Security Guide](Security) - Security architecture
- [Spec Template](Spec-Template) - Creating specifications
