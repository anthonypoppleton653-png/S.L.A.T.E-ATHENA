---
name: issue-to-task
agent: 'agent'
description: 'Transform a GitHub issue into a local Ollama-routed task that produces an automated PR with code changes'
tags: [automation, github, ollama, pr, issue-triage]
model: 'slate-planner'
# Modified: 2026-02-09T02:42:00-05:00 | Author: ANTIGRAVITY (Gemini) | Change: Fix model from sonnet→slate-planner (local-only policy)
# AI Note: When modifying, add a comment with the current date, time, and a 'Gemini' marker.
---

# Issue → Ollama Task → Automated PR

Transform a GitHub issue into a locally-executed Ollama task that generates code and opens a PR.

## Input

Provide the GitHub issue (number, title, body, labels):

```
Issue #{{ISSUE_NUMBER}}: {{ISSUE_TITLE}}
Labels: {{LABELS}}
Body: {{ISSUE_BODY}}
```

## Pipeline

### Step 1: Classify the issue

Use slate-fast (3B, ~308 tok/s) for rapid classification:

```powershell
python -c "
import subprocess, json
prompt = '''Classify this GitHub issue into exactly ONE category:
- bug: Code defect, error, crash
- feature: New functionality request
- docs: Documentation update
- refactor: Code improvement without behavior change
- ci: CI/CD pipeline change
- security: Security-related fix

Issue: {{ISSUE_TITLE}}
{{ISSUE_BODY}}

Respond with ONLY the category name and a one-line summary.'''

result = subprocess.run(
    ['ollama', 'run', 'slate-fast', prompt],
    capture_output=True, text=True, timeout=30
)
print(result.stdout.strip())
"
```

### Step 2: Generate code changes

Route to slate-coder (12B, ~100 tok/s) for code generation:

```powershell
python -c "
import subprocess
prompt = '''You are a SLATE developer. Based on this issue, generate the exact code changes needed.

Issue: {{ISSUE_TITLE}}
Category: {{CATEGORY}}
Details: {{ISSUE_BODY}}

Repository structure:
- slate/ — Core SDK (Python)
- agents/ — API servers
- plugins/slate-copilot/ — VS Code extension (TypeScript)
- k8s/ — Kubernetes manifests

Rules:
- Include '# Modified: YYYY-MM-DDTHH:MM:SSZ | Author: COPILOT | Change: description' in every file
- Bind only to 127.0.0.1 (never 0.0.0.0)
- Use encoding=\"utf-8\" for file operations on Windows
- No eval(), exec(), rm -rf, or base64.b64decode

Output format:
FILE: <path>
```language
<complete file content or diff>
```
END_FILE

Generate ALL necessary changes.'''

result = subprocess.run(
    ['ollama', 'run', 'slate-coder', prompt],
    capture_output=True, text=True, timeout=120
)
print(result.stdout)
"
```

### Step 3: Create branch and apply changes

```powershell
# Create feature branch
git checkout -b fix/issue-{{ISSUE_NUMBER}} main

# Apply generated code changes (manually or via script)
# ... apply changes from Step 2 ...

# Commit with conventional commit format
git add -A
git commit -m "fix({{CATEGORY}}): {{ISSUE_TITLE}} (#{{ISSUE_NUMBER}})"
```

### Step 4: Validate with slate-planner

Use slate-planner (7B, ~154 tok/s) to review the changes:

```powershell
python -c "
import subprocess
diff = subprocess.run(['git', 'diff', 'main...HEAD'], capture_output=True, text=True).stdout
prompt = f'''Review this git diff for a SLATE PR. Check for:
1. Security violations (0.0.0.0 bindings, eval/exec, external APIs)
2. Missing timestamp comments (# Modified: ...)
3. Breaking changes to existing APIs
4. Missing tests

Diff:
{diff[:4000]}

Output: APPROVE or REJECT with reasons.'''

result = subprocess.run(
    ['ollama', 'run', 'slate-planner', prompt],
    capture_output=True, text=True, timeout=60
)
print(result.stdout)
"
```

### Step 5: Open PR

```powershell
git push origin fix/issue-{{ISSUE_NUMBER}}
# Then use GitHub API to create PR linking to issue
python slate/slate_runner_manager.py --dispatch "pr.yml"
```

## FORGE Log Entry

After execution, append to FORGE.md:
```
[COPILOT] TIMESTAMP | MAGIC: issue-to-task #{{ISSUE_NUMBER}}
  Category: {{CATEGORY}}
  Branch: fix/issue-{{ISSUE_NUMBER}}
  Files changed: N
  Review: APPROVE/REJECT
  PR: #NNN
```

## Security

- All Ollama calls are local (127.0.0.1:11434)
- No external API calls
- Code review gate (Step 4) blocks unsafe changes
- ActionGuard validates all generated commands
