# S.L.A.T.E. Development Guidelines

**S.L.A.T.E.** = Synchronized Living Architecture for Transformation and Evolution

Last updated: 2026-02-06

## Architecture

SLATE uses a **GitHub-centric architecture** with a self-hosted runner for GPU-accelerated CI/CD:

```
GitHub Repository (S.L.A.T.E.)
         │
         ▼
  Self-Hosted Runner
  (2x RTX 5070 Ti)
         │
         ▼
   Workflow Jobs
   (tests, builds)
```

## Technologies

- Python 3.11+
- FastAPI (dashboard on port 8080)
- GitHub Actions (CI/CD)
- Self-hosted runner (GPU compute)

## Project Structure

```text
aurora_core/           # Core SLATE modules
  slate_status.py      # System status checker
  slate_runner_manager.py    # GitHub runner management
  slate_github_integration.py  # GitHub API integration
.github/
  workflows/           # GitHub Actions workflows
tests/                 # Test suite
specs/                 # Specifications
```

## Commands

```powershell
# Check SLATE status
.\.venv\Scripts\python.exe aurora_core/slate_status.py --quick

# Run tests
.\.venv\Scripts\python.exe -m pytest tests/ -v

# Lint
ruff check .

# Check GitHub integration
.\.venv\Scripts\python.exe aurora_core/slate_github_integration.py --status
```

## GitHub Runner

SLATE runs on a self-hosted GitHub Actions runner with GPU support.

### Status Check

```powershell
.\.venv\Scripts\python.exe aurora_core/slate_runner_manager.py --status
```

### Setup

```powershell
# Download runner
.\.venv\Scripts\python.exe aurora_core/slate_runner_manager.py --download

# Configure (get token from GitHub repo settings)
.\.venv\Scripts\python.exe aurora_core/slate_runner_manager.py --configure --token YOUR_TOKEN

# Start runner
.\.venv\Scripts\python.exe aurora_core/slate_runner_manager.py --start
```

### Runner Labels

Auto-detected labels:
- `self-hosted`, `slate`, `gpu`, `windows`
- `cuda`, `gpu-2` (GPU count)
- `blackwell` (RTX 50 series)

### Get Token

1. Go to https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E./settings/actions/runners
2. Click "New self-hosted runner"
3. Copy the token

## Development Workflow

```powershell
# Create feature branch
git checkout -b feature/my-feature

# Make changes, commit
git add .
git commit -m "feat: description"

# Push to origin
git push origin HEAD

# Create PR on GitHub
```

## Security

- All servers bind to `127.0.0.1` only
- No external network calls
- GitHub runner executes trusted workflows only

## GitHub Integration

Repository: https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E.

- Branch protection on `main`
- CODEOWNERS enforces review requirements
- All PRs must pass CI checks
