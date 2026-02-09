# Spec 025: SLATE User Permissions, Interactive Onboarding & Morph System

- **Spec ID**: 025-slate-user-permissions-onboarding
- **Status**: Specified
- **Created**: 2026-02-09
- **Author**: Antigravity (Gemini)
- **Dependencies**: 007-slate-design-system, 008-slate-guided-experience, 010-slate-generative-onboarding, 022-slate-brand-identity
- **Spec-Kit**: Yes

---

## 1. Overview

This specification defines the **complete user lifecycle** for SLATE — from first install to daily use to forking and morphing. It unifies:

1. **User Permission System** — Role-based AI system controls
2. **Interactive Onboarding** — AI-powered, animated, Watchmaker-themed first-run experience
3. **System Benchmarking** — Hardware profiling, thermal tuning, and performance optimization
4. **Token Counter & Throughput Monitor** — Objective inference metering and cost tracking
5. **Energy-Aware Scheduling** — Electrical provider billing integration for cost optimization
6. **SLATE Morphs** — Forking SLATE into user-customized projects
7. **Update & Conflict Resolution** — Safe upstream sync with morph protection
8. **Unified Theme & Token System** — Single source of truth for all visual surfaces

### Design Philosophy

> SLATE's onboarding exists to **demonstrate its power**. The install process IS the product demo.
> Every frame, every animation, every AI interaction during onboarding is a live proof of what
> SLATE can do. The user doesn't learn about SLATE — they experience it.

---

## 2. User Permission System

### 2.1 Permission Architecture

SLATE's AI systems operate under a **tiered permission model** that the user controls. Permissions determine what AI agents can touch, modify, create, and deploy.

```
╔═══════════════════════════════════════════════════════════════╗
║              SLATE AI PERMISSION TIERS                        ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  TIER 0 — OBSERVER (Read-Only)                               ║
║    Can: Read code, analyze architecture, generate reports     ║
║    Cannot: Modify files, run commands, commit changes         ║
║                                                               ║
║  TIER 1 — ADVISOR (Suggest-Only)                             ║
║    Can: All of Tier 0 + create suggestions, draft PRs        ║
║    Cannot: Auto-commit, run destructive commands              ║
║                                                               ║
║  TIER 2 — COLLABORATOR (Safe Modifications)                  ║
║    Can: All of Tier 1 + modify safe output directories       ║
║    Cannot: Modify source code, configs, workflows             ║
║    Safe Dirs: docs/, plans/, CHANGELOG.md, docs/wiki/         ║
║                                                               ║
║  TIER 3 — DEVELOPER (Full Source Access)                     ║
║    Can: All of Tier 2 + modify source code, create files     ║
║    Cannot: Modify .github/workflows, delete branches          ║
║    Requires: Review before commit (configurable)              ║
║                                                               ║
║  TIER 4 — ARCHITECT (Full System Access)                     ║
║    Can: All of Tier 3 + modify workflows, configs, deploy    ║
║    Cannot: Delete repository, revoke owner access             ║
║    Requires: User approval for destructive operations         ║
║                                                               ║
║  TIER 5 — AUTONOMOUS (Self-Governing)                        ║
║    Can: Everything Tier 4 + autonomous task execution         ║
║    Operates: Within user-defined guardrails and budgets       ║
║    Reports: All actions logged, audit trail maintained         ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
```

### 2.2 Permission Configuration

Stored in `.slate_config/permissions.yaml`:

```yaml
# SLATE User Permission Configuration
# Modified: 2026-02-09T11:33:00-05:00 | Gemini
# NOTE: All AIs modifying this file must add a dated comment.

version: "1.0.0"

# Global AI permission tier (0-5)
default_tier: 3

# Per-agent overrides
agents:
  antigravity:
    tier: 4
    allowed_paths:
      - "**/*"
    blocked_paths:
      - ".env"
      - "*.secret"
    can_commit: true
    can_deploy: false
    budget:
      max_tokens_per_hour: 500000
      max_api_calls_per_hour: 100

  copilot:
    tier: 3
    allowed_paths:
      - "slate/**"
      - "plugins/**"
      - "docs/**"
    can_commit: false
    review_required: true

  claude:
    tier: 4
    allowed_paths:
      - "**/*"
    can_commit: true
    can_deploy: false

  autonomous_runner:
    tier: 2
    allowed_paths:
      - "docs/**"
      - "plans/**"
      - "CHANGELOG.md"
    can_commit: true
    can_deploy: false

# Guardrails — apply to ALL tiers
guardrails:
  require_audit_trail: true
  max_files_per_commit: 50
  banned_operations:
    - "rm -rf /"
    - "git push --force origin main"
    - "DROP TABLE"
  protected_branches:
    - main
    - release/*
  require_approval_for:
    - workflow_modification
    - secret_access
    - deployment
    - branch_deletion

# Notification preferences
notifications:
  on_tier_escalation: true
  on_blocked_action: true
  on_autonomous_completion: true
  channels:
    - vscode    # VSCode notification
    - dashboard # Dashboard alert
    - github    # GitHub Issue/Discussion
```

### 2.3 Permission Enforcement

```python
class SlatePermissionGate:
    """
    Central permission enforcement for all AI operations.
    
    Every AI action passes through this gate. The gate checks:
    1. Agent's permission tier
    2. Target path against allowed/blocked lists
    3. Operation type against tier capabilities
    4. Guardrail constraints
    5. Budget limits (token/API call quotas)
    """
    
    def check(self, agent: str, operation: str, target: str) -> PermissionResult:
        """Returns ALLOW, DENY, or REQUIRE_APPROVAL."""
        pass
    
    def log_action(self, agent: str, operation: str, target: str, result: str):
        """Immutable audit trail entry."""
        pass
    
    def escalate(self, agent: str, reason: str) -> bool:
        """Request temporary tier escalation from user."""
        pass
```

### 2.4 Permission UI

The permission system is accessible from:
- **Dashboard**: `/settings/permissions` — Visual permission matrix editor
- **VSCode**: `@slate /permissions` — Quick permission check/modify
- **CLI**: `slate permissions show | set | audit`

---

## 3. Interactive Onboarding System

### 3.1 Onboarding Philosophy

The onboarding is NOT a setup wizard — it's a **live demonstration of SLATE's engineering**.

```
╔═══════════════════════════════════════════════════════════════╗
║                   ONBOARDING PRINCIPLES                       ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  1. SHOW, DON'T TELL                                         ║
║     Every feature is demonstrated live during setup            ║
║                                                               ║
║  2. AI GUIDES EVERYTHING                                     ║
║     Local Ollama narrates, explains, and executes              ║
║                                                               ║
║  3. WATCHMAKER AESTHETICS                                    ║
║     Gear animations, blueprint grids, jewel indicators         ║
║     demonstrate the design system in real-time                 ║
║                                                               ║
║  4. SYSTEM-AWARE                                             ║
║     Benchmarks adapt the experience to the user's hardware     ║
║                                                               ║
║  5. DECISION TREE                                            ║
║     User makes meaningful choices that shape their SLATE       ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
```

### 3.2 Onboarding Flow (12 Phases)

```
┌─────────────────────────────────────────────────────────────────┐
│                     SLATE ONBOARDING FLOW                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Phase 1: AWAKENING                                             │
│  ├─ Animated SLATE logo boot sequence                           │
│  ├─ Watchmaker gears spin up                                    │
│  ├─ Blueprint grid materializes                                 │
│  └─ AI voice: "Initializing S.L.A.T.E..."                     │
│                                                                  │
│  Phase 2: DISCOVERY (System Scan)                               │
│  ├─ Hardware detection with live GPU/CPU animation              │
│  ├─ Thermal baseline measurement                                │
│  ├─ Network speed test                                          │
│  ├─ Storage scan (reuse existing packages)                      │
│  └─ Results displayed as watchmaker complications               │
│                                                                  │
│  Phase 3: IDENTITY (User Path Selection)                        │
│  ├─ "Are you a SLATE Developer or creating a New SLATE?"       │
│  ├─ SLATE Developer → Contribute to main project                │
│  └─ New SLATE → Fork + Morph into custom project                │
│                                                                  │
│  Phase 4: PERMISSIONS (AI Control Setup)                        │
│  ├─ Interactive permission tier selector                         │
│  ├─ Visual explanation of each tier                              │
│  ├─ "How much autonomy should your AI have?"                   │
│  └─ Guardrail configuration                                     │
│                                                                  │
│  Phase 5: SYSTEMS (Choose Active Systems)                       │
│  ├─ Toggle grid of available SLATE systems                      │
│  │   ├─ 🧠 Local AI (Ollama)                                   │
│  │   ├─ ⚡ GPU Compute (CUDA)                                   │
│  │   ├─ 🤖 Agent Framework (Copilot/Claude/Antigravity)        │
│  │   ├─ 📦 CI/CD Runner (GitHub Actions)                       │
│  │   ├─ 🐳 Docker Containers                                   │
│  │   ├─ ☸️  Kubernetes Orchestration                            │
│  │   ├─ 📊 Dashboard & Monitoring                               │
│  │   ├─ 📚 Spec-Kit Documentation                              │
│  │   └─ 🎨 3D Avatar (TRELLIS.2)                               │
│  └─ Each toggle shows resource requirements                     │
│                                                                  │
│  Phase 6: BENCHMARK (Performance Profiling)                     │
│  ├─ GPU inference benchmark (Ollama)                            │
│  ├─ CPU multi-thread benchmark                                  │
│  ├─ Storage I/O benchmark                                       │
│  ├─ Thermal stress test (5 min)                                 │
│  ├─ Memory bandwidth test                                       │
│  └─ Results: Performance profile card                           │
│                                                                  │
│  Phase 7: TUNING (System + Energy Optimization)                 │
│  ├─ Auto-configure based on benchmark results                   │
│  ├─ GPU memory allocation strategy                              │
│  ├─ Ollama model selection (based on VRAM)                      │
│  ├─ Thermal throttle thresholds                                 │
│  ├─ Concurrent task limits                                      │
│  ├─ 🔌 Energy Configuration                                    │
│  │   ├─ Optional: Enter address or ZIP code                    │
│  │   ├─ Optional: Select electrical provider from list          │
│  │   ├─ Auto-detect rate schedule (peak/off-peak/super-off)    │
│  │   ├─ Configure heavy task scheduling windows                 │
│  │   └─ Estimated monthly energy cost for SLATE operations     │
│  └─ "Your SLATE is tuned for [profile name]"                   │
│                                                                  │
│  Phase 8: INSTALL (Dependency Setup)                            │
│  ├─ Animated installation with progress rings                   │
│  ├─ Parallel install visualization                              │
│  ├─ Package reuse detection (scan-first ethos)                  │
│  └─ Each install step shows the system it enables               │
│                                                                  │
│  Phase 9: FORKING (If New SLATE)                                │
│  ├─ Creative Commons licensing explanation                      │
│  ├─ Financial distribution model overview                       │
│  ├─ Fork creation with custom branding                          │
│  ├─ README generation with project description                  │
│  ├─ GitHub Pages setup                                          │
│  └─ Custom morph configuration                                  │
│                                                                  │
│  Phase 10: EDUCATION (SLATE Academy)                            │
│  ├─ Interactive system map tour                                  │
│  ├─ "Morphs" — what they are and how to build them              │
│  ├─ Plugin SDK overview with live code example                  │
│  ├─ Workflow Hub demonstration                                   │
│  ├─ Dashboard feature walkthrough                               │
│  └─ AI agent capability showcase                                │
│                                                                  │
│  Phase 11: VALIDATION (System Check)                            │
│  ├─ Full ecosystem health check                                 │
│  ├─ Each system lights up green on the blueprint                │
│  ├─ AI runs a sample task to prove functionality                │
│  └─ Performance score vs benchmark                              │
│                                                                  │
│  Phase 12: LAUNCH                                               │
│  ├─ Celebration animation (gears + starburst)                   │
│  ├─ System summary card                                         │
│  ├─ "Your SLATE is ready. What would you like to build?"       │
│  └─ Dashboard opens with full system view                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 Path: SLATE Developer

For users contributing to the main S.L.A.T.E. project:

```yaml
path: slate_developer
setup:
  - Clone/verify main repository
  - Configure upstream remote
  - Install full development dependencies
  - Setup pre-commit hooks
  - Enable all testing systems
  - Configure CI/CD runner (self-hosted)
  - Setup code review AI agents
  - Import existing task backlog from tech tree
permissions:
  default_tier: 3  # DEVELOPER
  can_push_to_main: false  # PR-only
  runner_role: contributor
```

### 3.4 Path: A New SLATE (Fork + Morph)

For users creating their own project powered by SLATE:

```yaml
path: new_slate
setup:
  - Fork the repository
  - Interactive project naming ceremony
  - Custom README generation (AI-powered)
  - Custom GitHub Pages theme selection
  - Project goal definition (AI interview)
  - Morph configuration
    - Which SLATE systems to keep
    - Which to disable
    - Custom branding colors/logo
  - Creative Commons contract acceptance
  - Upstream tracking configuration
  - Custom model training preparation

morph_config:
  project_name: "{{ user_input }}"
  description: "{{ ai_generated }}"
  primary_color: "{{ user_selected }}"
  logo: "{{ ai_generated_or_user_uploaded }}"
  active_systems:
    - core: true        # Always on
    - dashboard: true   # UI required
    - ollama: optional
    - gpu: optional
    - runner: optional
    - docker: optional
    - kubernetes: false # Usually not needed
  forking:
    upstream_tracking: true
    auto_sync: weekly
    conflict_strategy: preserve_morph
```

---

## 4. System Benchmarking

### 4.1 Benchmark Suite

```python
class SlateBenchmark:
    """
    Comprehensive system profiling for optimal SLATE configuration.
    
    Runs during onboarding Phase 6 and can be re-run anytime via
    @slate /benchmark or dashboard /settings/benchmark.
    """
    
    benchmarks = {
        "gpu_inference": {
            "description": "Ollama inference speed",
            "metric": "tokens/second",
            "method": "Run 3 inference passes with slate-fast, measure avg t/s",
            "duration": "~30 seconds",
        },
        "gpu_vram": {
            "description": "Available VRAM for model loading",
            "metric": "GB available",
            "method": "Query nvidia-smi for free memory per GPU",
            "duration": "~2 seconds",
        },
        "gpu_thermal": {
            "description": "GPU thermal headroom",
            "metric": "°C under load vs throttle point",
            "method": "Run 2-min inference loop, track temperature curve",
            "duration": "~120 seconds",
        },
        "cpu_multithread": {
            "description": "CPU parallel processing capability",
            "metric": "tasks/second",
            "method": "Run parallel JSON parsing + code analysis",
            "duration": "~15 seconds",
        },
        "storage_io": {
            "description": "Disk read/write speed",
            "metric": "MB/s read, MB/s write",
            "method": "Sequential + random I/O test on workspace drive",
            "duration": "~10 seconds",
        },
        "memory_bandwidth": {
            "description": "System memory throughput",
            "metric": "GB/s",
            "method": "Large array copy + transformation",
            "duration": "~5 seconds",
        },
        "network_latency": {
            "description": "GitHub API + Ollama response time",
            "metric": "ms round-trip",
            "method": "10 pings to each endpoint",
            "duration": "~10 seconds",
        },
    }
```

### 4.2 Performance Profile Generation

After benchmarks complete, SLATE generates a **Performance Profile Card**:

```
╔═══════════════════════════════════════════════════════════════╗
║              SLATE PERFORMANCE PROFILE                        ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  System: Dan's Workstation                                    ║
║  Profile: HIGH PERFORMANCE                                    ║
║  Score: 94 / 100                                             ║
║                                                               ║
║  GPU ████████████████████████████████░░ 92%                   ║
║  ├─ Inference: 45.2 tok/s (excellent)                        ║
║  ├─ VRAM: 32GB total (2x 16GB RTX 5070 Ti)                  ║
║  └─ Thermal: 72°C peak (18°C headroom)                       ║
║                                                               ║
║  CPU █████████████████████████████████░ 96%                   ║
║  ├─ Threads: 24 logical cores                                ║
║  └─ Multi-task: 187 tasks/sec                                ║
║                                                               ║
║  Storage ████████████████████████████░░░ 88%                  ║
║  ├─ Read: 3,200 MB/s (NVMe)                                 ║
║  └─ Write: 2,800 MB/s                                        ║
║                                                               ║
║  Recommended Configuration:                                   ║
║  ├─ Models: slate-coder (12B) + slate-planner (7B)           ║
║  ├─ Concurrent tasks: 4                                      ║
║  ├─ GPU split: 50/50 dual-GPU                                ║
║  └─ Thermal policy: balanced                                  ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
```

### 4.3 Thermal & Performance Policies

```yaml
thermal_policies:
  aggressive:
    description: "Maximum performance, higher temps"
    gpu_power_limit: 100%
    concurrent_models: 2
    fan_curve: aggressive
    throttle_temp: 90°C
    
  balanced:
    description: "Good performance, quiet operation"
    gpu_power_limit: 85%
    concurrent_models: 2
    fan_curve: balanced
    throttle_temp: 82°C
    
  quiet:
    description: "Lower performance, minimal noise"
    gpu_power_limit: 70%
    concurrent_models: 1
    fan_curve: silent
    throttle_temp: 75°C
    
  endurance:
    description: "Optimized for long-running tasks"
    gpu_power_limit: 75%
    concurrent_models: 1
    fan_curve: balanced
    throttle_temp: 78°C
    sustained_boost: false
```

---

## 4A. Token Counter & Throughput Monitor

### 4A.1 Overview

SLATE includes an **objective, always-on token counter** that measures all local AI inference operations. This is the system's odometer — it counts every token generated by Ollama, tracks throughput over time, and provides per-agent attribution so users can see exactly what their AI systems are doing.

### 4A.2 What is Counted

| Metric | Source | Description |
|--------|--------|-------------|
| **Prompt Tokens** | Ollama API response | Tokens sent TO the model |
| **Completion Tokens** | Ollama API response | Tokens generated BY the model |
| **Total Tokens** | Sum | Lifetime and per-session totals |
| **Tokens/Second** | Computed | Real-time inference throughput |
| **Model** | Ollama API response | Which model was used |
| **Agent** | Request context | Which AI agent initiated the request |
| **GPU** | nvidia-smi correlation | Which GPU served the request |
| **Energy Cost** | Computed | Estimated electrical cost (see §4B) |

### 4A.3 Token Counter Architecture

```python
class SlateTokenCounter:
    """
    Objective AI inference metering system.
    
    Every Ollama call in the SLATE ecosystem is routed through this
    counter. It intercepts the response metadata to extract token
    counts without adding latency to inference.
    
    Data is persisted to .slate_analytics/token_ledger.jsonl
    (append-only ledger, one JSON line per inference call).
    """
    
    def record(self, event: InferenceEvent):
        """
        Record a single inference event.
        
        InferenceEvent:
            timestamp: datetime
            agent: str          # "antigravity", "copilot", "claude", "workflow"
            model: str          # "slate-coder", "slate-fast", "slate-planner"
            prompt_tokens: int
            completion_tokens: int
            duration_ms: int
            gpu_id: int
            temperature: float  # GPU temp at time of inference
            energy_cost_usd: float  # Estimated from energy config
        """
        pass
    
    def get_throughput(self, window: str = "1h") -> ThroughputReport:
        """
        Calculate throughput metrics over a time window.
        
        Returns:
            total_tokens: int
            tokens_per_second: float
            tokens_per_minute_avg: float
            calls_count: int
            models_used: Dict[str, int]  # model -> token count
            agents_used: Dict[str, int]  # agent -> token count
            gpu_utilization: Dict[int, float]  # gpu_id -> % used
        """
        pass
    
    def get_lifetime_stats(self) -> LifetimeStats:
        """
        All-time cumulative statistics.
        
        Returns:
            total_tokens_generated: int
            total_inference_calls: int
            total_gpu_hours: float
            total_energy_cost_usd: float
            first_inference: datetime
            busiest_day: date
            favorite_model: str
            most_active_agent: str
        """
        pass
```

### 4A.4 Token Counter Dashboard Widget

```
╔═══════════════════════════════════════════════════════════════╗
║              SLATE INFERENCE MONITOR                          ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  THROUGHPUT (Last 1h)                                        ║
║  ┌─────────────────────────────────────────────────────┐     ║
║  │  ▄ ▅ █ ▇ ▅ ▃ ▂ ▄ ▆ █ ▇ ▄ ▃ ▂ ▅ ▇ █ ▆ ▄ ▃       │     ║
║  │  ▀ ▀ ▀ ▀ ▀ ▀ ▀ ▀ ▀ ▀ ▀ ▀ ▀ ▀ ▀ ▀ ▀ ▀ ▀ ▀       │     ║
║  │  11:00          11:30          12:00               │     ║
║  └─────────────────────────────────────────────────────┘     ║
║  Current: 42.3 tok/s │ Avg: 38.7 tok/s │ Peak: 51.2 tok/s  ║
║                                                               ║
║  SESSION TOTALS                                              ║
║  ├─ Prompt tokens:     │ 47,283                              ║
║  ├─ Completion tokens: │ 12,891                              ║
║  ├─ Total:             │ 60,174                              ║
║  ├─ Inference calls:   │ 234                                 ║
║  └─ Est. energy cost:  │ $0.03                               ║
║                                                               ║
║  PER-AGENT BREAKDOWN                                        ║
║  ├─ Antigravity  ████████████████░░░░ 41%  (24,671 tok)     ║
║  ├─ Copilot      █████████░░░░░░░░░░░ 23%  (13,840 tok)     ║
║  ├─ Claude       ████████░░░░░░░░░░░░ 20%  (12,035 tok)     ║
║  └─ Workflow     ██████░░░░░░░░░░░░░░ 16%  ( 9,628 tok)     ║
║                                                               ║
║  LIFETIME                                                    ║
║  ├─ Total tokens:      │ 14,283,947                         ║
║  ├─ GPU hours:         │ 127.4h                              ║
║  └─ Energy cost (MTD): │ $4.72                               ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
```

### 4A.5 Token Ledger Format

Append-only JSONL file at `.slate_analytics/token_ledger.jsonl`:

```jsonl
{"ts":"2026-02-09T12:01:23Z","agent":"antigravity","model":"slate-coder","prompt_tok":312,"completion_tok":87,"dur_ms":2140,"gpu":0,"temp_c":68.5,"cost_usd":0.00012}
{"ts":"2026-02-09T12:01:25Z","agent":"copilot","model":"slate-fast","prompt_tok":89,"completion_tok":234,"dur_ms":1820,"gpu":1,"temp_c":65.2,"cost_usd":0.00009}
```

### 4A.6 Access Points

| Surface | Access |
|---------|--------|
| **Dashboard** | `/monitoring/tokens` — Live throughput chart + totals |
| **VSCode** | `@slate /tokens` — Quick summary in chat |
| **CLI** | `slate tokens [--today \| --week \| --lifetime]` |
| **API** | `GET /api/tokens/throughput?window=1h` |
| **Status Bar** | VSCode status bar shows live tok/s indicator |

---

## 4B. Energy-Aware Scheduling

### 4B.1 Overview

SLATE can integrate with the user's **electrical provider billing schedule** to automatically shift heavy compute operations (batch inference, model training, CI builds, nightly workflows) to **off-peak hours** when electricity is cheapest.

During onboarding (Phase 7: Tuning), the user can optionally provide their location and electrical provider. SLATE then:
1. Looks up the provider's rate schedule
2. Maps rate tiers to SLATE operation categories
3. Builds an optimal scheduling calendar
4. Estimates monthly costs

### 4B.2 Onboarding Energy Setup

```
┌─────────────────────────────────────────────────────────────────┐
│  Phase 7: TUNING — Energy Configuration (Optional)              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  🔌 Would you like SLATE to optimize for your electricity       │
│     billing schedule?                                            │
│                                                                  │
│     This lets SLATE schedule heavy operations (CI builds,       │
│     batch AI inference, model training) during your cheapest    │
│     billing windows.                                             │
│                                                                  │
│  ┌───────────────────────────────────────────────────────┐      │
│  │  📍 Location                                          │      │
│  │  ZIP Code or City: [ 19103_____________ ]              │      │
│  │                                                        │      │
│  │  ⚡ Electrical Provider                                │      │
│  │  [ PECO Energy (Philadelphia) ▼ ]                      │      │
│  │                                                        │      │
│  │  Detected Rate Plan: Time-of-Use (TOU)                │      │
│  │                                                        │      │
│  │  Rate Schedule:                                        │      │
│  │  ├─ SUPER OFF-PEAK  12am - 6am    $0.04/kWh  🟢      │      │
│  │  ├─ OFF-PEAK        6am - 2pm     $0.08/kWh  🟡      │      │
│  │  ├─ PEAK            2pm - 7pm     $0.22/kWh  🔴      │      │
│  │  └─ OFF-PEAK        7pm - 12am    $0.08/kWh  🟡      │      │
│  │                                                        │      │
│  │  SLATE Scheduling Preview:                             │      │
│  │  ┌─────────────────────────────────────────────┐      │      │
│  │  │ 12a  3a  6a  9a  12p  3p  6p  9p  12a      │      │      │
│  │  │ ████ ▓▓  ░░  ░░  ░░   ▒▒  ▒▒  ░░  ████    │      │      │
│  │  │ HEAVY─┘  NORMAL──────  LIGHT──┘  NORMAL     │      │      │
│  │  └─────────────────────────────────────────────┘      │      │
│  │                                                        │      │
│  │  Estimated monthly cost: $4.72 (vs $11.30 unoptimized)│      │
│  │  Savings: ~58%                                         │      │
│  └───────────────────────────────────────────────────────┘      │
│                                                                  │
│  [ Skip — Run Anytime ]          [ Apply Energy Schedule ]      │
│                                                                  │
│  🤖 "Smart scheduling can cut your electricity costs by over   │
│     50%. Your heavy GPU tasks will run while you sleep!"        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4B.3 Energy Configuration

Stored in `.slate_config/energy.yaml`:

```yaml
# SLATE Energy-Aware Scheduling Configuration
# Modified: 2026-02-09T12:07:00-05:00 | Gemini
# NOTE: All AIs modifying this file must add a dated comment.

energy:
  enabled: true
  
  # User location (for provider lookup + timezone)
  location:
    zip_code: "19103"
    timezone: "America/New_York"
  
  # Electrical provider
  provider:
    name: "PECO Energy"
    plan: "Time-of-Use (TOU)"
    rates:
      super_off_peak:
        hours: [0, 1, 2, 3, 4, 5]  # 12am-6am
        cost_per_kwh: 0.04
      off_peak:
        hours: [6, 7, 8, 9, 10, 11, 12, 13, 19, 20, 21, 22, 23]
        cost_per_kwh: 0.08
      peak:
        hours: [14, 15, 16, 17, 18]  # 2pm-7pm
        cost_per_kwh: 0.22
  
  # System power draw estimates (watts)
  power_draw:
    idle: 120              # System idle
    single_gpu_inference: 250  # One GPU active
    dual_gpu_inference: 450    # Both GPUs active
    full_load: 650             # GPU + CPU + storage
  
  # Operation scheduling
  schedule:
    heavy_operations:  # Model training, batch inference, CI builds
      prefer: super_off_peak
      allowed: [super_off_peak, off_peak]
      forbidden: [peak]
    
    normal_operations:  # Interactive inference, code analysis
      prefer: off_peak
      allowed: [super_off_peak, off_peak, peak]  # always available
      forbidden: []
    
    light_operations:  # Documentation, GitHub sync, status checks
      prefer: any
      allowed: [super_off_peak, off_peak, peak]
      forbidden: []
  
  # Monthly budget alert
  budget:
    monthly_limit_usd: 25.00
    alert_at_percent: 80
    hard_cap: false  # If true, SLATE pauses non-essential ops at limit
```

### 4B.4 Energy Scheduler Engine

```python
class SlateEnergyScheduler:
    """
    Energy-aware task scheduling engine.
    
    Classifies every SLATE operation into heavy/normal/light,
    checks the current rate tier, and either:
    - Executes immediately (if allowed in current tier)
    - Queues for the next allowed window
    - Warns the user about cost implications
    """
    
    def classify_operation(self, operation: str) -> str:
        """
        Classify operation as 'heavy', 'normal', or 'light'.
        
        Heavy: nightly CI, model training, batch inference,
               benchmark runs, Docker builds
        Normal: Interactive inference, code analysis, PR review
        Light: Git sync, status checks, documentation
        """
        pass
    
    def current_rate_tier(self) -> str:
        """Returns current rate tier based on local time."""
        pass
    
    def should_execute(self, operation: str) -> ScheduleDecision:
        """
        Returns:
            execute_now: bool
            reason: str
            next_window: Optional[datetime]  # If deferred
            cost_estimate: float             # USD for this operation
        """
        pass
    
    def queue_for_window(self, operation: str, window: str):
        """Queue an operation for the next matching rate window."""
        pass
    
    def estimate_monthly_cost(self) -> MonthlyCostEstimate:
        """
        Based on historical token ledger data:
        - What did last month cost?
        - What would it cost without scheduling?
        - Projected cost for current month
        """
        pass


class EnergyProviderDatabase:
    """
    Database of US electrical providers and their rate schedules.
    
    Initially covers major metro providers. Community can contribute
    additional providers via SLATE Discussions.
    """
    
    def lookup_by_zip(self, zip_code: str) -> List[Provider]:
        """Find providers serving a ZIP code."""
        pass
    
    def get_rate_schedule(self, provider: str, plan: str) -> RateSchedule:
        """Get the rate tiers for a specific provider/plan."""
        pass
    
    # Initial provider list:
    providers = {
        "PECO Energy": {"region": "Philadelphia, PA", "type": "TOU"},
        "ComEd": {"region": "Chicago, IL", "type": "TOU"},
        "PG&E": {"region": "California", "type": "TOU"},
        "Con Edison": {"region": "New York, NY", "type": "TOU"},
        "Duke Energy": {"region": "Southeast US", "type": "TOU"},
        "Xcel Energy": {"region": "Colorado/Minnesota", "type": "TOU"},
        "SCE": {"region": "Southern California", "type": "TOU"},
        "Dominion Energy": {"region": "Virginia", "type": "TOU"},
        "AEP": {"region": "Ohio/Texas", "type": "TOU"},
        "Entergy": {"region": "Gulf States", "type": "flat"},
    }
```

### 4B.5 Energy Dashboard Widget

```
╔═══════════════════════════════════════════════════════════════╗
║              SLATE ENERGY MONITOR                             ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  CURRENT RATE: 🟡 OFF-PEAK ($0.08/kWh)                       ║
║  Next window:  🟢 SUPER OFF-PEAK in 4h 23m (12:00am)        ║
║                                                               ║
║  TODAY'S SCHEDULE                                            ║
║  ┌─────────────────────────────────────────────────────┐     ║
║  │ 12a  3a  6a  9a  12p  3p  6p  9p  12a              │     ║
║  │ 🟢🟢 🟢🟢 🟡🟡 🟡🟡 🟡🟡 🔴🔴 🔴🔴 🟡🟡 🟡🟡      │     ║
║  │ ▲▲▲▲              ▲                     NOW         │     ║
║  │ Heavy ops ran     Normal inference                   │     ║
║  └─────────────────────────────────────────────────────┘     ║
║                                                               ║
║  QUEUED OPERATIONS (waiting for super-off-peak)              ║
║  ├─ Nightly CI build           → 12:00am                    ║
║  ├─ Model fine-tune (slate-coder) → 12:30am                 ║
║  └─ Batch spec-kit analysis    → 1:00am                     ║
║                                                               ║
║  COST THIS MONTH                                             ║
║  ├─ Current:     $3.47 / $25.00 budget                       ║
║  ├─ Projected:   $8.20 (within budget)                       ║
║  ├─ Savings:     $6.80 vs unscheduled                        ║
║  └─ ████████████░░░░░░░░░░ 33% of budget used                ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
```

### 4B.6 Integration Points

| System | Energy Integration |
|--------|-------------------|
| **Workflow Hub** | Nightly/batch workflows deferred to super-off-peak |
| **Autonomous Runner** | Task loop respects energy windows |
| **Docker Runners** | GPU containers start/stop with rate schedule |
| **Model Training** | Fine-tuning jobs queued for cheapest window |
| **Benchmark Suite** | Re-benchmarks deferred to off-peak |
| **Token Counter** | Energy cost computed per inference call |
| **Dashboard** | Real-time rate tier indicator in header |

---

## 5. SLATE Morphs & Plugin SDK

### 5.1 What is a Morph?

A **SLATE Morph** is a forked SLATE project that has been customized for a specific purpose. The morph retains SLATE's core infrastructure but adapts the surface layer:

```
SLATE (Parent)
├── Core Engine (always inherited)
│   ├── Permission System
│   ├── AI Integration Layer
│   ├── Dashboard Framework
│   └── Install System
│
├── Morph Layer (user customizes)
│   ├── Project Branding (colors, logo, name)
│   ├── README & Documentation
│   ├── Active Systems Selection
│   ├── Custom Workflows
│   └── Domain-Specific Plugins
│
└── Plugin Layer (community extends)
    ├── SLATE Morphs SDK (@slate/morph-sdk)
    ├── Custom dashboard widgets
    ├── Workflow extensions
    └── AI model configurations
```

### 5.2 Morph Configuration

File: `.slate_config/morph.yaml`

```yaml
# SLATE Morph Configuration
# This defines how this fork differs from upstream SLATE

morph:
  name: "My Project Name"
  description: "AI-powered whatever"
  version: "0.1.0"
  upstream: "SynchronizedLivingArchitecture/S.L.A.T.E"
  created: "2026-02-09"
  
  # Branding
  brand:
    primary_color: "#3B82F6"      # Override SLATE's #B85A3C
    secondary_color: "#1E40AF"
    surface_color: "#0F172A"
    logo_path: ".slate_identity/custom_logo.svg"
    favicon_path: ".slate_identity/favicon.ico"
    project_title: "My Awesome Project"
    tagline: "Built with SLATE"
    
  # Active systems
  systems:
    core: true
    dashboard: true
    ollama: true
    gpu_compute: true
    github_runner: false
    docker: false
    kubernetes: false
    spec_kit: true
    avatar_3d: false
    
  # Protected paths (won't be overwritten by upstream sync)
  protected_paths:
    - README.md
    - .slate_config/morph.yaml
    - .slate_identity/
    - docs/pages/index.html
    - "custom/**"
    
  # Upstream sync preferences
  sync:
    auto: true
    frequency: weekly
    strategy: preserve_morph  # or: prefer_upstream, manual_merge
    notify_on_conflict: true
```

### 5.3 SLATE Morph SDK

```python
# @slate/morph-sdk — Python SDK for building SLATE Morphs

from slate_morph_sdk import Morph, Widget, Workflow, Plugin

class MyMorph(Morph):
    """Custom SLATE Morph definition."""
    
    name = "My Project"
    version = "0.1.0"
    
    # Custom dashboard widgets
    widgets = [
        Widget("project-status", template="widgets/status.html"),
        Widget("custom-metrics", template="widgets/metrics.html"),
    ]
    
    # Custom workflows
    workflows = [
        Workflow("daily-report", schedule="0 9 * * *", script="scripts/report.py"),
    ]
    
    # Custom plugins
    plugins = [
        Plugin("my-data-source", entrypoint="plugins/datasource.py"),
    ]
    
    def on_install(self, context):
        """Called during morph setup."""
        pass
    
    def on_update(self, context, upstream_changes):
        """Called when upstream SLATE is updated."""
        pass
    
    def on_benchmark(self, context, results):
        """Called after system benchmark — customize based on results."""
        pass
```

---

## 6. Creative Commons & Financial Distribution

### 6.1 Forking Contract

When a user forks SLATE, they are presented with the **Creating Commons Contract**:

```
╔═══════════════════════════════════════════════════════════════╗
║            SLATE CREATING COMMONS CONTRACT                    ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  License: Creative Commons Attribution-ShareAlike 4.0         ║
║                                                               ║
║  By forking SLATE, you agree to:                             ║
║                                                               ║
║  1. ATTRIBUTION                                              ║
║     Your project must credit SLATE as its foundation          ║
║     "Built with S.L.A.T.E." badge in README                  ║
║                                                               ║
║  2. SHARE-ALIKE                                              ║
║     Improvements to core SLATE systems should be              ║
║     contributed back upstream via Pull Requests                ║
║                                                               ║
║  3. FINANCIAL DISTRIBUTION                                   ║
║     If your morph generates revenue:                          ║
║     ├─ 5% → SLATE Foundation (infrastructure maintenance)    ║
║     ├─ 10% → Upstream Contributors (weighted by commits)     ║
║     └─ 85% → Morph Owner (you)                              ║
║                                                               ║
║  4. COMMUNITY PARTICIPATION                                  ║
║     Morphs are encouraged to participate in:                  ║
║     ├─ Monthly community showcases                           ║
║     ├─ Shared model training pools                           ║
║     └─ Cross-morph plugin ecosystem                          ║
║                                                               ║
║  Benefits You Receive:                                        ║
║  ├─ Upstream security patches auto-merged                    ║
║  ├─ Access to SLATE model training infrastructure            ║
║  ├─ Featured in SLATE ecosystem directory                    ║
║  ├─ Community support via GitHub Discussions                 ║
║  └─ Revenue share from upstream plugin marketplace           ║
║                                                               ║
║  [ I Accept ]                    [ Learn More ]               ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
```

### 6.2 Revenue Tracking

```python
class RevenueDistribution:
    """
    Tracks and distributes revenue from SLATE morphs.
    
    Revenue events are reported via the SLATE API.
    Distribution is calculated monthly and settled quarterly.
    """
    
    distribution_model = {
        "foundation": 0.05,       # 5% to SLATE infrastructure
        "upstream_contributors": 0.10,  # 10% to code contributors
        "morph_owner": 0.85,      # 85% to the morph creator
    }
    
    def calculate_contributor_shares(self, period):
        """
        Weight upstream contributor shares by:
        - Lines of code contributed
        - PR reviews performed
        - Issues resolved
        - Documentation written
        """
        pass
```

---

## 7. Update & Conflict Resolution System

### 7.1 SLATE Update Process

When upstream SLATE releases an update:

```
┌─────────────────────────────────────────────────────────────────┐
│                  SLATE UPDATE PROCESS                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. DETECTION                                                    │
│  ├─ Webhook notification from upstream                          │
│  ├─ Scheduled check (configurable, default: daily)              │
│  └─ Manual: @slate /update check                                │
│                                                                  │
│  2. ANALYSIS                                                     │
│  ├─ AI reads upstream changelog                                 │
│  ├─ Diff analysis against current morph                         │
│  ├─ Conflict prediction                                         │
│  └─ Impact assessment ("3 files conflict, 47 clean merge")     │
│                                                                  │
│  3. PREVIEW                                                      │
│  ├─ Interactive diff viewer in dashboard                        │
│  ├─ AI explains each change        │
│  ├─ Morph-impact highlighting                                   │
│  └─ "This update improves GPU scheduling — safe for your morph"│
│                                                                  │
│  4. MERGE STRATEGY                                               │
│  ├─ AUTO: Clean merges applied immediately                      │
│  ├─ ASSIST: AI resolves simple conflicts                        │
│  ├─ MANUAL: User reviews complex conflicts                      │
│  └─ SKIP: User defers this update                               │
│                                                                  │
│  5. VALIDATION                                                   │
│  ├─ Full test suite runs post-merge                             │
│  ├─ Benchmark comparison (before/after)                         │
│  ├─ Morph config validation                                     │
│  └─ Rollback available for 7 days                               │
│                                                                  │
│  6. REPORT                                                       │
│  ├─ Update summary in dashboard                                 │
│  ├─ Changelog entry auto-generated                              │
│  └─ Notification: "SLATE updated to v2.4.1 — 0 conflicts"     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Conflict Resolution AI

```python
class MorphConflictResolver:
    """
    AI-powered conflict resolution that protects morph identity.
    
    Key principle: The user's morph is ALWAYS the priority.
    Upstream changes to core systems are merged; upstream changes
    that would alter the morph identity are flagged for review.
    """
    
    def classify_conflict(self, file_path, upstream_change, morph_change):
        """
        Returns one of:
        - SAFE_MERGE: Core system update, no morph impact
        - MORPH_DIVERGENCE: Change would alter morph identity
        - FEATURE_CONFLICT: Both sides modified same feature
        - DEPENDENCY_CONFLICT: Package version mismatch
        """
        pass
    
    def suggest_resolution(self, conflict):
        """
        AI generates a merge resolution that:
        1. Preserves the morph's custom identity
        2. Incorporates the upstream improvement
        3. Explains the resolution to the user
        """
        pass
    
    def guard_morph_identity(self, merge_result):
        """
        Post-merge validation:
        - Does README still reflect the morph's project?
        - Are custom colors/branding preserved?
        - Are morph-specific workflows intact?
        - Is the morph config still valid?
        """
        pass
```

---

## 8. Unified Theme & Token System

### 8.1 Token Hierarchy

```
design-tokens.json (SINGLE SOURCE OF TRUTH)
    │
    ├── CSS Variables ──────── All web surfaces
    │   ├── dashboard/static/tokens.css
    │   ├── plugins/slate-copilot/webview.css
    │   ├── docs/pages/style.css
    │   └── .slate_identity/theme.css
    │
    ├── Python Constants ───── Backend generation
    │   └── slate/design_tokens.py
    │
    ├── VSCode Theme ────────── Editor theming
    │   └── plugins/slate-copilot/themes/slate-dark.json
    │
    ├── GitHub Labels ────────── Issue/PR colors
    │   └── .github/labels.yml
    │
    ├── Morph Overrides ──────── Custom project branding
    │   └── .slate_config/morph.yaml → brand section
    │
    └── CLI Colors ──────────── Terminal output
        └── slate_core/cli_theme.py
```

### 8.2 Token Schema

```json
{
  "$schema": "https://slate.dev/token-schema/v1",
  "version": "3.1.0",
  "locked": true,
  "tokens": {
    "color": {
      "primary": {
        "base": "#B85A3C",
        "light": "#D4785A",
        "dark": "#8B4530",
        "container": { "light": "#FFE4D9", "dark": "#5C2E1E" },
        "on": { "light": "#FFFFFF", "dark": "#2A1508" },
        "on-container": { "light": "#3D1E10", "dark": "#FFE4D9" }
      },
      "blueprint": {
        "bg": "#0D1B2A",
        "grid": "#1B3A4B",
        "accent": "#98C1D9",
        "node": "#E0FBFC"
      },
      "status": {
        "active": "#4CAF50",
        "pending": "#FF9800",
        "error": "#F44336",
        "info": "#2196F3",
        "inactive": "#6B7280"
      },
      "surface": {
        "light": "#FBF8F6",
        "dark": "#1A1816",
        "variant": { "light": "#F0EBE7", "dark": "#2A2624" }
      }
    },
    "typography": {
      "display": { "family": "Styrene A, Inter Tight, system-ui, sans-serif" },
      "body": { "family": "Tiempos Text, Georgia, serif" },
      "mono": { "family": "Cascadia Code, JetBrains Mono, Consolas, monospace" }
    },
    "spacing": {
      "xs": "4px", "sm": "8px", "md": "16px", "lg": "24px",
      "xl": "32px", "2xl": "48px", "3xl": "64px"
    },
    "elevation": {
      "0": "none",
      "1": "0 1px 2px rgba(0,0,0,0.05), 0 1px 3px rgba(0,0,0,0.1)",
      "2": "0 2px 4px rgba(0,0,0,0.05), 0 4px 8px rgba(0,0,0,0.1)",
      "3": "0 4px 8px rgba(0,0,0,0.08), 0 8px 16px rgba(0,0,0,0.12)",
      "4": "0 8px 16px rgba(0,0,0,0.1), 0 16px 32px rgba(0,0,0,0.15)",
      "5": "0 16px 32px rgba(0,0,0,0.12), 0 32px 64px rgba(0,0,0,0.18)"
    },
    "motion": {
      "easing": {
        "standard": "cubic-bezier(0.4, 0, 0.2, 1)",
        "decelerate": "cubic-bezier(0, 0, 0.2, 1)",
        "accelerate": "cubic-bezier(0.4, 0, 1, 1)",
        "spring": "cubic-bezier(0.34, 1.56, 0.64, 1)"
      },
      "duration": {
        "instant": "50ms", "fast": "150ms", "normal": "250ms",
        "slow": "400ms", "glacial": "600ms"
      }
    }
  }
}
```

### 8.3 Token Propagation Pipeline

```python
class TokenPropagator:
    """
    Reads design-tokens.json and propagates to all output formats.
    
    Run manually: python slate/propagate_tokens.py
    Run auto: Pre-commit hook, CI pipeline
    """
    
    outputs = [
        CSSOutput("dashboard/static/tokens.css"),
        CSSOutput("plugins/slate-copilot/media/tokens.css"),
        CSSOutput(".slate_identity/theme.css"),
        PythonOutput("slate/design_tokens.py"),
        VSCodeThemeOutput("plugins/slate-copilot/themes/slate-dark.json"),
        GitHubLabelsOutput(".github/labels.yml"),
        CLIThemeOutput("slate_core/cli_theme.py"),
    ]
    
    def propagate(self, tokens_path: str = "design-tokens.json"):
        """Read source tokens, generate all output formats."""
        tokens = json.load(open(tokens_path))
        for output in self.outputs:
            output.generate(tokens)
        
    def validate(self):
        """Ensure all outputs are in sync with source."""
        pass
```

---

## 9. Onboarding Animation Specification

### 9.1 Phase 1: Awakening Animation Sequence

```
Timeline (0 - 5000ms):

0ms     — Black screen
200ms   — Blueprint grid fades in (opacity 0→0.3)
500ms   — Center dot appears (scale 0→1, spring easing)
800ms   — First gear ring materializes (rotation 0°, fade in)
1200ms  — Second gear ring (counter-rotation, offset phase)
1600ms  — Starburst rays extend outward (each ray 100ms stagger)
2400ms  — "S.L.A.T.E." letters appear (typewriter effect, 80ms/char)
3200ms  — Subtitle fades in: "Synchronized Living Architecture..."
4000ms  — Status jewels pulse on (green, amber, blue, red)
4500ms  — AI voice bubble appears: "Initializing..."
5000ms  — Transition to Phase 2 (slide-up reveal)

CSS Animations:
  @keyframes gear-rotate { 0% { rotate: 0deg } 100% { rotate: 360deg } }
  @keyframes starburst-extend { 0% { scale: 0 } 100% { scale: 1 } }
  @keyframes jewel-pulse { 0%,100% { opacity: 1 } 50% { opacity: 0.5 } }
  @keyframes blueprint-scan { 0% { clip-path: inset(100% 0 0 0) } 100% { clip-path: inset(0) } }
```

### 9.2 Interactive Decision Points

At Phase 3 (IDENTITY), the UI presents an animated choice:

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│     ┌───────────────────────┐   ┌───────────────────────┐       │
│     │                       │   │                       │       │
│     │    ⚙️  SLATE           │   │    ✨ NEW SLATE       │       │
│     │    DEVELOPER          │   │    (Your Project)     │       │
│     │                       │   │                       │       │
│     │  Join the team.       │   │  Build something      │       │
│     │  Contribute to the    │   │  new. Fork SLATE      │       │
│     │  core SLATE project.  │   │  and morph it into    │       │
│     │                       │   │  YOUR creation.       │       │
│     │  • Full dev tools     │   │  • Custom branding    │       │
│     │  • CI/CD access       │   │  • Your own GitHub    │       │
│     │  • Code review AI     │   │  • AI-powered setup   │       │
│     │  • Tech tree tasks    │   │  • Plugin SDK         │       │
│     │                       │   │                       │       │
│     │  [ Choose This ]      │   │  [ Choose This ]      │       │
│     └───────────────────────┘   └───────────────────────┘       │
│                                                                  │
│     🤖 "Which path calls to you? Both lead to greatness."      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

Each card has:
- Hover: Elevation rise + glow effect
- Click: Card expands to fill screen, transition to next phase
- Background: Subtle gear rotation animation behind each card

---

## 10. Education System (SLATE Academy)

### 10.1 System Map

During Phase 10, users receive an interactive map of all SLATE systems:

```
                        ┌──────────┐
                        │  SLATE   │
                        │   CORE   │
                        └────┬─────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
      ┌─────┴─────┐   ┌─────┴─────┐   ┌─────┴─────┐
      │ AI Layer  │   │ Dev Layer │   │ Ops Layer │
      └─────┬─────┘   └─────┬─────┘   └─────┬─────┘
            │                │                │
    ┌───────┼───────┐  ┌─────┼─────┐  ┌──────┼──────┐
    │       │       │  │     │     │  │      │      │
  Ollama  GPUs  Models Code Tests Docs Runner Docker K8s
    │       │       │  │     │     │  │      │      │
  Local  Dual   Custom Agents CI  Wiki Self  Container Cluster
  LLMs  5070Ti Trained       CD    Kit Hosted  GPU

Each node is clickable → reveals description + demo
```

### 10.2 Morph Education

```markdown
## What are SLATE Morphs?

A **Morph** is your customized version of SLATE. Think of SLATE as a toolkit:

| SLATE Feature | What it does for your morph |
|---------------|----------------------------|
| Dashboard | Your project's control center |
| AI Agents | Custom AI for your domain |
| CI/CD | Automated testing & deployment |
| Spec-Kit | Documentation engine |
| GPU Compute | Local AI inference |

### Building Your First Plugin

```python
from slate_morph_sdk import Plugin

class MyPlugin(Plugin):
    name = "weather-dashboard"
    
    def register(self, slate):
        slate.add_widget("weather", self.render_weather)
    
    def render_weather(self, context):
        return "<div>Current: 72°F ☀️</div>"
```
```

---

## 11. Implementation Requirements

### 11.1 New Files

| File | Description |
|------|-------------|
| `.slate_config/permissions.yaml` | User permission configuration |
| `.slate_config/morph.yaml` | Morph identity configuration |
| `.slate_config/benchmark.json` | Latest benchmark results |
| `.slate_config/thermal.yaml` | Thermal policy configuration |
| `.slate_config/energy.yaml` | Energy-aware scheduling configuration |
| `.slate_analytics/token_ledger.jsonl` | Append-only inference token ledger |
| `design-tokens.json` | Single source of truth for all tokens |
| `slate/permission_gate.py` | Permission enforcement engine |
| `slate/benchmark_suite.py` | System benchmarking tools |
| `slate/token_counter.py` | Inference token counting & throughput monitoring |
| `slate/energy_scheduler.py` | Energy-aware task scheduling engine |
| `slate/energy_providers.py` | Electrical provider database & rate lookup |
| `slate/morph_manager.py` | Morph lifecycle management |
| `slate/conflict_resolver.py` | AI-powered merge conflict resolution |
| `slate/token_propagator.py` | Token system propagation pipeline |
| `slate/onboarding_engine.py` | Interactive onboarding orchestrator |
| `plugins/slate-copilot/src/onboardingView.ts` | VSCode onboarding webview |
| `plugins/slate-sdk/morph-sdk/` | SLATE Morph SDK package |

### 11.2 Modified Files

| File | Changes |
|------|---------|
| `install_slate.py` | Integrate new onboarding phases, benchmark, permissions |
| `plugins/slate-copilot/package.json` | Add onboarding view registration |
| `.github/workflows/workflow-hub.yml` | Add morph sync and update checks |
| `slate_startup.py` | Add permission gate initialization |
| `CONTRIBUTING.md` | Add morph contribution guidelines |

### 11.3 Implementation Priority

#### Phase 1: Foundation (Sprint 1)
- [ ] Create `design-tokens.json` source of truth
- [ ] Build `token_propagator.py`
- [ ] Create `permissions.yaml` schema
- [ ] Build `permission_gate.py`

#### Phase 2: Benchmarking & Metering (Sprint 2)
- [ ] Build `benchmark_suite.py`
- [ ] Build `token_counter.py` — inference metering
- [ ] Build `energy_scheduler.py` — rate-aware scheduling
- [ ] Build `energy_providers.py` — provider database
- [ ] Integration with install flow
- [ ] Performance profile generation
- [ ] Thermal policy system
- [ ] Token counter dashboard widget
- [ ] Energy schedule dashboard widget

#### Phase 3: Onboarding UI (Sprint 3-4)
- [ ] Phase 1-3 animations (Awakening, Discovery, Identity)
- [ ] Decision tree UI (Developer vs New SLATE)
- [ ] System selector toggle grid
- [ ] AI narration integration

#### Phase 4: Morph System (Sprint 5)
- [ ] `morph_manager.py`
- [ ] `morph.yaml` schema
- [ ] Fork + custom branding flow
- [ ] Creative Commons contract UI

#### Phase 5: Update System (Sprint 6)
- [ ] `conflict_resolver.py`
- [ ] Upstream change detection
- [ ] AI-powered merge resolution
- [ ] Morph identity guard

#### Phase 6: Education (Sprint 7)
- [ ] Interactive system map
- [ ] Plugin SDK documentation
- [ ] SLATE Academy content
- [ ] Achievement system

---

## 12. Success Metrics

| Metric | Target |
|--------|--------|
| Time to first onboard completion | < 10 minutes |
| User decision points | ≤ 5 meaningful choices |
| Benchmark accuracy | ±5% of manual measurement |
| Morph fork success rate | > 95% |
| Update conflict auto-resolution | > 80% |
| Theme token consistency | 100% across all surfaces |
| Permission enforcement accuracy | 100% |
| Onboarding animation frame rate | 60fps |
| Token counter accuracy | ±0.1% vs Ollama reported counts |
| Token ledger write latency | < 5ms (no inference slowdown) |
| Energy cost savings (with scheduling) | > 40% vs unscheduled |
| Energy provider coverage | Top 10 US metro providers at launch |

---

## 13. References

- **Spec 007**: SLATE Unified Design System (token definitions)
- **Spec 008**: SLATE Guided Experience (onboarding flow architecture)
- **Spec 010**: SLATE Generative Onboarding (AI narration system)
- **Spec 022**: SLATE Brand Identity (visual identity system)
- **CC-BY-SA 4.0**: https://creativecommons.org/licenses/by-sa/4.0/
- **M3 Material Design**: https://m3.material.io/
