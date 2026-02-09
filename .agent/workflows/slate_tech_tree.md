---
description: Discover and Assign Tasks from Tech Tree
---
# Tech Tree Discovery

Workflow for identifying and starting tasks from the SLATE Tech Tree.

## 1. Discovery
- Run: `python slate/slate_unified_autonomous.py --discover` (or inspect `tech_tree.json`).
- Filter for `status: "available"` or `status: "in_progress"`.

## 2. Selection
- Choose a high-priority node aligned with user goals.
- Check dependencies (`edges` in `tech_tree.json`).

## 3. Initialization
- Create a new entry in `current_tasks.json` via `slate_workflow_manager.py --add-task`.
- Assign to `Antigravity` (Google AI Ultra).

## 4. Handoff
- Proceed to **Slate Coding Task** workflow.
