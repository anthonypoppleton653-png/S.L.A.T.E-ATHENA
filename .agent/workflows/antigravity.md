---
description: Antigravity Agent Workflow
---
# Antigravity General Workflow

This workflow defines the standard operating procedure for the Antigravity agent (Google AI Ultra) within the SLATE ecosystem.

## 1. Context Loading
- Always reference `brain/slate_active_context.md` for current rules.
- Check `brain/slate_cheatsheet.md` for paths and commands.

## 2. Task Intake
- If assigned a specific task, create a `branding/implementation_plan.md`.
- If asked to "work on slate", consult `.slate_tech_tree/tech_tree.json` for `in_progress` or `available` items.

## 3. Execution Standard
- **Code Style**: Google Python Style Guide + Type Hints.
- **Safety**:
  - `ACTION_GUARD` compliance (no `eval`, limited shell).
  - Use `slate_status.py` to verify environment health.
- **Documentation**:
  - Update `task.md` continuously.
  - Modify files with the `# Modified:` header.

## 4. Workflows
- To execute a specific coding task, use `slate_task` workflow.
- To manage the tech tree, use `slate_tech_tree` workflow.
