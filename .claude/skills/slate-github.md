# SLATE GitHub Skill

Manage GitHub integrations including Actions, Projects, and Models.

## Repository

- **URL**: https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E.
- **Wiki**: https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E./wiki

## GitHub CLI

```powershell
# Check auth status
gh auth status

# List workflows
gh workflow list

# View recent runs
gh run list --limit 10

# Trigger workflow
gh workflow run <workflow-name>

# View PR
gh pr view <number>

# Create PR
gh pr create --title "title" --body "body"
```

## GitHub Actions

18 workflows available:
- `ci.yml` - Continuous Integration
- `cd.yml` - Continuous Deployment
- `gpu-tests.yml` - GPU-enabled tests on self-hosted runner
- `slate-protocol.yml` - Sync, validate, deploy automation
- `github-models.yml` - AI code review with GitHub Models
- `release.yml` - Release management
- `codeql.yml` - Security analysis

## GitHub Projects

```powershell
# List projects
.\.venv\Scripts\python.exe slate/slate_project_manager.py --list

# Create project
.\.venv\Scripts\python.exe slate/slate_project_manager.py --create --template development

# Sync tasks
.\.venv\Scripts\python.exe slate/slate_project_manager.py --sync --project 1
```

## GitHub Models

```powershell
# List models
.\.venv\Scripts\python.exe slate/slate_github_models.py --list-models

# Chat
.\.venv\Scripts\python.exe slate/slate_github_models.py --chat "Hello"

# Check availability
.\.venv\Scripts\python.exe slate/slate_github_models.py --check
```

## Git Integration

```powershell
# Configure remotes
python slate/slate_sdk.py --integrate-git

# Push with workflow scope (if needed)
gh auth login -s workflow -w
git push origin HEAD
```

## Dashboard

GitHub Models panel at http://127.0.0.1:8080 shows:
- Token status
- SDK installation
- Available models
- Connection test
