# SLATE-ATHENA Design System
# Modified: 2026-02-08T02:45:00Z | Author: COPILOT | Change: Create Athena branding and design principles

## Design Philosophy: "Wisdom Meets Precision"

Inspired by Athena, goddess of wisdom, strategy, and craftsmanship. Rooted in Greek architectural elegance—minimalist, structured, purposeful. Like the Parthenon's perfect proportions, every element serves a function.

---

## Core Principles

### 1. **Strategic Clarity**
- Information architecture mirrors military strategy (Athena's domain)
- No visual clutter; every element has purpose
- Clear hierarchy and decision trees (wisdom in action)

### 2. **Timeless Craftsmanship**
- Greek marble aesthetic: durable, elegant, ageless
- Modern minimalism with classical restraint
- Precision in every detail (like Armor Engine blueprint accuracy)

### 3. **Purposeful Automation**
- Automate the mundane, elevate the creative (Athena's gift to craftspeople)
- Voice-first interaction model (future Athena AI)
- Anticipatory intelligence without being intrusive

### 4. **Strategic Constraint**
- Limited palette (like ancient Greek pottery)
- Modular design (like Greek column orders: Doric, Ionic, Corinthian)
- Freedom within structure (games need rules to be fun)

---

## Color Palette: SLATE-ATHENA

### Primary Colors
- **Parthenon Gold** `#D4AF37` — Doric column wisdom, luxury restraint
- **Acropolis Gray** `#3A3A3A` — Marble stone foundation, strength
- **Aegean Deep** `#1A3A52` — Mediterranean depth, calm focus

### Secondary Colors
- **Owl Silver** `#B0B0B0` — Athena's owl, vigilance, clarity
- **Torch Flame** `#FF6B1A` — Sacred fire, purpose-driven energy
- **Olive Green** `#4A6741` — Ancient olive groves, patience + growth

### Accent Colors
- **Thunderbolt White** `#F8F8F8` — Zeus lineage, purity
- **Shadow Black** `#0D0D0D` — Strategic depth
- **Wisdom Bronze** `#6B4423` — Crafted metal, enduring value

### Semantic Colors
- Success: `#2D5F2E` (olive green)
- Warning: `#FF6B1A` (torch flame)
- Error: `#8B0000` (Spartan red)
- Info: `#1A3A52` (Aegean deep)

---

## Typography: "Classical Proportions"

### Typeface Stack (Web-Safe)
```
Headlines:    Georgia, 'Times New Roman', serif (classical elegance)
Body:         -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif (modern clarity)
Monospace:    'Monaco', 'Courier New', monospace (code precision)
```

### Sizes & Hierarchy
- **H1 (Acropolis)** 48px, 1.2 line-height, Parthenon Gold, font-weight 700
- **H2 (Decree)** 32px, 1.3 line-height, Acropolis Gray, font-weight 600
- **H3 (Inscription)** 24px, 1.4 line-height, Acropolis Gray, font-weight 600
- **Body (Wisdom)** 16px, 1.6 line-height, Acropolis Gray, font-weight 400
- **Caption (Engraving)** 12px, 1.5 line-height, Owl Silver, font-weight 400

---

## Iconography: "Sacred Symbols"

### Core Icons
- **Owl** — Wisdom, vigilance, Athena's familiar
- **Spear** — Purpose, direction, strategic focus
- **Olive Branch** — Peace, growth, solution
- **Greek Key** — Pattern, continuity, iterative refinement
- **Acropolis Silhouette** — Home, foundation, cultural identity
- **Torch** — Knowledge sharing, illumination

### Icon Style
- Minimalist, 2px stroke width
- SVG-based, scalable 16px-256px
- No fill; outline only (like ancient Greek line drawings)
- 45° angles where possible (mimic Greek architecture)

---

## Layout Grid: "Doric Proportions"

**24-column grid** (mimics classical architectural modules)
```
Desktop (1440px):  24 columns × 40px gutter × 60px margins
Tablet (768px):   12 columns × 32px gutter × 40px margins
Mobile (375px):   6 columns × 24px gutter × 16px margins
```

Gutter ratio: 2:1 (classic Greek proportion)

---

## Spacing & Whitespace: "Negative Space Wisdom"

Follow the "Rule of Thirds" (classical composition):
```
xs: 4px      (micro adjustment)
sm: 8px      (component padding)
md: 16px     (section spacing)
lg: 32px     (major block separation)
xl: 64px     (page sections)
2xl: 128px   (hero spacing)
```

Whitespace IS content. Never fill silently.

---

## Component Patterns: "Modular Architecture"

### Button Design
```
Default:    [Acropolis Gray text] on transparent, Parthenon Gold border
Hover:      [Parthenon Gold text] on Acropolis Gray bg, Owl Silver border
Active:     [Thunderbolt White text] on Aegean Deep bg
Disabled:   [Owl Silver text] on transparent, Owl Silver border (40% opacity)
```

### Card Design
```
Background:   Thunderbolt White
Border:       Parthenon Gold (1px top), Owl Silver (1px sides/bottom)
Shadow:       0 2px 4px rgba(0,0,0,0.1) (marble depth)
Padding:      lg (32px)
Radius:       0px (sharp angles, like Doric columns)
```

### Form Inputs
```
Background:   Thunderbolt White
Border:       Acropolis Gray (1px)
Focus:        Parthenon Gold (2px), Aegean Deep text
Label:        12px, Acropolis Gray, font-weight 600
```

---

## Motion & Interaction: "Purposeful Flow"

- **Easing**: `cubic-bezier(0.4, 0, 0.2, 1)` (deceleration, like precision landing)
- **Durations**: 200ms (UI), 400ms (page transitions), 600ms (complex animations)
- **No bloat**: Every animation serves comprehension or delight
- **Hover feedback**: 50ms underline expansion, color shift
- **Voice interaction**: 100ms pulse feedback, 300ms response delay

---

## Accessibility: "Inclusive Wisdom"

- **Color Contrast**: WCAG AAA compliant (Acropolis Gray #3A3A3A + Thunderbolt White = 12.6:1)
- **Type Size**: Minimum 16px body (mobile-ready)
- **Touch Targets**: Minimum 44×44px (recommendation; supports motor accessibility)
- **Semantic HTML**: `<button>` not `<div onclick>` (screen reader friendly)
- **ARIA Labels**: Every interactive element documented
- **Keyboard Navigation**: Full support (Tab, Enter, Escape, Arrow keys)
- **Reduced Motion**: `@media (prefers-reduced-motion: reduce)` respected

---

## Brand Voice: "Strategic & Warm"

- **Tone**: Wise but approachable, professional but conversational
- **Language**: Clear, purposeful. "Build with precision" not "Leverage synergies"
- **Metaphors**: Greek mythology, craftsmanship, games, strategy
- **No jargon bloat**: Prefer "decision" over "decision matrix"
- **Ownership**: "We're automating this for you" (Athena's gift)

---

## Use Cases: Design Patterns by Context

### For Game Developers (Armor Engine Users)
- Blueprint precision tools (gold highlights)
- Collision grid system (Greek key patterns)
- Asset management (modular card layouts)
- Collaborative workflows (Acropolis color for team zones)

### For Voice Interaction (Future Athena Model)
- Waveform visualization (Parthenon Gold lines on Aegean Deep)
- Confidence indicators (olive green success feedback)
- Listening state (torch flame animated pulse)
- Response queuing (strategic multi-step flows)

### For Code Builders
- Syntax highlighting (Acropolis Gray base, Torch Flame for keywords)
- Git diff visualization (green additions, Spartan red deletions)
- PR review (Parthenon Gold for approved, torch flame for requested)

---

## Reference Implementations

See:
- `slate/design_tokens.py` — Programmatic token definitions
- `plugins/slate-copilot/src/athena.css` — CSS custom properties
- `models/Modelfile.slate-athena` — Athena AI model branding
- `.athena_personalization.json` — User profile data

---

## Future: Voice-Controlled Athena

The design system anticipates voice interaction:
- **Audio representation**: Waveform visualizations in Parthenon Gold
- **Listening states**: Animated listening pulse (Torch Flame)
- **Response hierarchy**: Confidence indicators (Olive Green = high, Spartan Red = clarification needed)
- **Spatial layout**: Voice commands trigger spatial cues (Greek key animated borders)

---

## Design Review Checklist

Before merging any UI:
- [ ] Uses SLATE-ATHENA color palette (no unauthorized colors)
- [ ] Respects 24-column grid spacing
- [ ] Typography hierarchy follows rules (H1 > H2 > Body)
- [ ] Icons are minimal outline style, 45° where possible
- [ ] Component shadows/borders match marble aesthetic
- [ ] Whitespace is intentional (not "filling space")
- [ ] Motion has purpose (not decorative)
- [ ] WCAG AAA contrast verified
- [ ] Responsive breakpoints tested (desktop/tablet/mobile)
- [ ] Keyboard navigation works
- [ ] Voice interaction ready (aria-labels present)

---

**Godspeed, architect of wisdom. Build with precision.** ⚡

