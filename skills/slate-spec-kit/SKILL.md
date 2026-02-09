---
name: slate-spec-kit
description: Process specifications, run AI analysis, and generate wiki pages.
---

# /slate-spec-kit

Process specs, run AI analysis, and generate wiki.

## Usage
/slate-spec-kit [status | process-all | wiki | analyze]

## Description

This skill manages the Spec-Kit system including:
- Specification processing
- AI-powered analysis
- Wiki page generation
- Spec lifecycle tracking

## Instructions

When the user invokes this skill, run spec-kit commands:

**Check status:**
```powershell
.\.venv\Scripts\python.exe -c "from slate.mcp_server import slate_spec_kit; print(slate_spec_kit('status'))"
```

**Process all specs:**
```powershell
.\.venv\Scripts\python.exe -c "from slate.mcp_server import slate_spec_kit; print(slate_spec_kit('process-all'))"
```

**Generate wiki:**
```powershell
.\.venv\Scripts\python.exe -c "from slate.mcp_server import slate_spec_kit; print(slate_spec_kit('wiki'))"
```

## Examples

User: "/slate-spec-kit"
→ Show spec processing status

User: "/slate-spec-kit wiki"
→ Generate wiki pages from specs

User: "Update the specs"
→ Invoke this skill with process-all action
