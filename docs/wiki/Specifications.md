# SLATE Specifications
<!-- Modified: 2026-02-08T12:00:00Z | Author: Claude Opus 4.5 | Change: Add specs 013-019, new tracks, updated relationships -->

This page provides an overview of all SLATE specifications, their status, and relationships.

## Development Roadmap

<div align="center">

![SLATE Development Roadmap](../assets/development-roadmap.svg)

</div>

## Specification Lifecycle

```
DRAFT → SPECIFIED → PLANNED → IMPLEMENTING → COMPLETED
```

<table>
<tr>
<th>Status</th>
<th>Symbol</th>
<th>Description</th>
</tr>
<tr>
<td><span style="color:#4D4845">●</span> Draft</td>
<td><code>[ ]</code></td>
<td>Initial concept, gathering requirements</td>
</tr>
<tr>
<td><span style="color:#3B82F6">●</span> Specified</td>
<td><code>[s]</code></td>
<td>Full spec written, awaiting planning</td>
</tr>
<tr>
<td><span style="color:#60A5FA">●</span> Planned</td>
<td><code>[p]</code></td>
<td>Tasks created, ready for implementation</td>
</tr>
<tr>
<td><span style="color:#B85A3C">●</span> Implementing</td>
<td><code>[~]</code></td>
<td>Active development in progress</td>
</tr>
<tr>
<td><span style="color:#22C55E">●</span> Completed</td>
<td><code>[x]</code></td>
<td>Fully implemented and verified</td>
</tr>
</table>

## Active Specifications

### Design System Track

| # | Specification | Status | Description |
|---|---------------|--------|-------------|
| 005 | [Dashboard Monochrome Theme](Spec-005-Monochrome-Theme) | [x] Completed | Black and white base theme with minimal status colors |
| 006 | [Natural Theme System](Spec-006-Natural-Theme-System) | [x] Completed | Procedural dark/light slider with natural color palette |
| 007 | [Unified Design System](Spec-007-Design-System) | [x] Completed | M3 Material Design + Anthropic Geometric Art + Awwwards patterns |
| 013 | [Engineering Drawing Theme](Spec-013-Engineering-Theme) | [~] Implementing | ISO 128/IEC 60617 engineering drawing visual standards |
| 014 | [Golden Ratio UI](Spec-014-Golden-Ratio) | [~] Implementing | Watchmaker metaphor + golden ratio (phi) proportions |

### User Experience Track

| # | Specification | Status | Description |
|---|---------------|--------|-------------|
| 008 | [Guided Experience](Spec-008-Guided-Experience) | [x] Completed | AI-driven onboarding wizard with zero-config setup |
| 010 | [Generative Onboarding](Spec-010-Generative-Onboarding) | [x] Completed | AI-generated installation and setup flows |

### Integration Track

| # | Specification | Status | Description |
|---|---------------|--------|-------------|
| 009 | [Copilot Roadmap Awareness](Spec-009-Copilot-Roadmap-Awareness) | [x] Completed | @slate participant with dev cycle integration |

### Visualization Track

| # | Specification | Status | Description |
|---|---------------|--------|-------------|
| 011 | [Schematic Diagram SDK](Spec-011-Schematic-SDK) | [x] Completed | Circuit-board style architecture visualization |
| 012 | [Schematic GUI Layout](Spec-012-Schematic-GUI-Layout) | [~] Implementing | Dashboard-integrated schematic widgets with live updates |
| 012b | [Watchmaker 3D Dashboard](Spec-012-Watchmaker-3D) | [~] Implementing | Interactive 3D dashboard with gear animations and depth layers |

### Infrastructure Track

| # | Specification | Status | Description |
|---|---------------|--------|-------------|
| 015 | [Vendor Integration](Spec-015-Vendor-Integration) | [s] Specified | Multi-vendor SDK integration (OpenAI, Autogen, Semantic Kernel) |
| 016 | [Multi-Runner System](Spec-016-Multi-Runner) | [s] Specified | Distributed GitHub runner orchestration |
| 019 | [Dual GPU Manager](Spec-019-Dual-GPU) | [s] Specified | Dual RTX 5070 Ti load balancing and scheduling |

### SDK Track

| # | Specification | Status | Description |
|---|---------------|--------|-------------|
| 017 | [Claude Agent SDK](Spec-017-Claude-Agent-SDK) | [s] Specified | Claude Agent SDK integration for programmatic AI operations |

## Specification Relationships

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                           SLATE SPECIFICATION MAP                                 │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                         DESIGN SYSTEM TRACK                                  │ │
│  │                                                                              │ │
│  │  [005] Monochrome → [006] Natural → [007] Unified → [013] Engineering       │ │
│  │       Theme              Theme         Design         Drawing Theme         │ │
│  │                                          │                  │               │ │
│  │                                          └───────┬──────────┘               │ │
│  │                                                  ▼                          │ │
│  │                                          [014] Golden Ratio                 │ │
│  │                                          Watchmaker UI                      │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                       USER EXPERIENCE TRACK                                  │ │
│  │                                                                              │ │
│  │                 [008] Guided Experience → [010] Generative Onboarding       │ │
│  │                          │                                                   │ │
│  │                          └──────────────────────────────────────────────────┤ │
│  └──────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                        INTEGRATION TRACK                                     │ │
│  │                                                                              │ │
│  │                      [009] Copilot Roadmap Awareness                        │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                       VISUALIZATION TRACK                                    │ │
│  │                                                                              │ │
│  │         [011] Schematic SDK → [012] Schematic GUI → [012b] Watchmaker 3D    │ │
│  │                                        │                    │               │ │
│  │                                        └────────┬───────────┘               │ │
│  │                                                 ▼                           │ │
│  │                                    Integrates [013] + [014]                 │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                       INFRASTRUCTURE TRACK                                   │ │
│  │                                                                              │ │
│  │  [015] Vendor Integration ────────────────────────────────────────────────┐ │ │
│  │         │                                                                  │ │ │
│  │  [016] Multi-Runner ───────────────────────────────┐                      │ │ │
│  │         │                                          │                      │ │ │
│  │  [019] Dual GPU Manager ──────────────────────────┼──────────────────────┘ │ │
│  │                                                    │                        │ │
│  └────────────────────────────────────────────────────┼────────────────────────┘ │
│                                                       │                          │
│  ┌────────────────────────────────────────────────────┼────────────────────────┐ │
│  │                           SDK TRACK                │                         │ │
│  │                                                    ▼                         │ │
│  │                             [017] Claude Agent SDK                           │ │
│  │                                    │                                         │ │
│  │                   Uses [015] Vendor Integration for multi-SDK               │ │
│  └──────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                   │
└──────────────────────────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

### Color Philosophy

The design system evolved through three iterations:

1. **Spec 005**: Pure monochrome (black/white/gray) with minimal status colors
2. **Spec 006**: Natural earth tones with procedural interpolation
3. **Spec 007**: M3-inspired warm palette with Anthropic geometric influence

Final palette:
- Primary: `#B85A3C` (Anthropic-inspired warm rust)
- Surface: Natural earth tones
- Status: Semantic colors (success/warning/error/info)

### Architecture Principles

| Principle | Description |
|-----------|-------------|
| **Radiating Architecture** | Information flows outward from central focus points |
| **Dynamic Theming** | M3-style tonal palettes with procedural interpolation |
| **Human-Centered AI** | Warm, approachable aesthetics |
| **Geometric Precision** | Clean forms with mathematical relationships |
| **Living System** | UI that evolves with system state |

### Typography

```css
--slate-font-display: 'Styrene A', 'Inter Tight', system-ui, sans-serif;
--slate-font-body: 'Tiempos Text', 'Georgia', serif;
--slate-font-mono: 'Cascadia Code', 'JetBrains Mono', 'Consolas', monospace;
```

## Implementation Priority

### Phase 1: Foundation (Completed)
- [x] Monochrome base theme
- [x] Natural color palette
- [x] Theme slider system

### Phase 2: Design System (Completed)
- [x] M3 design tokens
- [x] Starburst logo generator
- [x] Component library
- [x] Animation system

### Phase 3: User Experience (Completed)
- [x] Guided mode overlay
- [x] AI narrator integration
- [x] Step execution engine
- [x] Error recovery

### Phase 4: Integration (Completed)
- [x] @slate Copilot participant
- [x] Dev cycle engine
- [x] Spec-Kit CLI
- [x] Token optimization
- [x] Generative onboarding

### Phase 5: Visualization (In Progress)
- [x] Schematic Diagram SDK
- [x] Blueprint theme system
- [~] Dashboard hero widgets
- [~] WebSocket live updates
- [~] Interactive schematic modals
- [~] Component hover tooltips
- [~] Watchmaker 3D dashboard

### Phase 6: Engineering Theme (In Progress)
- [~] ISO 128 line type standards
- [~] IEC 60617 component symbols
- [~] ASME Y14.44 reference designators
- [~] Golden ratio proportions
- [ ] Watchmaker UI components (gears, jewels, springs)

### Phase 7: Infrastructure (Specified)
- [s] Vendor SDK integration framework
- [s] Multi-runner orchestration
- [s] Dual GPU load balancing
- [ ] Runner health monitoring
- [ ] GPU memory scheduling

### Phase 8: SDK Integration (Specified)
- [s] Claude Agent SDK integration
- [ ] Programmatic AI operations
- [ ] Hook-based tool validation
- [ ] Session management
- [ ] Agent workflow automation

## Files by Specification

### Spec 005: Monochrome Theme
- `agents/slate_dashboard_server.py` (modified)

### Spec 006: Natural Theme System
- `agents/slate_dashboard_server.py` (modified)
- `.slate_identity/theme.css` (new)
- `docs/specs/design-inspiration.json` (new)

### Spec 007: Unified Design System
- `slate/design_tokens.py` (new)
- `slate/logo_generator/` (new)
- `.slate_identity/design-tokens.css` (new)
- `.slate_identity/logos/` (new)

### Spec 008: Guided Experience
- `slate/guided_mode.py` (new)
- `slate/guided_workflow.py` (new)
- `slate_web/guided_workflow_ui.py` (new)

### Spec 009: Copilot Roadmap Awareness
- `plugins/slate-copilot/src/tools.ts` (modified)
- `plugins/slate-copilot/src/slateParticipant.ts` (modified)
- `slate/dev_cycle_engine.py` (new)
- `slate/slate_spec_kit.py` (new)

### Spec 010: Generative Onboarding
- `slate/slate_generative_ui.py` (new)
- `slate_web/interactive_experience_ui.py` (new)

### Spec 011: Schematic Diagram SDK
- `slate/schematic_sdk/` (new directory)
- `slate/schematic_sdk/engine.py` (new)
- `slate/schematic_sdk/components.py` (new)
- `slate/schematic_sdk/theme.py` (new)
- `slate/schematic_sdk/layout.py` (new)
- `slate/schematic_sdk/svg_renderer.py` (new)
- `slate/schematic_sdk/library.py` (new)
- `slate/schematic_sdk/exporters.py` (new)

### Spec 012: Schematic GUI Layout
- `slate/schematic_api.py` (new)
- `slate_web/dashboard_schematics.py` (new)
- `slate_web/dashboard_template.py` (modified)

### Spec 012b: Watchmaker 3D Dashboard
- `slate/static/css/watchmaker.css` (new)
- `slate/static/css/3d-dashboard.css` (new)
- `slate/static/js/gear-animation.js` (new)
- `slate/static/js/depth-manager.js` (new)
- `slate/templates/dashboard-3d.html` (new)

### Spec 013: Engineering Drawing Theme
- `slate/schematic_sdk/theme.py` (modified)
- `slate/schematic_sdk/components.py` (modified)
- `.slate_identity/engineering-theme.css` (new)

### Spec 014: Golden Ratio UI
- `plugins/slate-copilot/src/slateUnifiedDashboardView.ts` (modified)
- `plugins/slate-copilot/themes/slate-dark-color-theme.json` (modified)
- `slate/schematic_sdk/theme.py` (modified)

### Spec 015: Vendor Integration
- `slate/vendor_integration.py` (new)
- `slate/vendor_autogen_sdk.py` (new)
- `slate/vendor_agents_sdk.py` (new)
- `vendor/` (submodules)

### Spec 016: Multi-Runner System
- `slate/multi_runner_manager.py` (new)
- `k8s/runners.yaml` (modified)

### Spec 017: Claude Agent SDK
- `slate/claude_agent_sdk_integration.py` (new)
- `slate/claude_code_manager.py` (modified)

### Spec 019: Dual GPU Manager
- `slate/gpu_manager.py` (modified)
- `slate/gpu_scheduler.py` (new)

## API Endpoints by Specification

### Design System (Spec 007)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/design/tokens` | GET | Get current design tokens |
| `/api/design/theme` | GET/POST | Theme configuration |
| `/api/logo/generate` | POST | Generate logo variant |

### Guided Experience (Spec 008)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/guided/start` | POST | Start guided mode |
| `/api/guided/status` | GET | Get current guided state |
| `/api/guided/step` | GET | Get current step details |
| `/api/guided/advance` | POST | Force advance to next step |

### Integration (Spec 009)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/devcycle/*` | GET/POST | Dev cycle state management |
| `/api/interactive/*` | GET/POST | Learning paths, progress |
| `/api/feedback/*` | GET/POST | Tool events, patterns |

### Generative UI (Spec 010)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/generative/experience` | GET | Get current experience state |
| `/api/generative/step` | POST | Execute generative step |

### Schematic SDK (Spec 011 & 012)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/schematic/system` | GET | Get system architecture schematic |
| `/api/schematic/live` | GET | Get live system state schematic |
| `/api/schematic/templates` | GET | List available templates |
| `/api/schematic/generate` | POST | Generate custom schematic |
| `/api/schematic/ws/live` | WS | WebSocket live updates |

### Watchmaker 3D Dashboard (Spec 012b)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/dashboard/3d/state` | GET | Get 3D dashboard state |
| `/api/dashboard/3d/layer` | GET | Get specific depth layer |
| `/api/dashboard/gear/status` | GET | Get gear animation status |

### Multi-Runner (Spec 016)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/runners/status` | GET | Get all runner status |
| `/api/runners/dispatch` | POST | Dispatch job to runner |
| `/api/runners/health` | GET | Health check for runners |

### GPU Manager (Spec 019)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/gpu/status` | GET | Get GPU cluster status |
| `/api/gpu/schedule` | POST | Schedule task on GPU |
| `/api/gpu/balance` | GET | Get load balancing metrics |

## Related Documentation

- [Architecture](Architecture) - System design overview
- [Getting Started](Getting-Started) - Installation guide
- [CLI Reference](CLI-Reference) - Command-line tools
