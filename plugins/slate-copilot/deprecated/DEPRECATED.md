# DEPRECATED: SLATE Copilot Extensions v2.x — v4.x
# DEPRECATED: 2026-02-08 | Reason: Replaced by v5.0.0 with K8s/Docker runtime backend
# Modified: 2026-02-08T22:00:00Z | Author: COPILOT | Change: Deprecate all pre-v5 VSIX builds

## Notice

All VSIX files in this directory are **DEPRECATED** and should NOT be installed.

### Deprecated Versions

| Version | Date | Reason |
|---------|------|--------|
| 2.5.0 | 2026-02-07 | Initial release — local Python execution only |
| 2.5.2 | 2026-02-07 | Bug fixes — no K8s support |
| 2.6.0 | 2026-02-07 | Added more tools — still local-only |
| 2.6.1 | 2026-02-07 | Minor fixes |
| 2.7.0 | 2026-02-07 | Added background schematic |
| 3.0.0 | 2026-02-07 | Major: unified dashboard — no K8s backend |
| 3.1.0 | 2026-02-07 | Service monitor |
| 3.2.0 | 2026-02-07 | VS Code deep integrations |
| 3.2.1 | 2026-02-07 | Bug fixes |
| 3.3.0 | 2026-02-07 | Agent bridge |
| 3.4.0 | 2026-02-07 | Spec kit |
| 4.0.0 | 2026-02-07 | Added K8s tool — but still local Python execution |
| 4.1.0 | 2026-02-08 | GitHub integrations — still local Python execution |

### Why Deprecated

All versions v2.x through v4.x execute SLATE commands by spawning **local Python
processes** via `child_process.spawn()`. This architecture:

1. **Cannot reach K8s services** — commands run locally, not against the cluster
2. **Requires local Python/venv** — won't work in remote or container environments
3. **No Docker runtime awareness** — cannot detect/interact with containerized SLATE
4. **Single-node only** — no multi-pod, multi-replica support

### Replacement

**v5.0.0** (`slate-copilot-5.0.0.vsix`) introduces:

- **K8s Backend Mode** — routes commands to `slate-copilot-bridge-svc:8083` in the cluster
- **Docker Runtime Detection** — auto-detects Docker containers and routes accordingly
- **Hybrid Execution** — falls back to local Python if K8s/Docker are unavailable
- **Service Discovery** — discovers SLATE services via K8s API or Docker labels
- **Health-aware routing** — checks service health before routing commands

Install the new version:
```bash
code --install-extension slate-copilot-5.0.0.vsix
```
