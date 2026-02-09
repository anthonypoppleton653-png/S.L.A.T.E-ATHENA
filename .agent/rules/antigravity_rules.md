
# Antigravity Rules
# Description: Rules governing Antigravity's behavior and decision-making process.

1.  **User Primacy**: User intent is the highest priority. If instructions conflict with user requests, ask for clarification or prioritize the user's explicit command.
2.  **System Integrity**: Do not break the build. Ensure all changes are verified with tests (`slate_runtime.py --check-all`).
3.  **Local-First**, **Privacy-First**: All operations must be local (127.0.0.1). No external API calls without explicit user permission.
4.  **Architectural Purity**: Changes should adhere to the established patterns in `slate/` and `plugins/`. Avoid ad-hoc solutions.
5.  **Documentation**: Update documentation (`docs/`) and task lists (`task.md`) with every significant change.
6.  **GPU Awareness**: Utilize detected GPUs (`cuda:0`, `cuda:1`) for inference and testing where applicable.
7.  **Skill Utilization**: Use relevant skills from `.agent/skills/` to execute complex workflows.
