---
description: Execute a Slate Coding Task
---
# Slate Coding Task

A standardized workflow for executing coding tasks within the SLATE ecosystem.

## 1. Task Initialization
- **Read**: `task.md` or user request.
- **Reference**: `AGENTS.md` and `slate_active_context.md`.
- **Status Check**: Ensure environment is clean (`slate_status.py --quick`).

## 2. Planning
- Create `branding/implementation_plan.md`:
  - Goal
  - Affected Files (use `grep_search`)
  - Verification Plan (Tests)

## 3. Execution
- **Step 1**: Run tests *before* changes (establish baseline).
- **Step 2**: Apply changes (using `replace_file_content` or `multi_replace`).
- **Step 3**: Verify changes (run tests again).
- **Step 4**: Update `task.md`.

## 4. Completion
- Run `slate_runtime.py --check-all` (Integration Test).
- Mark task complete in `current_tasks.json` (if applicable).
- Notify User.
