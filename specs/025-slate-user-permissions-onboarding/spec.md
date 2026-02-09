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
4. **SLATE Morphs** — Forking SLATE into user-customized projects
5. **Update & Conflict Resolution** — Safe upstream sync with morph protection
6. **Unified Theme & Token System** — Single source of truth for all visual surfaces

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
│  Phase 7: TUNING (System Optimization)                          │
│  ├─ Auto-configure based on benchmark results                   │
│  ├─ GPU memory allocation strategy                              │
│  ├─ Ollama model selection (based on VRAM)                      │
│  ├─ Thermal throttle thresholds                                 │
│  ├─ Concurrent task limits                                      │
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
| `design-tokens.json` | Single source of truth for all tokens |
| `slate/permission_gate.py` | Permission enforcement engine |
| `slate/benchmark_suite.py` | System benchmarking tools |
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

#### Phase 2: Benchmarking (Sprint 2)
- [ ] Build `benchmark_suite.py`
- [ ] Integration with install flow
- [ ] Performance profile generation
- [ ] Thermal policy system

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

---

## 13. References

- **Spec 007**: SLATE Unified Design System (token definitions)
- **Spec 008**: SLATE Guided Experience (onboarding flow architecture)
- **Spec 010**: SLATE Generative Onboarding (AI narration system)
- **Spec 022**: SLATE Brand Identity (visual identity system)
- **CC-BY-SA 4.0**: https://creativecommons.org/licenses/by-sa/4.0/
- **M3 Material Design**: https://m3.material.io/
