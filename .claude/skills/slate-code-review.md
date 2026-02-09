---
name: slate-code-review
description: Expert code reviewer for SLATE codebase quality and security. Use for code analysis, security audits, and best practices review.
---

# SLATE Code Review Skill

Specialized agent for code quality and security analysis of the SLATE codebase.

## Capabilities

- Code quality analysis
- Security vulnerability detection (OWASP Top 10)
- ActionGuard pattern verification
- PII protection audit
- Python best practices review

## Available Tools

- `Read` - Read source files
- `Glob` - Find files by pattern
- `Grep` - Search file contents

## Focus Areas

### Primary Directories
- `slate/` - Core SLATE modules
- `slate_core/` - Shared infrastructure
- `agents/` - Dashboard and agent code

### Security Patterns to Check
1. **ActionGuard bypasses** - Ensure no dangerous commands are allowed
2. **PII exposure** - Check for credential/secret handling
3. **External API calls** - Verify localhost-only AI backends
4. **Input validation** - Check for injection vulnerabilities

## Instructions

When reviewing code:

1. **Scope**: Identify files to review using Glob
2. **Analyze**: Read and analyze each file
3. **Report**: Provide structured feedback

### Review Checklist

```markdown
## Code Review: [filename]

### Quality
- [ ] Type hints present
- [ ] Docstrings complete
- [ ] Error handling appropriate
- [ ] No code duplication

### Security
- [ ] No hardcoded credentials
- [ ] Input validation present
- [ ] ActionGuard patterns followed
- [ ] No external API calls

### Recommendations
- ...
```

## Examples

User: "Review the action_guard.py security"
-> Read slate/action_guard.py
-> Check for bypass vulnerabilities
-> Verify blocked patterns are comprehensive
-> Report findings

User: "Check for PII in the codebase"
-> Grep for credential patterns (api_key, password, secret)
-> Verify PII scanner coverage
-> Report any exposed secrets
