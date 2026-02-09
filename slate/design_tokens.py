#!/usr/bin/env python3
# Modified: 2026-02-08T18:00:00Z | Author: COPILOT | Change: Initial SLATE design token system
"""
SLATE Design Tokens
===================

Comprehensive design token system synthesizing:
- Google M3 Material Design tokens
- Anthropic geometric art palette
- Awwwards modern dashboard patterns

These tokens are injected into the generative UI during installation
and are used by the dashboard server for consistent styling.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path
import json


@dataclass
class ColorTokens:
    """
    Color token definitions.

    Design Philosophy (2026 Premium Fintech - QT Capital Inspired):
    - Pure black foundations for maximum contrast and premium feel
    - Copper/bronze primary accent (Watchmaker heritage)
    - Electric blue secondary for tech/data visualization
    - Sophisticated glassmorphism with ambient lighting
    - High contrast text hierarchy on dark surfaces
    """

    # ═══════════════════════════════════════════════════════════════════════════
    # PRIMARY PALETTE — Copper/Bronze (Watchmaker Precision)
    # ═══════════════════════════════════════════════════════════════════════════
    primary: str = "#B87333"              # Copper — signature accent
    primary_light: str = "#D4956B"        # Light copper — hover states
    primary_dark: str = "#8B5E2B"         # Dark copper — pressed states
    primary_container: str = "rgba(184,115,51,0.12)"
    on_primary: str = "#000000"
    on_primary_container: str = "#F5DCC8"

    # ═══════════════════════════════════════════════════════════════════════════
    # SECONDARY PALETTE — Electric Blue (Tech/Data)
    # ═══════════════════════════════════════════════════════════════════════════
    secondary: str = "#3B82F6"            # Electric blue — data viz, links
    secondary_light: str = "#60A5FA"      # Light blue — hover
    secondary_dark: str = "#2563EB"       # Dark blue — active
    secondary_container: str = "rgba(59,130,246,0.12)"
    on_secondary: str = "#FFFFFF"
    on_secondary_container: str = "#DBEAFE"

    # ═══════════════════════════════════════════════════════════════════════════
    # TERTIARY PALETTE — Neon Violet (Premium Accent)
    # ═══════════════════════════════════════════════════════════════════════════
    tertiary: str = "#8B5CF6"             # Violet — premium highlights
    tertiary_light: str = "#A78BFA"       # Light violet
    tertiary_dark: str = "#7C3AED"        # Dark violet
    tertiary_container: str = "rgba(139,92,246,0.12)"
    on_tertiary: str = "#FFFFFF"
    on_tertiary_container: str = "#EDE9FE"

    # ═══════════════════════════════════════════════════════════════════════════
    # DARK MODE SURFACES — Pure Black Foundation (QT Capital Style)
    # ═══════════════════════════════════════════════════════════════════════════
    surface_dark: str = "#000000"         # Pure black — root background
    surface_dim_dark: str = "#030303"     # Near black — subtle depth
    surface_bright_dark: str = "#0A0A0A"  # Elevated black
    surface_container_lowest_dark: str = "#000000"
    surface_container_low_dark: str = "#0A0A0A"
    surface_container_dark: str = "#111111"
    surface_container_high_dark: str = "#1A1A1A"
    surface_container_highest_dark: str = "#222222"
    on_surface_dark: str = "#FAFAFA"      # Pure white text
    on_surface_variant_dark: str = "#A1A1AA"

    # ═══════════════════════════════════════════════════════════════════════════
    # LIGHT MODE SURFACES — Warm White (Contrast Mode)
    # ═══════════════════════════════════════════════════════════════════════════
    surface: str = "#FAFAF9"
    surface_dim: str = "#E7E5E4"
    surface_bright: str = "#FFFFFF"
    surface_container_lowest: str = "#FFFFFF"
    surface_container_low: str = "#F5F5F4"
    surface_container: str = "#E7E5E4"
    surface_container_high: str = "#D6D3D1"
    surface_container_highest: str = "#A8A29E"
    on_surface: str = "#0C0A09"
    on_surface_variant: str = "#44403C"

    # ═══════════════════════════════════════════════════════════════════════════
    # OUTLINE — Subtle Borders
    # ═══════════════════════════════════════════════════════════════════════════
    outline: str = "#78716C"
    outline_variant: str = "#D6D3D1"
    outline_dark: str = "#3F3F46"
    outline_variant_dark: str = "#27272A"

    # ═══════════════════════════════════════════════════════════════════════════
    # SEMANTIC COLORS — Premium Fintech Status
    # ═══════════════════════════════════════════════════════════════════════════
    success: str = "#22C55E"              # Vibrant green — active/success
    success_container: str = "rgba(34,197,94,0.12)"
    on_success: str = "#000000"
    on_success_container: str = "#DCFCE7"

    warning: str = "#F59E0B"              # Amber — pending/warning
    warning_container: str = "rgba(245,158,11,0.12)"
    on_warning: str = "#000000"
    on_warning_container: str = "#FEF3C7"

    error: str = "#EF4444"                # Red — error/critical
    error_container: str = "rgba(239,68,68,0.12)"
    on_error: str = "#FFFFFF"
    on_error_container: str = "#FEE2E2"

    info: str = "#06B6D4"                 # Cyan — informational
    info_container: str = "rgba(6,182,212,0.12)"
    on_info: str = "#000000"
    on_info_container: str = "#CFFAFE"

    # ═══════════════════════════════════════════════════════════════════════════
    # GLASSMORPHISM — 2026 Dark Glass Aesthetic
    # ═══════════════════════════════════════════════════════════════════════════
    glass_bg: str = "rgba(0,0,0,0.6)"     # Dark glass background
    glass_bg_elevated: str = "rgba(10,10,10,0.8)"
    glass_border: str = "rgba(255,255,255,0.06)"
    glass_border_hover: str = "rgba(255,255,255,0.12)"
    glass_shine: str = "linear-gradient(135deg, rgba(255,255,255,0.1) 0%, transparent 50%)"
    glass_blur: str = "24px"
    glass_saturate: str = "1.2"

    # ═══════════════════════════════════════════════════════════════════════════
    # AMBIENT GRADIENTS — Floating Light Orbs
    # ═══════════════════════════════════════════════════════════════════════════
    ambient_copper: str = "radial-gradient(ellipse 50% 50% at 50% 0%, rgba(184,115,51,0.15), transparent 70%)"
    ambient_blue: str = "radial-gradient(ellipse 40% 40% at 80% 80%, rgba(59,130,246,0.1), transparent 60%)"
    ambient_violet: str = "radial-gradient(ellipse 30% 30% at 20% 70%, rgba(139,92,246,0.08), transparent 50%)"

    # ═══════════════════════════════════════════════════════════════════════════
    # HOLOGRAPHIC — Premium Gradient Effects
    # ═══════════════════════════════════════════════════════════════════════════
    holo_gradient: str = "linear-gradient(135deg, #B87333, #3B82F6, #8B5CF6)"
    holo_text: str = "linear-gradient(90deg, #B87333 0%, #D4956B 25%, #3B82F6 50%, #8B5CF6 75%, #B87333 100%)"

    # ═══════════════════════════════════════════════════════════════════════════
    # ENGINEERING BLUEPRINT THEME
    # ═══════════════════════════════════════════════════════════════════════════
    blueprint_bg: str = "#000000"         # Pure black (updated)
    blueprint_grid: str = "#1A1A1A"       # Subtle grid
    blueprint_line: str = "#27272A"       # Connection lines
    blueprint_accent: str = "#B87333"     # Copper highlights
    blueprint_node: str = "#111111"       # Node backgrounds
    blueprint_text: str = "#FAFAFA"       # Text on blueprint

    blueprint_bg_light: str = "#FAFAF9"
    blueprint_grid_light: str = "#E7E5E4"
    blueprint_line_light: str = "#A8A29E"
    blueprint_accent_light: str = "#8B5E2B"
    blueprint_node_light: str = "#FFFFFF"
    blueprint_text_light: str = "#0C0A09"

    # ═══════════════════════════════════════════════════════════════════════════
    # CONNECTION STATUS — Live System States
    # ═══════════════════════════════════════════════════════════════════════════
    connection_active: str = "#22C55E"
    connection_pending: str = "#F59E0B"
    connection_error: str = "#EF4444"
    connection_inactive: str = "#52525B"

    # ═══════════════════════════════════════════════════════════════════════════
    # WIZARD/STEPPER — Installation Flow
    # ═══════════════════════════════════════════════════════════════════════════
    step_active: str = "#B87333"          # Copper — current step
    step_complete: str = "#22C55E"        # Green — completed
    step_pending: str = "#52525B"         # Gray — future
    step_error: str = "#EF4444"           # Red — error


@dataclass
class TypographyTokens:
    """Typography token definitions."""

    # Font families
    font_display: str = "'Styrene A', 'Inter Tight', system-ui, sans-serif"
    font_body: str = "'Tiempos Text', 'Georgia', serif"
    font_mono: str = "'Cascadia Code', 'JetBrains Mono', 'Consolas', monospace"

    # Font sizes (fluid with clamp)
    display_large: str = "clamp(2.5rem, 2rem + 2.5vw, 3.5625rem)"
    display_medium: str = "clamp(2rem, 1.5rem + 2vw, 2.8125rem)"
    display_small: str = "clamp(1.5rem, 1.25rem + 1.25vw, 2.25rem)"
    headline_large: str = "clamp(1.5rem, 1.25rem + 1vw, 2rem)"
    headline_medium: str = "clamp(1.25rem, 1rem + 0.75vw, 1.75rem)"
    headline_small: str = "clamp(1.125rem, 1rem + 0.5vw, 1.5rem)"
    title_large: str = "1.375rem"
    title_medium: str = "1rem"
    title_small: str = "0.875rem"
    body_large: str = "1rem"
    body_medium: str = "0.875rem"
    body_small: str = "0.75rem"
    label_large: str = "0.875rem"
    label_medium: str = "0.75rem"
    label_small: str = "0.6875rem"

    # Font weights
    weight_regular: int = 400
    weight_medium: int = 500
    weight_bold: int = 700

    # Line heights
    line_height_tight: float = 1.2
    line_height_normal: float = 1.5
    line_height_relaxed: float = 1.75


@dataclass
class SpacingTokens:
    """Spacing token definitions."""

    # Base unit: 4px
    space_0: str = "0"
    space_1: str = "0.25rem"   # 4px
    space_2: str = "0.5rem"    # 8px
    space_3: str = "0.75rem"   # 12px
    space_4: str = "1rem"      # 16px
    space_5: str = "1.25rem"   # 20px
    space_6: str = "1.5rem"    # 24px
    space_7: str = "1.75rem"   # 28px
    space_8: str = "2rem"      # 32px
    space_10: str = "2.5rem"   # 40px
    space_12: str = "3rem"     # 48px
    space_16: str = "4rem"     # 64px
    space_20: str = "5rem"     # 80px
    space_24: str = "6rem"     # 96px

    # Semantic spacing
    gutter: str = "clamp(1rem, 2vw, 1.5rem)"
    container_padding: str = "clamp(1rem, 4vw, 3rem)"


@dataclass
class ElevationTokens:
    """
    Elevation/shadow token definitions.

    2026 Glassmorphism Elevation:
    - Darker shadows for true black backgrounds
    - Subtle ambient glow from accent colors
    - Inner shine for glass depth effect
    """

    # ═══════════════════════════════════════════════════════════════════════════
    # STANDARD ELEVATION — Dark Theme Optimized
    # ═══════════════════════════════════════════════════════════════════════════
    elevation_0: str = "none"
    elevation_1: str = "0 1px 3px rgba(0,0,0,0.5), 0 1px 2px rgba(0,0,0,0.3)"
    elevation_2: str = "0 3px 6px rgba(0,0,0,0.5), 0 2px 4px rgba(0,0,0,0.3)"
    elevation_3: str = "0 6px 12px rgba(0,0,0,0.5), 0 4px 8px rgba(0,0,0,0.3)"
    elevation_4: str = "0 12px 24px rgba(0,0,0,0.5), 0 8px 16px rgba(0,0,0,0.3)"
    elevation_5: str = "0 24px 48px rgba(0,0,0,0.6), 0 12px 24px rgba(0,0,0,0.4)"

    # ═══════════════════════════════════════════════════════════════════════════
    # GLASS ELEVATION — With Ambient Glow
    # ═══════════════════════════════════════════════════════════════════════════
    glass_elevation_1: str = "0 4px 16px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.05)"
    glass_elevation_2: str = "0 8px 32px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.06)"
    glass_elevation_3: str = "0 16px 48px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.08)"

    # ═══════════════════════════════════════════════════════════════════════════
    # ACCENT GLOW — Copper Ambient Light
    # ═══════════════════════════════════════════════════════════════════════════
    glow_copper_sm: str = "0 0 20px rgba(184,115,51,0.15)"
    glow_copper_md: str = "0 0 40px rgba(184,115,51,0.2)"
    glow_copper_lg: str = "0 0 60px rgba(184,115,51,0.25)"

    # ═══════════════════════════════════════════════════════════════════════════
    # STATUS GLOW — Semantic Ambient
    # ═══════════════════════════════════════════════════════════════════════════
    glow_success: str = "0 0 30px rgba(34,197,94,0.3)"
    glow_warning: str = "0 0 30px rgba(245,158,11,0.3)"
    glow_error: str = "0 0 30px rgba(239,68,68,0.3)"
    glow_info: str = "0 0 30px rgba(6,182,212,0.3)"


@dataclass
class RadiusTokens:
    """Border radius token definitions."""

    radius_none: str = "0"
    radius_xs: str = "4px"
    radius_sm: str = "8px"
    radius_md: str = "12px"
    radius_lg: str = "16px"
    radius_xl: str = "24px"
    radius_2xl: str = "32px"
    radius_full: str = "9999px"


@dataclass
class MotionTokens:
    """
    Animation/motion token definitions.

    2026 Motion Design Principles:
    - Expo easing for premium feel
    - Spring physics for organic interactions
    - Staggered reveals for depth
    - Subtle parallax for immersion
    """

    # ═══════════════════════════════════════════════════════════════════════════
    # EASING CURVES — Premium 2026 Motion
    # ═══════════════════════════════════════════════════════════════════════════
    easing_standard: str = "cubic-bezier(0.4, 0, 0.2, 1)"      # M3 standard
    easing_decelerate: str = "cubic-bezier(0, 0, 0.2, 1)"      # Enter
    easing_accelerate: str = "cubic-bezier(0.4, 0, 1, 1)"      # Exit
    easing_spring: str = "cubic-bezier(0.34, 1.56, 0.64, 1)"   # Bounce
    easing_expo_out: str = "cubic-bezier(0.16, 1, 0.3, 1)"     # Premium expo
    easing_expo_in_out: str = "cubic-bezier(0.87, 0, 0.13, 1)" # Dramatic
    easing_back_out: str = "cubic-bezier(0.34, 1.4, 0.64, 1)"  # Overshoot
    easing_smooth: str = "cubic-bezier(0.25, 0.1, 0.25, 1)"    # Smooth linear

    # ═══════════════════════════════════════════════════════════════════════════
    # DURATIONS — Hierarchical Timing
    # ═══════════════════════════════════════════════════════════════════════════
    duration_instant: str = "50ms"
    duration_fast: str = "150ms"
    duration_normal: str = "300ms"
    duration_slow: str = "500ms"
    duration_slower: str = "700ms"
    duration_slowest: str = "1000ms"

    # ═══════════════════════════════════════════════════════════════════════════
    # STAGGER — Sequential Reveals
    # ═══════════════════════════════════════════════════════════════════════════
    stagger_fast: str = "30ms"
    stagger_normal: str = "50ms"
    stagger_slow: str = "80ms"

    # ═══════════════════════════════════════════════════════════════════════════
    # AMBIENT MOTION — Background Animations
    # ═══════════════════════════════════════════════════════════════════════════
    ambient_float: str = "20s"           # Floating orbs
    ambient_rotate: str = "60s"          # Slow rotation
    ambient_pulse: str = "3s"            # Glow pulse
    ambient_flow: str = "2s"             # Data flow lines


@dataclass
class StateTokens:
    """State layer token definitions (M3)."""

    state_hover: float = 0.08
    state_focus: float = 0.12
    state_pressed: float = 0.12
    state_dragged: float = 0.16
    state_disabled: float = 0.38


@dataclass
class EngineeringDrawingTokens:
    """
    Engineering Drawing Standards (Spec 013)

    Based on:
    - ISO 128 (Technical Drawing Line Types)
    - IEC 60617 (Electronic Schematic Symbols)
    - ASME Y14.44 (Reference Designators)
    - PCB Silkscreen Conventions
    """

    # ═══════════════════════════════════════════════════════════════════════════
    # ISO 128 Line Types (stroke-dasharray patterns)
    # ═══════════════════════════════════════════════════════════════════════════

    # Type 01: Continuous thick - visible outlines, active connections
    line_continuous_thick: str = "none"
    line_continuous_thick_width: str = "2px"

    # Type 02: Continuous thin - dimension lines, leaders
    line_continuous_thin: str = "none"
    line_continuous_thin_width: str = "1px"

    # Type 03: Dashed thick - hidden components, inactive services
    line_dashed_thick: str = "8,4"
    line_dashed_thick_width: str = "2px"

    # Type 04: Dashed thin - hidden details, pending tasks
    line_dashed_thin: str = "6,3"
    line_dashed_thin_width: str = "1px"

    # Type 05: Chain thin - center lines, symmetry axes
    line_chain_thin: str = "12,3,3,3"
    line_chain_thin_width: str = "1px"

    # Type 06: Chain thick - cut planes, section indicators
    line_chain_thick: str = "16,4,4,4"
    line_chain_thick_width: str = "2px"

    # Type 07: Dotted thin - projection lines, data flow
    line_dotted_thin: str = "2,2"
    line_dotted_thin_width: str = "1px"

    # Type 08: Long-dash double-short - boundaries, system limits
    line_boundary: str = "18,3,3,3,3,3"
    line_boundary_width: str = "1px"

    # ═══════════════════════════════════════════════════════════════════════════
    # Blueprint Colors (Engineering Drawing Palette)
    # ═══════════════════════════════════════════════════════════════════════════

    # Background variants
    blueprint_primary: str = "#0D1B2A"      # Deep blueprint blue
    blueprint_secondary: str = "#0a0a0a"    # SLATE dark
    blueprint_tertiary: str = "#1B2838"     # Lighter blueprint

    # Trace colors by type
    trace_signal: str = "#B87333"           # Copper - primary signals
    trace_power: str = "#C47070"            # Warm red - power lines
    trace_ground: str = "#78716C"           # Cool gray - ground
    trace_data: str = "#7EA8BE"             # Soft blue - data lines
    trace_control: str = "#D4A054"          # Gold - control signals

    # Status indicators
    status_active: str = "#22C55E"          # Green - live/active
    status_pending: str = "#D4A054"         # Gold - waiting
    status_error: str = "#C47070"           # Red - fault
    status_disabled: str = "#333333"        # Dim gray - disabled
    status_unknown: str = "#4B5563"         # Neutral gray - unknown

    # Component fills
    fill_service: str = "#1a1510"           # Dark warm - services
    fill_database: str = "#101520"          # Dark cool - databases
    fill_gpu: str = "#15120a"               # Dark copper - GPU/compute
    fill_ai: str = "#0a1515"                # Dark teal - AI/ML
    fill_external: str = "#151015"          # Dark purple - external

    # ═══════════════════════════════════════════════════════════════════════════
    # PCB Silkscreen Typography
    # ═══════════════════════════════════════════════════════════════════════════

    # Font sizes (following silkscreen conventions)
    text_component_label: str = "14px"      # Component labels
    text_reference_designator: str = "12px" # Reference designators (R1, C2)
    text_pin_number: str = "10px"           # Pin numbers
    text_status_indicator: str = "8px"      # Status text
    text_section_header: str = "16px"       # Section headers

    # Font families (engineering-style)
    font_schematic: str = "Consolas, 'Courier New', monospace"
    font_schematic_bold: str = "Consolas, 'Courier New', monospace"
    font_labels: str = "'Segoe UI', system-ui, sans-serif"

    # Text colors
    text_primary: str = "#E7E0D8"           # Cream - primary text
    text_secondary: str = "#A8A29E"         # Warm gray - secondary
    text_designator: str = "#C9956B"        # Copper - designators
    text_muted: str = "#78716C"             # Muted - tertiary text

    # ═══════════════════════════════════════════════════════════════════════════
    # Engineering Grid System (8px base unit)
    # ═══════════════════════════════════════════════════════════════════════════

    grid_base: str = "8px"                  # Base unit (ISO module)
    grid_minor: str = "16px"                # Minor grid (2 × base)
    grid_major: str = "64px"                # Major grid (8 × base)

    # Component sizes (multiples of major grid)
    component_small: str = "64px"           # 1×1 major (status)
    component_medium_w: str = "128px"       # 2×1 major width (services)
    component_medium_h: str = "64px"        # 2×1 major height
    component_large: str = "128px"          # 2×2 major (databases)
    component_xlarge_w: str = "256px"       # 4×2 major width (groups)
    component_xlarge_h: str = "128px"       # 4×2 major height

    # Spacing
    spacing_component: str = "32px"         # Between components (4 × base)
    spacing_group: str = "64px"             # Between groups (8 × base)
    spacing_margin: str = "48px"            # Edge margin (6 × base)

    # ═══════════════════════════════════════════════════════════════════════════
    # ASME Y14.44 Reference Designator Prefixes
    # ═══════════════════════════════════════════════════════════════════════════

    designator_service: str = "SVC"         # Core services
    designator_database: str = "DB"         # Databases
    designator_gpu: str = "GPU"             # GPU units
    designator_ai: str = "AI"               # AI models
    designator_api: str = "API"             # API routes
    designator_connector: str = "J"         # Connectors
    designator_bus: str = "BUS"             # Data buses
    designator_terminal: str = "T"          # Terminals

    # ═══════════════════════════════════════════════════════════════════════════
    # Animation Standards
    # ═══════════════════════════════════════════════════════════════════════════

    anim_pulse_duration: str = "2s"         # Active pulse
    anim_flow_duration: str = "1s"          # Data flow
    anim_connect_duration: str = "0.5s"     # Connection establish
    anim_appear_duration: str = "0.3s"      # Component appear
    anim_transition_duration: str = "0.3s"  # Status change
    anim_error_duration: str = "0.2s"       # Error flash

    anim_easing_pulse: str = "ease-in-out"
    anim_easing_flow: str = "linear"
    anim_easing_appear: str = "ease-out"
    anim_easing_transition: str = "ease-in-out"

    # ═══════════════════════════════════════════════════════════════════════════
    # Polarity & Orientation Markers
    # ═══════════════════════════════════════════════════════════════════════════

    marker_pin1: str = "●"                  # Pin 1 indicator (filled circle)
    marker_active: str = "+"                # Active/power marker
    marker_ground: str = "−"                # Ground/inactive marker
    marker_empty: str = "○"                 # Empty/unconnected
    marker_bidirectional: str = "↔"         # Bidirectional flow
    marker_input: str = "→"                 # Input direction
    marker_output: str = "←"                # Output direction


@dataclass
class DesignTokens:
    """Complete design token collection."""

    colors: ColorTokens = field(default_factory=ColorTokens)
    typography: TypographyTokens = field(default_factory=TypographyTokens)
    spacing: SpacingTokens = field(default_factory=SpacingTokens)
    elevation: ElevationTokens = field(default_factory=ElevationTokens)
    radius: RadiusTokens = field(default_factory=RadiusTokens)
    motion: MotionTokens = field(default_factory=MotionTokens)
    state: StateTokens = field(default_factory=StateTokens)
    engineering: EngineeringDrawingTokens = field(default_factory=EngineeringDrawingTokens)

    def to_css_variables(self, prefix: str = "slate") -> str:
        """Generate CSS custom properties from all tokens."""
        lines = [":root {"]

        # Colors
        for name, value in vars(self.colors).items():
            css_name = name.replace("_", "-")
            lines.append(f"    --{prefix}-{css_name}: {value};")

        lines.append("")

        # Typography
        for name, value in vars(self.typography).items():
            if isinstance(value, (int, float)):
                lines.append(f"    --{prefix}-{name.replace('_', '-')}: {value};")
            else:
                lines.append(f"    --{prefix}-{name.replace('_', '-')}: {value};")

        lines.append("")

        # Spacing
        for name, value in vars(self.spacing).items():
            lines.append(f"    --{prefix}-{name.replace('_', '-')}: {value};")

        lines.append("")

        # Elevation
        for name, value in vars(self.elevation).items():
            lines.append(f"    --{prefix}-{name.replace('_', '-')}: {value};")

        lines.append("")

        # Radius
        for name, value in vars(self.radius).items():
            lines.append(f"    --{prefix}-{name.replace('_', '-')}: {value};")

        lines.append("")

        # Motion
        for name, value in vars(self.motion).items():
            lines.append(f"    --{prefix}-{name.replace('_', '-')}: {value};")

        lines.append("")

        # State
        for name, value in vars(self.state).items():
            lines.append(f"    --{prefix}-{name.replace('_', '-')}: {value};")

        lines.append("")

        # Engineering Drawing (Spec 013)
        lines.append("    /* Engineering Drawing Standards (ISO 128, IEC 60617, ASME Y14.44) */")
        for name, value in vars(self.engineering).items():
            css_name = name.replace("_", "-")
            lines.append(f"    --{prefix}-eng-{css_name}: {value};")

        lines.append("}")

        return "\n".join(lines)

    def to_json(self) -> str:
        """Export tokens as JSON for programmatic use."""
        data = {
            "colors": vars(self.colors),
            "typography": vars(self.typography),
            "spacing": vars(self.spacing),
            "elevation": vars(self.elevation),
            "radius": vars(self.radius),
            "motion": vars(self.motion),
            "state": vars(self.state),
            "engineering": vars(self.engineering)
        }
        return json.dumps(data, indent=2)

    def save_css(self, path: Path) -> None:
        """Save tokens as CSS file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_css_variables(), encoding='utf-8')

    def save_json(self, path: Path) -> None:
        """Save tokens as JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json(), encoding='utf-8')


# Global default tokens instance
DEFAULT_TOKENS = DesignTokens()


def get_tokens() -> DesignTokens:
    """Get the default design tokens."""
    return DEFAULT_TOKENS


def generate_theme_css(theme_value: float = 0.0) -> str:
    """
    Generate CSS for a specific theme value.

    Args:
        theme_value: 0.0 = full dark, 1.0 = full light

    Returns:
        CSS string with interpolated values
    """
    tokens = DEFAULT_TOKENS

    # Interpolate between dark and light values
    def lerp_color(dark: str, light: str, t: float) -> str:
        """Linear interpolate between two hex colors."""
        dark = dark.lstrip('#')
        light = light.lstrip('#')

        r1, g1, b1 = int(dark[0:2], 16), int(dark[2:4], 16), int(dark[4:6], 16)
        r2, g2, b2 = int(light[0:2], 16), int(light[2:4], 16), int(light[4:6], 16)

        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)

        return f"#{r:02x}{g:02x}{b:02x}"

    # Generate interpolated colors
    surface = lerp_color(
        tokens.colors.surface_dark,
        tokens.colors.surface,
        theme_value
    )
    on_surface = lerp_color(
        tokens.colors.on_surface_dark,
        tokens.colors.on_surface,
        theme_value
    )

    css = f"""
:root {{
    --slate-theme-value: {theme_value};
    --slate-surface-computed: {surface};
    --slate-on-surface-computed: {on_surface};
}}
"""
    return css


if __name__ == "__main__":
    # Demo: generate token files
    tokens = DesignTokens()

    output_dir = Path(__file__).parent.parent / ".slate_identity"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save CSS
    tokens.save_css(output_dir / "design-tokens.css")
    print(f"Generated: {output_dir / 'design-tokens.css'}")

    # Save JSON
    tokens.save_json(output_dir / "design-tokens.json")
    print(f"Generated: {output_dir / 'design-tokens.json'}")

    print("\nDesign token generation complete!")
