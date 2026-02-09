# Specification: SLATE Brand Identity System
<!-- Auto-generated from specs/022-slate-brand-identity/spec.md -->
<!-- Generated: 2026-02-09T16:00:00+00:00 -->

| Property | Value |
|----------|-------|
| **Spec Id** | 022-slate-brand-identity |
| **Status** | specified |
| **Created** | 2026-02-09 |
| **Author** | ClaudeCode (Opus 4.6) |
| **Tech Tree Id** | brand-identity |

## Contents

- [Overview](#overview)
- [Brand Architecture](#brand-architecture)
  - [Brand Essence](#brand-essence)
  - [Visual Identity](#visual-identity)
  - [Brand Touchpoints](#brand-touchpoints)
- [Color System](#color-system)
- [Typography](#typography)
- [Iconography](#iconography)
- [Token System Integration](#token-system-integration)
- [Design Token Distribution](#design-token-distribution)
- [Implementation Requirements](#implementation-requirements)
- [Related Specifications](#related-specifications)

---

## Overview

Define the complete SLATE brand identity system that unifies all visual, verbal, and interactive touchpoints across the SLATE ecosystem: dashboard, GitHub Pages, wiki, VS Code extensions, documentation, and 3D avatar representation.

## Brand Architecture

### Brand Essence

```
SLATE = Synchronized Living Architecture for Transformation and Evolution
```

| Attribute | Value |
|-----------|-------|
| **Personality** | Precise, evolving, watchmaker-crafted, transparent |
| **Voice** | Technical yet approachable, systems-thinking, progress-oriented |
| **Aesthetic** | Watchmaker + Blueprint + Living System |
| **Philosophy** | "Systems evolve with progress" — beauty from function |

### Visual Identity

#### Logo System

| Variant | Usage | Format |
|---------|-------|--------|
| **Primary** | GitHub, dashboard header | SVG (starburst) |
| **Compact** | Favicons, small spaces | SVG (hexagon) |
| **Wordmark** | Documentation, wiki | SVG (logo + "S.L.A.T.E.") |
| **3D Avatar** | Interactive, social, onboarding | GLB (TRELLIS.2 generated) |
| **Animated** | Loading states, transitions | CSS/SVG animation |

### Brand Touchpoints

| Surface | Brand Expression |
|---------|-----------------|
| **GitHub Profile** | Logo, description, topics, social preview |
| **GitHub Pages** | Full brand with glassmorphism theme |
| **GitHub Wiki** | Branded sidebar, headers, navigation |
| **GitHub Projects** | Branded column headers, labels |
| **Dashboard** | Full watchmaker theme + schematic background |
| **VS Code** | SLATE Dark theme + schematic background |
| **Documentation** | Wordmark header + design tokens |
| **CLI Output** | Branded ASCII art + color codes |
| **3D Avatar** | TRELLIS.2 generated interactive representation |

## Color System

The SLATE color system is **locked** and distributed via design tokens:

```css
/* Primary Palette — Anthropic-inspired warm rust */
--brand-primary: #B85A3C;
--brand-primary-light: #D4785A;
--brand-primary-dark: #8B4530;

/* Blueprint Palette — Technical precision */
--brand-blueprint-bg: #0D1B2A;
--brand-blueprint-grid: #1B3A4B;
--brand-blueprint-accent: #4FC3F7;

/* Status Jewels — Watchmaker complications */
--brand-jewel-active: #4CAF50;
--brand-jewel-pending: #FF9800;
--brand-jewel-error: #F44336;
--brand-jewel-info: #2196F3;

/* Surface System */
--brand-surface-light: #FBF8F6;
--brand-surface-dark: #1A1816;
```

## Typography

| Use | Font Stack | Weight |
|-----|-----------|--------|
| Display | Styrene A, Inter Tight, system-ui | 700 |
| Body | Tiempos Text, Georgia, serif | 400 |
| Monospace | Cascadia Code, JetBrains Mono, Consolas | 400 |

## Iconography

| Icon Type | Style | Usage |
|-----------|-------|-------|
| **Gear** | Rotating when active | Processing indicators |
| **Jewel** | Color-coded gem | Status indicators |
| **Circuit** | Blueprint line art | System connections |
| **Flow** | Animated dash-array | Data paths |

## Token System Integration

The brand identity connects to the SLATE Token System for:
- Service identity verification (branded token prefixes: `slsvc_`, `slagt_`, etc.)
- Plugin authentication with brand-consistent naming
- API access with rate-limited brand endpoints

## Design Token Distribution

Design tokens are distributed to all surfaces from a single source of truth:

```
design-tokens.json (source of truth)
    |
    +-- design-tokens.css     (web surfaces)
    +-- design_tokens.py      (Python generation)
    +-- theme.css              (.slate_identity)
    +-- theme-locked.css       (.slate_identity)
    +-- VS Code theme          (plugins/slate-copilot)
    +-- GitHub Pages            (docs/pages/)
    +-- Wiki templates          (docs/wiki/)
```

## Implementation Requirements

1. **Brand Guidelines Document** — Complete visual style guide
2. **Token Distribution Pipeline** — Auto-update all surfaces when tokens change
3. **Social Preview Generator** — Programmatic GitHub social preview images
4. **Wiki Branding** — Styled sidebar, headers, and page templates
5. **CLI Branding** — ANSI-colored output matching brand palette
6. **3D Avatar Pipeline** — TRELLIS.2 integration for 3D brand representation

## Related Specifications

- **007-slate-design-system**: Unified design system with M3 + Anthropic art
- **012-watchmaker-3d-dashboard**: 3D dashboard with watchmaker aesthetic
- **013-engineering-drawing-theme**: ISO 128/IEC 60617 technical drawing system
- **014-watchmaker-golden-ratio-ui**: Fibonacci-based layout system
- **023-slate-avatar-system**: Avatar as brand embodiment
- **024-trellis-3d-integration**: 3D generation pipeline for brand assets

---
*Source: [specs/022-slate-brand-identity/spec.md](../../../specs/022-slate-brand-identity/spec.md)*
