---
name: pr-review
agent: 'agent'
description: 'Automated local code review of PR diffs using slate-coder and slate-planner via Ollama'
tags: [code-review, pr, ollama, security, quality]
model: 'slate-coder'
# Modified: 2026-02-09T02:42:00-05:00 | Author: ANTIGRAVITY (Gemini) | Change: Fix model from sonnet→slate-coder (local-only policy)
# AI Note: When modifying, add a comment with the current date, time, and a 'Gemini' marker.
---

# PR Code Review via Local Ollama

Perform automated, security-aware code review on pull request diffs using local SLATE models.

## Input

Provide PR number or branch name:

```
PR #{{PR_NUMBER}} | Branch: {{BRANCH_NAME}}
```

## Pipeline

### Step 1: Extract diff

```powershell
# Get the diff against main
$diff = git diff main...{{BRANCH_NAME}} -- ':(exclude)*.lock' ':(exclude)vendor/'
$stats = git diff --stat main...{{BRANCH_NAME}}
Write-Host "Files changed:"
Write-Host $stats
```

### Step 2: Security scan (slate-fast — 3B, fast gate)

Quick security pass — reject obvious violations immediately:

```powershell
python -c "
import subprocess
diff = subprocess.run(
    ['git', 'diff', 'main...{{BRANCH_NAME}}'],
    capture_output=True, text=True
).stdout[:6000]

prompt = f'''SECURITY REVIEW — scan this diff for violations.

BLOCKED PATTERNS (instant reject):
- 0.0.0.0 bindings (must be 127.0.0.1)
- eval(), exec() calls
- rm -rf, del /s, format commands
- base64.b64decode of unknown data
- API keys, tokens, passwords in code
- External paid API calls (OpenAI, Anthropic direct)
- curl.exe usage (use urllib.request instead)

Diff:
{diff}

Output EXACTLY one of:
PASS — No security violations found
FAIL — [list each violation with file:line]'''

result = subprocess.run(
    ['ollama', 'run', 'slate-fast', prompt],
    capture_output=True, text=True, timeout=30
)
print(result.stdout.strip())
"
```

### Step 3: Code quality review (slate-coder — 12B, deep analysis)

```powershell
python -c "
import subprocess
diff = subprocess.run(
    ['git', 'diff', 'main...{{BRANCH_NAME}}'],
    capture_output=True, text=True
).stdout[:8000]

prompt = f'''CODE REVIEW — analyze this diff for quality and correctness.

Check for:
1. **Correctness** — Logic errors, edge cases, null handling
2. **Style** — Follows SLATE conventions (timestamps, encoding='utf-8')
3. **Performance** — Unnecessary loops, blocking calls, memory leaks
4. **Tests** — Are changes covered by tests?
5. **Breaking changes** — API signature changes, removed exports
6. **Documentation** — Updated docstrings, README if needed

SLATE conventions:
- Every edited file needs: # Modified: YYYY-MM-DDTHH:MM:SSZ | Author: ... | Change: ...
- Network bindings: 127.0.0.1 only
- File encoding: utf-8 on Windows
- PowerShell: pwsh 7.5+ preferred

Diff:
{diff}

Output:
SUMMARY: one-line verdict
SCORE: 1-10
ISSUES: numbered list (empty if none)
SUGGESTIONS: numbered list (empty if none)'''

result = subprocess.run(
    ['ollama', 'run', 'slate-coder', prompt],
    capture_output=True, text=True, timeout=120
)
print(result.stdout)
"
```

### Step 4: Architecture review (slate-planner — 7B, design analysis)

```powershell
python -c "
import subprocess
diff = subprocess.run(
    ['git', 'diff', 'main...{{BRANCH_NAME}}', '--stat'],
    capture_output=True, text=True
).stdout

prompt = f'''ARCHITECTURE REVIEW — evaluate structural impact.

File change summary:
{diff}

Evaluate:
1. Does this change respect SLATE module boundaries?
   - slate/ = Core SDK (Python)
   - agents/ = API servers
   - plugins/ = VS Code extensions (TypeScript)
   - k8s/ = Kubernetes manifests
   - .github/workflows/ = Protected CI/CD

2. Are there cross-cutting concerns?
3. Should this be split into smaller PRs?
4. Impact on K8s deployments or Docker image?

Output: APPROVE / SPLIT / DISCUSS with reasoning.'''

result = subprocess.run(
    ['ollama', 'run', 'slate-planner', prompt],
    capture_output=True, text=True, timeout=60
)
print(result.stdout)
"
```

### Step 5: Compose review summary

Combine all three reviews into a structured report:

| Gate | Model | Result | Details |
|------|-------|--------|---------|
| Security | slate-fast | PASS/FAIL | Violations list |
| Quality | slate-coder | Score/10 | Issues + suggestions |
| Architecture | slate-planner | APPROVE/SPLIT | Structural analysis |

**Overall verdict**: APPROVE / REQUEST_CHANGES / REJECT

## FORGE Log Entry

```
[COPILOT] TIMESTAMP | MAGIC: pr-review #{{PR_NUMBER}}
  Security: PASS/FAIL
  Quality: N/10
  Architecture: APPROVE/SPLIT/DISCUSS
  Verdict: APPROVE/REQUEST_CHANGES/REJECT
```
