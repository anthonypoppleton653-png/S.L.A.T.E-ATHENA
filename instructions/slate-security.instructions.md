---
name: slate-security
description: 'Security requirements enforced by ActionGuard across all SLATE code'
applyTo: '**/*.py, **/*.ts, **/*.sh, **/*.ps1, **/*.yaml'
tags: [security, actionguard, slate]
---

# SLATE Security Standards

These security requirements are enforced by ActionGuard and apply to ALL code in SLATE.

## ActionGuard Blocked Patterns

The following patterns are automatically blocked and will fail CI:

### Destructive Commands
```
rm -rf /
rm -rf ~
del /s /q C:\
format C:
```

### Network Exposure
```
0.0.0.0  # Never bind to all interfaces (except in K8s containers)
```

### Dynamic Code Execution
```python
eval(user_input)      # Blocked
exec(code_string)     # Blocked
compile(source, ...)  # Review required
```

### Obfuscation Attempts
```python
base64.b64decode(...)  # Blocked in most contexts
marshal.loads(...)     # Blocked
```

### Shell Injection
```python
subprocess.call(cmd, shell=True)  # Blocked
os.system(user_input)             # Blocked
```

## Network Security

### Local-Only Binding

All SLATE services must bind to `127.0.0.1`:

```python
# CORRECT
uvicorn.run(app, host="127.0.0.1", port=8080)

# BLOCKED by ActionGuard
uvicorn.run(app, host="0.0.0.0", port=8080)
```

### No External API Calls

SLATE is local-first. External API calls to paid services are blocked:

```python
# BLOCKED - Paid cloud APIs
openai.ChatCompletion.create(...)
anthropic.messages.create(...)

# ALLOWED - Local services
ollama.generate(model="mistral-nemo", prompt=...)
```

## SDK Source Guard

Only packages from trusted publishers are allowed:

| Trusted Publisher | Examples |
|-------------------|----------|
| Microsoft | azure-*, onnxruntime |
| NVIDIA | nvidia-cuda-*, triton |
| Anthropic | anthropic SDK |
| Meta/Facebook | torch, torchvision |
| Google | tensorflow, jax |
| Hugging Face | transformers, datasets |
| Python Foundation | pip, setuptools |

Unknown PyPI packages will be flagged for review.

## PII Scanner

Before any GitHub sync, the PII scanner checks for:

- API keys (patterns like `sk-...`, `ghp_...`)
- Access tokens
- Passwords in plaintext
- Email addresses (in certain contexts)
- Private keys (RSA, SSH)

## File Access Rules

### Protected Paths

These paths require elevated permissions:

```
.github/workflows/*    # Workflow modifications
CODEOWNERS            # Code ownership
.claude/hooks.json    # Security hooks
slate/action_guard.py # Security code
```

### Credential Files

Never commit these files:

```
.env
.env.local
credentials.json
*.pem
*.key
id_rsa*
```

## Git Operations

### No Force Push to Protected Branches

```bash
# BLOCKED
git push --force origin main
git push -f origin main

# ALLOWED (with review)
git push --force-with-lease origin feature-branch
```

### Commit Signing

Commits should include author attribution:

```bash
git commit -m "feat: add feature

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

## Validation Commands

Run security checks before committing:

```powershell
# ActionGuard validation
python slate/action_guard.py --scan .

# PII scan
python slate/pii_scanner.py --scan .

# SDK source validation
python slate/sdk_source_guard.py --check-requirements
```

## Reporting Security Issues

If you discover a security vulnerability:

1. Do NOT create a public issue
2. Email slate-security@example.com
3. Include reproduction steps
4. Wait for acknowledgment before disclosure
