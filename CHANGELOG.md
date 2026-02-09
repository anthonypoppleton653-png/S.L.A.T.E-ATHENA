# Changelog
<!-- Modified: 2026-02-09T16:01:00-05:00 | Author: Gemini (Antigravity) | Change: Add v3.0.0-stable entry -->
*Auto-generated: 2026-02-09*

## [3.0.0-stable] — 2026-02-09

### Added
- **Spec 025**: User Permissions & Onboarding system
  - `slate/benchmark_suite.py` — 9 hardware benchmarks (GPU VRAM, inference tok/s, thermal, CPU, memory, storage, network)
  - `slate/permission_gate.py` — Role-based permission system (OBSERVER → ARCHITECT)
  - `slate/token_counter.py` — LLM token metering with cost tracking
  - `slate/energy_scheduler.py` — Energy-aware task scheduling with GPU thermal management
  - `slate/token_propagator.py` — Design token distribution across all SLATE surfaces
  - Performance Profile Card generator (ASCII, HTML, JSON output)
  - Thermal Policy System (aggressive / balanced / quiet / endurance)
- **AI Agent Integrations** — 3 active platforms: Claude Code, GitHub Copilot, Antigravity (Gemini)
- **Docker stable image** — `ghcr.io/synchronizedlivingarchitecture/slate:stable`
- AI Agent Integrations section on GitHub Pages with premium card showcase
- `design-tokens.json` — Unified design token system

### Changed
- Docker image version bump to v3.0.0
- README updated with all 3 AI agents, Docker GHCR instructions, Spec 025 summary
- Hardware specs updated (64 GB DDR5 RAM, benchmark score 86.1/100)
- Docker workflow now tags GPU image as `:stable` alongside `:latest-gpu`

### Infrastructure
- Benchmark score: 86.1/100 — Workstation Tier
- RTX 5070 Ti: 32,606 MB VRAM detected
- 24-core CPU, 63.3 GB RAM, NVMe SSD

 ## [Unreleased]

### Added
- Guided workflow engine (368d3f74)
- Multiple AI SDK integrations (368d3f74)
- Extensive documentation with new specifications and Kubernetes support (368d3f74)
- PowerShell MCP launcher and diagnostic tool (01baaee0, 057071f1)
- Adaptive instruction layer for K8s-driven dynamic instruction system (10b24827)
- GitHub Models and Semantic Kernel modules (ee9cc048)
- Kubernetes infrastructure for SLATE system (45b34af6)
- Stability module, local K8s overlay, Helm chart, deploy manager (777a5321)
- Unified aurora_core references to slate (9b3112ba)
- SLATE timestamp comments to flagged files (b5610d23)
- Runtime integrations, vendor SDKs, K8s infra, wiki docs, specs, and tests (e35b1b40)
- Full Docker/K8s onboarding for real services (789684a3)
- Contact email and author biography to documentation (dcc7bcd0)
- Watchmaker Golden Ratio UI, unified tokens, logo, theme (225b7177)

### Changed
- Upgrade GitHub Pages with watchmaker design system, Phase 3 showcase, and live system metrics (02738427)
- Embed GitHub Pages feature site in README with badges and dedicated section (c40611f2)
- Phase 3 expansion of token system, brand identity, avatar system, TRELLIS.2 integration, unified AI backend, full documentation update (6e30d96b)
- Simplify manifests for Claude Code schema compliance (33262bed)
- Add plugins array for Claude Code marketplace schema (95bb97c8)
- Update settings.json for unified plugin v5.3.0 (6885e787)
- Unify SLATE plugin to single v5.3.0 package (4314ac7d)
- Fix docker.yml env context in matrix, boolean input defaults (4be5f1a5)

### Fixed
- Correct marketplace.json schema for Claude Code (7f8c4d6b, 9a900b11)
- Use object format for plugin source schema (9cd64a20)
- Simplify plugin and marketplace for Claude Code compatibility (057071f1)
- Fix MCP launcher for self-resolving paths (56431272, f034aee7)
- Use cwd and env var for MCP path resolution (a1516e36, a1516e36)
- Add SLATE timestamp comments to flagged files (b5610d23)
- Fix docker.yml env context in matrix, boolean input defaults (4be5f1a5)

### Infrastructure
- 4 self-hosted GitHub Actions runners
- 2 RTX 5070 Ti GPUs
- Kubernetes integration for SLATE system (ac191277, c388d2fc, ac191277)