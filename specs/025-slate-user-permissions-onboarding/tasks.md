# Tasks: Spec 025 — SLATE User Permissions, Interactive Onboarding & Morph System

## Phase 1: Token Foundation (Sprint 1)

- [x] **T-025-001**: Create `design-tokens.json` — Single source of truth
  - Consolidate all tokens from spec-007, spec-008, spec-022
  - JSON schema with validation
  - Version lock mechanism

- [x] **T-025-002**: Build `slate/token_propagator.py`
  - Read `design-tokens.json`
  - Generate CSS, Python, VSCode theme, GitHub labels, CLI colors
  - Validation: ensure all outputs match source
  - Pre-commit hook integration

- [x] **T-025-003**: Create `.slate_config/permissions.yaml` schema
  - Define tier 0-5 permission levels
  - Agent-specific overrides
  - Guardrail configuration
  - Budget/quota system

- [x] **T-025-004**: Build `slate/permission_gate.py`
  - Central enforcement engine
  - Audit trail logging
  - Tier escalation flow
  - Integration with all AI agent entry points

## Phase 2: Benchmarking, Metering & Energy (Sprint 2)

- [x] **T-025-005**: Build `slate/benchmark_suite.py`
  - GPU inference benchmark (Ollama tok/s)
  - GPU VRAM scan
  - GPU thermal profile (temperature under load)
  - CPU multi-thread benchmark
  - Storage I/O benchmark
  - Memory bandwidth test
  - Network latency test

- [x] **T-025-006**: Performance Profile Card generator
  - ASCII art output (terminal)
  - HTML output (dashboard widget)
  - JSON output (storage)
  - Scoring algorithm (0-100)

- [x] **T-025-007**: Thermal Policy System
  - `.slate_config/thermal.yaml` schema
  - Four policies: aggressive, balanced, quiet, endurance
  - Auto-select based on benchmark results
  - Runtime enforcement (GPU power limiting)

- [x] **T-025-008**: Integrate benchmark into `install_slate.py`
  - Add as Phase 6 in onboarding flow
  - Animated progress in dashboard
  - Results feed into system tuning

- [x] **T-025-028**: Build `slate/token_counter.py` — Inference Token Metering
  - Hook into all Ollama API call points in the SLATE ecosystem
  - Extract prompt_tokens, completion_tokens from API response
  - Per-agent attribution (tag each call with originating agent)
  - Real-time throughput calculation (tokens/second, rolling average)
  - Append-only JSONL ledger at `.slate_analytics/token_ledger.jsonl`
  - Lifetime statistics aggregation
  - VSCode status bar live tok/s indicator
  - Dashboard widget: throughput chart + session totals + agent breakdown
  - API endpoint: `GET /api/tokens/throughput?window=1h`
  - CLI: `slate tokens [--today | --week | --lifetime]`

- [x] **T-025-029**: Build `slate/energy_providers.py` — Provider Database
  - US electrical provider database (top 10 metro providers)
  - ZIP code to provider lookup
  - Rate schedule parsing (TOU: peak/off-peak/super-off-peak)
  - Flat rate provider support
  - Community-contributed provider submissions (via SLATE Discussions)
  - Seasonal rate adjustment support

- [x] **T-025-030**: Build `slate/energy_scheduler.py` — Rate-Aware Scheduling
  - Operation classifier (heavy/normal/light)
  - Current rate tier detection (time-based)
  - Schedule decision engine (execute now vs queue for window)
  - Operation queue with next-window targeting
  - Monthly cost estimator (actual vs projected vs unscheduled)
  - Budget alerting at configurable thresholds
  - Hard cap option (pause non-essential ops at budget limit)
  - `.slate_config/energy.yaml` configuration schema

- [x] **T-025-031**: Energy Configuration Onboarding UI (Phase 7)
  - ZIP code / city input field
  - Electrical provider dropdown (auto-populated from ZIP)
  - Rate schedule visualization (color-coded timeline)
  - SLATE scheduling preview (heavy/normal/light operation windows)
  - Cost comparison (optimized vs unoptimized)
  - "Skip — Run Anytime" option for users who don't care
  - AI narration explaining the savings opportunity

- [x] **T-025-032**: Token Counter + Energy Dashboard Widgets
  - Token throughput live chart (sparkline in dashboard header)
  - Per-agent token breakdown (bar chart with percentages)
  - Current rate tier indicator (green/yellow/red badge)
  - Queued operations list (with scheduled execution times)
  - Monthly cost gauge (budget progress bar)
  - Energy savings counter ($XX saved vs unscheduled)

## Phase 3: Onboarding UI (Sprint 3-4)

- [ ] **T-025-009**: Phase 1 Awakening animation
  - Blueprint grid fade-in
  - Gear ring materialization
  - Starburst ray extension
  - Typewriter title effect
  - Status jewel pulse

- [ ] **T-025-010**: Phase 2 Discovery (System Scan)
  - Hardware detection with live animation
  - Thermal baseline measurement
  - Results as watchmaker complications
  - Network speed test visualization

- [ ] **T-025-011**: Phase 3 Identity (Path Selection)
  - "SLATE Developer" vs "New SLATE" cards
  - Hover/click animations
  - AI narration for each path
  - Decision persistence

- [ ] **T-025-012**: Phase 4 Permissions (AI Control)
  - Interactive tier selector (slider + visual)
  - Tier explanation cards
  - Guardrail toggle grid
  - Live preview of what each tier allows

- [ ] **T-025-013**: Phase 5 Systems (Feature Selection)
  - Toggle grid with resource requirements
  - Dependency warnings (e.g., GPU required for inference)
  - Running total of resource usage
  - Recommended configuration highlight

- [ ] **T-025-014**: Phase 10 Education (SLATE Academy)
  - Interactive system map (clickable nodes)
  - Plugin SDK code example (live-editable)
  - Morph concept explanation
  - Achievement/badge system start

- [ ] **T-025-015**: Phase 12 Launch Celebration
  - Starburst + gear celebration animation
  - System summary card
  - "What to do next" guidance
  - Dashboard launch transition

## Phase 4: Morph System (Sprint 5)

- [ ] **T-025-016**: Create `.slate_config/morph.yaml` schema
  - Project identity fields
  - Brand override configuration
  - Active systems selection
  - Protected paths list
  - Upstream sync preferences

- [ ] **T-025-017**: Build `slate/morph_manager.py`
  - Fork creation automation
  - Custom branding application
  - README generation (AI-powered)
  - GitHub Pages setup
  - morph.yaml read/write

- [ ] **T-025-018**: Build Morph SDK (`plugins/slate-sdk/morph-sdk/`)
  - Python SDK for building SLATE Morphs
  - Widget registration API
  - Workflow extension API
  - Plugin lifecycle hooks (on_install, on_update, on_benchmark)

- [ ] **T-025-019**: Creative Commons Contract UI
  - Contract display in onboarding
  - Acceptance flow with signature
  - Financial distribution explanation
  - Benefits showcase
  - Legal text rendering

- [ ] **T-025-020**: Fork Branding Flow
  - Color picker for primary brand color
  - Project name + tagline input
  - Logo upload or AI generation
  - README template selection
  - Live preview in dashboard theme

## Phase 5: Update & Conflict System (Sprint 6)

- [ ] **T-025-021**: Build `slate/conflict_resolver.py`
  - Upstream change detection (webhook + polling)
  - Diff analysis engine
  - Conflict classification (SAFE_MERGE, MORPH_DIVERGENCE, etc.)
  - AI-powered resolution suggestions
  - Morph identity guard (post-merge validation)

- [ ] **T-025-022**: Update Preview UI
  - Interactive diff viewer in dashboard
  - AI change explanation
  - Morph-impact highlighting
  - One-click merge for safe changes
  - Guided merge for conflicts

- [ ] **T-025-023**: Rollback System
  - Pre-update snapshot creation
  - 7-day rollback window
  - One-click revert
  - Benchmark comparison (before/after update)

- [ ] **T-025-024**: Upstream Sync Workflow
  - GitHub Action for automated sync check
  - configurable frequency (daily/weekly/manual)
  - Notification on available updates
  - Auto-merge for non-conflicting core updates

## Phase 6: Education & Polish (Sprint 7)

- [ ] **T-025-025**: SLATE Academy Content
  - System overview documentation
  - Plugin SDK tutorial
  - Morph creation guide
  - Video/GIF walkthrough generation
  - Achievement badges

- [ ] **T-025-026**: Permission Dashboard Widget
  - Visual permission matrix editor
  - Real-time audit log viewer
  - Agent activity heatmap
  - Budget usage gauges

- [ ] **T-025-027**: Integration Testing
  - Full onboarding flow E2E test
  - Permission enforcement tests
  - Benchmark accuracy validation
  - Morph creation + branding test
  - Update conflict resolution test
  - Token propagation validation

---

## Dependencies

```
T-025-001 ─┬─→ T-025-002 (tokens must exist before propagation)
            └─→ T-025-009 (animations use token colors)

T-025-003 ─→ T-025-004 (schema before enforcement)
T-025-004 ─→ T-025-012 (gate before permission UI)

T-025-005 ─→ T-025-006 (benchmarks before profile card)
T-025-006 ─→ T-025-007 (profile before thermal policy)
T-025-007 ─→ T-025-008 (policy before install integration)

T-025-028 ─→ T-025-032 (token counter before dashboard widget)
T-025-029 ─→ T-025-030 (provider DB before scheduler)
T-025-030 ─→ T-025-031 (scheduler before onboarding UI)
T-025-028 ─┬─→ T-025-030 (token counter feeds energy cost calc)
            └─→ T-025-032 (counter data for dashboard)

T-025-016 ─→ T-025-017 (schema before manager)
T-025-017 ─→ T-025-018 (manager before SDK)
T-025-017 ─→ T-025-020 (manager before branding)

T-025-021 ─→ T-025-022 (resolver before preview UI)
T-025-022 ─→ T-025-023 (preview before rollback)
```
