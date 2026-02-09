#!/usr/bin/env python3
# Modified: 2026-02-07T10:00:00Z | Author: COPILOT | Change: SLATE generative UI design system
# Purpose: M3 Material + Awwwards-inspired design token generator for SLATE dashboards
"""
SLATE Generative UI Design System
==================================
Procedural design token generator combining:
- Google Material Design 3 (M3) color system & elevation tokens
- Awwwards-trend analysis: editorial grids, kinetic typography, geometric art
- Anthropic geometric patterns: crystalline forms, tessellations, depth fields
- SLATE brand identity: agentic AI, dual-GPU, orchestration metaphors

Generates CSS custom properties, SVG patterns, and theme configurations
that can be injected into the dashboard HTML at build time.
"""

import colorsys
import hashlib
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

WORKSPACE_ROOT = Path(__file__).parent.parent


# ═══════════════════════════════════════════════════════════════════════════════
# M3 TONAL PALETTE GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════

class M3TonalPalette:
    """
    Generates Material Design 3 tonal palettes from a seed color.
    Based on HCT (Hue, Chroma, Tone) color space approximation.
    Reference: https://m3.material.io/styles/color/system/overview
    """

    TONES = [0, 4, 6, 10, 12, 17, 20, 22, 24, 25, 30, 35, 40, 50, 60, 70, 80, 87, 90, 92, 94, 95, 96, 98, 99, 100]

    @staticmethod
    def hex_to_hsl(hex_color: str) -> Tuple[float, float, float]:
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16) / 255, int(hex_color[2:4], 16) / 255, int(hex_color[4:6], 16) / 255
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        return h * 360, s, l

    @staticmethod
    def hsl_to_hex(h: float, s: float, l: float) -> str:
        r, g, b = colorsys.hls_to_rgb(h / 360, l, s)
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

    @classmethod
    def generate(cls, seed_hex: str) -> Dict[int, str]:
        """Generate tonal palette from seed color."""
        h, s, _ = cls.hex_to_hsl(seed_hex)
        palette = {}
        for tone in cls.TONES:
            lightness = tone / 100
            # M3: reduce chroma at extremes, preserve hue
            chroma = s * (1 - abs(2 * lightness - 1) * 0.3)
            chroma = max(0, min(1, chroma))
            palette[tone] = cls.hsl_to_hex(h, chroma, lightness)
        return palette


# ═══════════════════════════════════════════════════════════════════════════════
# SLATE DESIGN TOKENS
# ═══════════════════════════════════════════════════════════════════════════════

class SlateDesignTokens:
    """
    Core SLATE design token system.

    Design philosophy (Awwwards 2025-2026 + ASUS ProArt Design Language):
    - Editorial minimalism with bold typography
    - Geometric depth through layered surfaces
    - Kinetic micro-interactions
    - Data-dense but spatially breathable layouts
    - Dark-first: true black with copper/white accents
    - Anthropic crystalline geometry for backgrounds

    Color strategy (ASUS ProArt + Anthropic inspired):
    - Primary: True black (#0a0a0a) → professional-grade substrate
    - Accent: Copper/bronze (#B87333) → ProArt precision engineering aesthetic
    - Secondary: Warm white (#F5F0EB) → clean readability on dark surfaces
    - Neutral: Cool charcoal grays → infrastructure depth
    - Semantic: Muted professional traffic-light system
    """

    # Modified: 2026-02-07T12:00:00Z | Author: COPILOT | Change: ASUS ProArt black/white/copper palette
    # SLATE Brand Colors — ASUS ProArt inspired (black + white + copper)
    BRAND = {
        "primary": "#0a0a0a",       # True black — professional substrate
        "accent": "#B87333",        # Copper — ProArt precision engineering
        "accent_light": "#C9956B", # Light copper — hover/highlight states
        "surface": "#111111",       # Near-black — card/container surfaces
        "neutral": "#1a1a1a",       # Charcoal — subtle elevation
        "white": "#F5F0EB",         # Warm white — primary text
        "white_dim": "#A8A29E",    # Muted warm gray — secondary text
    }

    # Modified: 2026-02-08T02:35:00Z | Author: COPILOT | Change: add SLATE-ATHENA palette
    ATHENA = {
        "gold": "#D4AF37",         # Parthenon Gold
        "gold_light": "#E2C25A",   # Highlight gold
        "gold_dim": "#B08A2E",     # Aged gold
        "aegean": "#1A3A52",       # Aegean Deep
        "acropolis": "#3A3A3A",    # Acropolis Gray
        "owl": "#B0B0B0",          # Owl Silver
        "torch": "#FF6B1A",        # Torch Flame
        "olive": "#4A6741",        # Olive Green
        "thunderbolt": "#F8F8F8",  # Thunderbolt White
        "shadow": "#0D0D0D",       # Shadow Black
        "bronze": "#6B4423",       # Wisdom Bronze
    }

    # Semantic Colors (muted, professional)
    SEMANTIC = {
        "success": "#78B89A",       # Muted sage green
        "warning": "#D4A054",       # Warm amber
        "error": "#C47070",         # Muted rose
        "info": "#7EA8BE",          # Steel blue
    }

    @classmethod
    def generate_tokens(cls, theme: str = "dark") -> Dict[str, str]:
        """Generate CSS custom property values for the given theme."""
        primary_palette = M3TonalPalette.generate(cls.BRAND["primary"])
        accent_palette = M3TonalPalette.generate(cls.BRAND["accent"])
        neutral_palette = M3TonalPalette.generate(cls.BRAND["neutral"])

        if theme == "dark":
            tokens = {
                # Surfaces — true black foundation (ProArt inspired)
                "--sl-bg-root": "#050505",
                "--sl-bg-surface": "#0a0a0a",
                "--sl-bg-surface-dim": "#030303",
                "--sl-bg-surface-bright": "#161616",
                "--sl-bg-container": "#111111",
                "--sl-bg-container-high": "#1a1a1a",
                "--sl-bg-container-highest": "#222222",
                "--sl-bg-inverse": "#F5F0EB",

                # Elevation overlays — subtle copper-tinted shadows
                "--sl-elevation-1": "0 1px 3px rgba(0,0,0,0.6), 0 1px 2px rgba(0,0,0,0.4), inset 0 1px 0 rgba(184,115,51,0.04)",
                "--sl-elevation-2": "0 2px 6px rgba(0,0,0,0.5), 0 1px 3px rgba(0,0,0,0.4), inset 0 1px 0 rgba(184,115,51,0.06)",
                "--sl-elevation-3": "0 4px 12px rgba(0,0,0,0.6), 0 2px 4px rgba(0,0,0,0.4)",
                "--sl-elevation-4": "0 8px 24px rgba(0,0,0,0.6), 0 4px 8px rgba(0,0,0,0.4)",
                "--sl-elevation-5": "0 12px 32px rgba(0,0,0,0.7), 0 4px 12px rgba(0,0,0,0.5)",

                # Text — warm white hierarchy
                "--sl-text-primary": "#F5F0EB",
                "--sl-text-secondary": "#A8A29E",
                "--sl-text-tertiary": "#78716C",
                "--sl-text-disabled": "#44403C",
                "--sl-text-on-primary": "#0a0a0a",
                "--sl-text-on-accent": "#0a0a0a",

                # Accent — copper/bronze (ProArt)
                "--sl-accent": "#B87333",
                "--sl-accent-dim": "#8B5E2B",
                "--sl-accent-light": "#C9956B",
                "--sl-accent-container": "rgba(184,115,51,0.12)",
                "--sl-accent-on-container": "#D4A97A",
                "--sl-accent-glow": "rgba(184,115,51,0.15)",

                # Borders — subtle, monochrome
                "--sl-border": "rgba(255,255,255,0.08)",
                "--sl-border-variant": "rgba(255,255,255,0.12)",
                "--sl-border-focus": "#B87333",
                "--sl-outline": "rgba(255,255,255,0.06)",

                # Semantic status (muted professional)
                "--sl-success": cls.SEMANTIC["success"],
                "--sl-warning": cls.SEMANTIC["warning"],
                "--sl-error": cls.SEMANTIC["error"],
                "--sl-info": cls.SEMANTIC["info"],
                "--sl-success-container": f"{cls.SEMANTIC['success']}15",
                "--sl-warning-container": f"{cls.SEMANTIC['warning']}15",
                "--sl-error-container": f"{cls.SEMANTIC['error']}15",
                "--sl-info-container": f"{cls.SEMANTIC['info']}15",

                # Glass effects — dark, copper-tinged
                "--sl-glass-bg": "rgba(10, 10, 10, 0.78)",
                "--sl-glass-border": "rgba(184,115,51,0.08)",
                "--sl-glass-blur": "20px",
                "--sl-glass-saturate": "1.1",

                # Typography
                "--sl-font-sans": "'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif",
                "--sl-font-mono": "'JetBrains Mono', 'Cascadia Code', 'Fira Code', monospace",
                "--sl-font-display": "'Inter', 'Segoe UI', system-ui, sans-serif",

                # Spacing (8px grid)
                "--sl-space-1": "4px",
                "--sl-space-2": "8px",
                "--sl-space-3": "12px",
                "--sl-space-4": "16px",
                "--sl-space-5": "20px",
                "--sl-space-6": "24px",
                "--sl-space-8": "32px",
                "--sl-space-10": "40px",
                "--sl-space-12": "48px",
                "--sl-space-16": "64px",

                # Radii (M3 shape)
                "--sl-radius-xs": "4px",
                "--sl-radius-sm": "8px",
                "--sl-radius-md": "12px",
                "--sl-radius-lg": "16px",
                "--sl-radius-xl": "28px",
                "--sl-radius-full": "9999px",

                # Motion (M3 easing)
                "--sl-ease-standard": "cubic-bezier(0.2, 0, 0, 1)",
                "--sl-ease-decelerate": "cubic-bezier(0, 0, 0, 1)",
                "--sl-ease-accelerate": "cubic-bezier(0.3, 0, 1, 1)",
                "--sl-ease-emphasized": "cubic-bezier(0.2, 0, 0, 1)",
                "--sl-duration-short": "150ms",
                "--sl-duration-medium": "300ms",
                "--sl-duration-long": "500ms",
            }
            tokens.update({
                "--sl-bg-hover": "#141414",
                "--sl-bg-inset": "#0c0c0c",
                "--sl-border-subtle": "rgba(255,255,255,0.06)",
                "--sl-copper": tokens["--sl-accent"],
                "--sl-copper-light": tokens["--sl-accent-light"],
                "--sl-copper-dark": tokens["--sl-accent-dim"],
            })
            return tokens
        elif theme == "light":
            # Light theme variant (warm white + copper)
            tokens = {
                "--sl-bg-root": "#FAF8F5",
                "--sl-bg-surface": "#F5F0EB",
                "--sl-bg-surface-dim": "#EDE8E3",
                "--sl-bg-surface-bright": "#FFFFFF",
                "--sl-bg-container": "#F0ECE7",
                "--sl-bg-container-high": "#F5F2EE",
                "--sl-bg-container-highest": "#FFFFFF",
                "--sl-bg-inverse": "#1a1a1a",

                "--sl-text-primary": "#1C1917",
                "--sl-text-secondary": "#44403C",
                "--sl-text-tertiary": "#78716C",
                "--sl-text-disabled": "#A8A29E",
                "--sl-text-on-primary": "#FAF8F5",
                "--sl-text-on-accent": "#FFFFFF",

                "--sl-accent": "#8B5E2B",
                "--sl-accent-dim": "#B87333",
                "--sl-accent-light": "#C9956B",
                "--sl-accent-container": "rgba(184,115,51,0.10)",
                "--sl-accent-on-container": "#6B4226",
                "--sl-accent-glow": "rgba(184,115,51,0.10)",

                "--sl-border": "rgba(0,0,0,0.08)",
                "--sl-border-variant": "rgba(0,0,0,0.05)",
                "--sl-border-focus": "#8B5E2B",
                "--sl-outline": "rgba(0,0,0,0.06)",

                "--sl-success": "#527A65",
                "--sl-warning": "#A67C3D",
                "--sl-error": "#9E5555",
                "--sl-info": "#5A8599",

                "--sl-glass-bg": "rgba(255, 255, 255, 0.80)",
                "--sl-glass-border": "rgba(184,115,51,0.10)",
                "--sl-glass-blur": "20px",
                "--sl-glass-saturate": "1.1",

                "--sl-font-sans": "'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif",
                "--sl-font-mono": "'JetBrains Mono', 'Cascadia Code', 'Fira Code', monospace",
                "--sl-font-display": "'Inter', 'Segoe UI', system-ui, sans-serif",

                "--sl-space-1": "4px", "--sl-space-2": "8px", "--sl-space-3": "12px",
                "--sl-space-4": "16px", "--sl-space-5": "20px", "--sl-space-6": "24px",
                "--sl-space-8": "32px", "--sl-space-10": "40px", "--sl-space-12": "48px",
                "--sl-space-16": "64px",

                "--sl-radius-xs": "4px", "--sl-radius-sm": "8px", "--sl-radius-md": "12px",
                "--sl-radius-lg": "16px", "--sl-radius-xl": "28px", "--sl-radius-full": "9999px",

                "--sl-ease-standard": "cubic-bezier(0.2, 0, 0, 1)",
                "--sl-ease-decelerate": "cubic-bezier(0, 0, 0, 1)",
                "--sl-ease-accelerate": "cubic-bezier(0.3, 0, 1, 1)",
                "--sl-ease-emphasized": "cubic-bezier(0.2, 0, 0, 1)",
                "--sl-duration-short": "150ms",
                "--sl-duration-medium": "300ms",
                "--sl-duration-long": "500ms",
            }
            tokens.update({
                "--sl-bg-hover": "#E6E1DC",
                "--sl-bg-inset": "#EDE8E3",
                "--sl-border-subtle": "rgba(0,0,0,0.08)",
                "--sl-copper": tokens["--sl-accent"],
                "--sl-copper-light": tokens["--sl-accent-light"],
                "--sl-copper-dark": tokens["--sl-accent-dim"],
            })
            return tokens
        elif theme == "athena":
            tokens = {
                # Surfaces — Athena dark marble + Aegean depth
                "--sl-bg-root": cls.ATHENA["shadow"],
                "--sl-bg-surface": "#11161C",
                "--sl-bg-surface-dim": "#0B0F14",
                "--sl-bg-surface-bright": cls.ATHENA["aegean"],
                "--sl-bg-container": "#16212C",
                "--sl-bg-container-high": "#1E2B38",
                "--sl-bg-container-highest": "#263646",
                "--sl-bg-inverse": cls.ATHENA["thunderbolt"],

                # Elevation overlays
                "--sl-elevation-1": "0 1px 3px rgba(0,0,0,0.6), 0 1px 2px rgba(0,0,0,0.4), inset 0 1px 0 rgba(212,175,55,0.06)",
                "--sl-elevation-2": "0 2px 6px rgba(0,0,0,0.5), 0 1px 3px rgba(0,0,0,0.4), inset 0 1px 0 rgba(212,175,55,0.08)",
                "--sl-elevation-3": "0 4px 12px rgba(0,0,0,0.6), 0 2px 4px rgba(0,0,0,0.4)",
                "--sl-elevation-4": "0 8px 24px rgba(0,0,0,0.6), 0 4px 8px rgba(0,0,0,0.4)",
                "--sl-elevation-5": "0 12px 32px rgba(0,0,0,0.7), 0 4px 12px rgba(0,0,0,0.5)",

                # Text — marble hierarchy
                "--sl-text-primary": cls.ATHENA["thunderbolt"],
                "--sl-text-secondary": cls.ATHENA["owl"],
                "--sl-text-tertiary": "#8B8B8B",
                "--sl-text-disabled": "#5F5F5F",
                "--sl-text-on-primary": cls.ATHENA["shadow"],
                "--sl-text-on-accent": cls.ATHENA["shadow"],

                # Accent — Parthenon gold
                "--sl-accent": cls.ATHENA["gold"],
                "--sl-accent-dim": cls.ATHENA["gold_dim"],
                "--sl-accent-light": cls.ATHENA["gold_light"],
                "--sl-accent-container": "rgba(212,175,55,0.12)",
                "--sl-accent-on-container": "#F1D98C",
                "--sl-accent-glow": "rgba(212,175,55,0.20)",

                # Borders
                "--sl-border": "rgba(248,248,248,0.10)",
                "--sl-border-variant": "rgba(212,175,55,0.35)",
                "--sl-border-focus": cls.ATHENA["gold"],
                "--sl-outline": "rgba(248,248,248,0.06)",

                # Semantic status
                "--sl-success": "#2D5F2E",
                "--sl-warning": cls.ATHENA["torch"],
                "--sl-error": "#8B0000",
                "--sl-info": cls.ATHENA["aegean"],
                "--sl-success-container": "rgba(45,95,46,0.15)",
                "--sl-warning-container": "rgba(255,107,26,0.15)",
                "--sl-error-container": "rgba(139,0,0,0.15)",
                "--sl-info-container": "rgba(26,58,82,0.15)",

                # Glass effects
                "--sl-glass-bg": "rgba(13, 13, 13, 0.78)",
                "--sl-glass-border": "rgba(212,175,55,0.12)",
                "--sl-glass-blur": "18px",
                "--sl-glass-saturate": "1.1",

                # Typography
                "--sl-font-sans": "'Optima', 'Segoe UI', 'Trebuchet MS', sans-serif",
                "--sl-font-mono": "'Monaco', 'Courier New', monospace",
                "--sl-font-display": "Georgia, 'Times New Roman', serif",

                # Spacing (8px grid)
                "--sl-space-1": "4px",
                "--sl-space-2": "8px",
                "--sl-space-3": "12px",
                "--sl-space-4": "16px",
                "--sl-space-5": "20px",
                "--sl-space-6": "24px",
                "--sl-space-8": "32px",
                "--sl-space-10": "40px",
                "--sl-space-12": "48px",
                "--sl-space-16": "64px",

                # Radii (Athena: sharper, Doric)
                "--sl-radius-xs": "2px",
                "--sl-radius-sm": "4px",
                "--sl-radius-md": "8px",
                "--sl-radius-lg": "10px",
                "--sl-radius-xl": "16px",
                "--sl-radius-full": "9999px",

                # Motion
                "--sl-ease-standard": "cubic-bezier(0.4, 0, 0.2, 1)",
                "--sl-ease-decelerate": "cubic-bezier(0, 0, 0.2, 1)",
                "--sl-ease-accelerate": "cubic-bezier(0.4, 0, 1, 1)",
                "--sl-ease-emphasized": "cubic-bezier(0.4, 0, 0.2, 1)",
                "--sl-duration-short": "200ms",
                "--sl-duration-medium": "400ms",
                "--sl-duration-long": "600ms",
            }
            tokens.update({
                "--sl-bg-hover": "#223247",
                "--sl-bg-inset": "#0F141B",
                "--sl-border-subtle": "rgba(248,248,248,0.06)",
                "--sl-copper": tokens["--sl-accent"],
                "--sl-copper-light": tokens["--sl-accent-light"],
                "--sl-copper-dark": tokens["--sl-accent-dim"],
            })
            return tokens

        return cls.generate_tokens("dark")

    @classmethod
    def to_css(cls, theme: str = "dark") -> str:
        """Generate CSS :root block with all tokens."""
        tokens = cls.generate_tokens(theme)
        lines = [":root {"]
        for key, value in tokens.items():
            lines.append(f"    {key}: {value};")
        lines.append("}")
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# GEOMETRIC PATTERN GENERATOR
# (Inspired by Anthropic's crystalline/geometric visual language)
# ═══════════════════════════════════════════════════════════════════════════════

class GeometricPatternGenerator:
    """
    Generates SVG geometric patterns for dashboard backgrounds.

    Inspired by:
    - Anthropic's tessellated neural-crystal motifs
    - Awwwards 2025: mesh gradients, voronoi cells, parametric grids
    - SLATE identity: interconnected nodes (agents, GPUs, workflows)
    """

    # Modified: 2026-02-08T02:38:00Z | Author: COPILOT | Change: allow theme accent colors in patterns
    @staticmethod
    def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        hex_color = hex_color.lstrip("#")
        return int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)

    @staticmethod
    def constellation_grid(width: int = 1200, height: int = 800,
                           nodes: int = 40, seed: int = 42,
                           accent_hex: str = "#B87333") -> str:
        """Generate a constellation/network pattern — interconnected nodes."""
        import random
        rng = random.Random(seed)
        accent_r, accent_g, accent_b = GeometricPatternGenerator._hex_to_rgb(accent_hex)
        points = [(rng.randint(20, width-20), rng.randint(20, height-20)) for _ in range(nodes)]

        lines_svg = []
        dots_svg = []

        # Connect nearby points (Delaunay-like)
        for i, (x1, y1) in enumerate(points):
            for j, (x2, y2) in enumerate(points):
                if i >= j:
                    continue
                dist = math.sqrt((x2-x1)**2 + (y2-y1)**2)
                if dist < 200:
                    opacity = max(0.02, 0.08 * (1 - dist/200))
                    lines_svg.append(
                        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                        f'stroke="rgba({accent_r},{accent_g},{accent_b},{opacity:.3f})" stroke-width="0.4"/>'
                    )

        for x, y in points:
            r = rng.uniform(1, 2.5)
            opacity = rng.uniform(0.06, 0.25)
            dots_svg.append(
                f'<circle cx="{x}" cy="{y}" r="{r}" fill="rgba({accent_r},{accent_g},{accent_b},{opacity:.2f})"/>'
            )

        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
            f'preserveAspectRatio="xMidYMid slice">\n'
            f'  {"".join(lines_svg)}\n'
            f'  {"".join(dots_svg)}\n'
            f'</svg>'
        )

    @staticmethod
    def hex_mesh(size: int = 60, cols: int = 20, rows: int = 12,
                 accent_hex: str = "#B87333") -> str:
        """Generate hexagonal mesh background pattern."""
        accent_r, accent_g, accent_b = GeometricPatternGenerator._hex_to_rgb(accent_hex)
        hexagons = []
        for row in range(rows):
            for col in range(cols):
                cx = col * size * 1.5
                cy = row * size * math.sqrt(3) + (size * math.sqrt(3) / 2 if col % 2 else 0)
                points = []
                for i in range(6):
                    angle = math.pi / 3 * i + math.pi / 6
                    px = cx + (size * 0.45) * math.cos(angle)
                    py = cy + (size * 0.45) * math.sin(angle)
                    points.append(f"{px:.1f},{py:.1f}")
                opacity = 0.02 + 0.015 * math.sin(col * 0.3 + row * 0.5)
                hexagons.append(
                    f'<polygon points="{" ".join(points)}" fill="none" '
                    f'stroke="rgba({accent_r},{accent_g},{accent_b},{opacity:.3f})" stroke-width="0.4"/>'
                )
        w = cols * size * 1.5
        h = rows * size * math.sqrt(3)
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" '
            f'preserveAspectRatio="xMidYMid slice">\n'
            f'  {"".join(hexagons)}\n'
            f'</svg>'
        )

    @staticmethod
    def crystalline_field(width: int = 1200, height: int = 800, facets: int = 25, seed: int = 7,
                          accent_hex: str = "#B87333") -> str:
        """Generate crystalline/faceted background — Anthropic-style geometric art."""
        import random
        rng = random.Random(seed)
        accent_r, accent_g, accent_b = GeometricPatternGenerator._hex_to_rgb(accent_hex)
        triangles = []
        points = [(rng.randint(0, width), rng.randint(0, height)) for _ in range(facets)]
        # Add corners
        points.extend([(0,0), (width,0), (0,height), (width,height)])

        for i in range(len(points)):
            for j in range(i+1, len(points)):
                for k in range(j+1, len(points)):
                    x1,y1 = points[i]; x2,y2 = points[j]; x3,y3 = points[k]
                    # Only connect close triangles
                    side_a = math.sqrt((x2-x1)**2 + (y2-y1)**2)
                    side_b = math.sqrt((x3-x2)**2 + (y3-y2)**2)
                    side_c = math.sqrt((x1-x3)**2 + (y1-y3)**2)
                    if max(side_a, side_b, side_c) < 300:
                        opacity = rng.uniform(0.008, 0.03)
                        triangles.append(
                            f'<polygon points="{x1},{y1} {x2},{y2} {x3},{y3}" '
                            f'fill="rgba({accent_r},{accent_g},{accent_b},{opacity:.3f})" '
                            f'stroke="rgba({accent_r},{accent_g},{accent_b},0.015)" stroke-width="0.4"/>'
                        )
                    if len(triangles) > 120:
                        break
                if len(triangles) > 120:
                    break
            if len(triangles) > 120:
                break

        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
            f'preserveAspectRatio="xMidYMid slice">\n'
            f'  {"".join(triangles)}\n'
            f'</svg>'
        )


# ═══════════════════════════════════════════════════════════════════════════════
# WATCHMAKER PATTERN GENERATOR
# (Precision mechanism aesthetic for 3D dashboard)
# ═══════════════════════════════════════════════════════════════════════════════

class WatchmakerPatternGenerator:
    """
    Generates SVG watchmaker mechanism patterns for dashboard backgrounds.

    Design philosophy (Watchmaker Aesthetic - spec 012):
    - Precision: Every element serves a purpose, 4px grid alignment
    - Mechanism: Users see the system working — animated gears, flow lines
    - Depth: Information in discoverable layers (z-index hierarchy)
    - Function: Every UI element serves a specific purpose
    - Craft: Beauty emerges from functional perfection
    """

    @staticmethod
    def gear_svg(size: int = 100, teeth: int = 8, inner_radius: float = 0.35) -> str:
        """Generate a single gear SVG path for CSS/inline use."""
        center = size / 2
        outer_r = size * 0.45
        inner_r = size * inner_radius
        tooth_height = outer_r * 0.15

        points = []
        for i in range(teeth * 2):
            angle = (math.pi / teeth) * i - math.pi / 2
            if i % 2 == 0:
                # Tooth tip
                r = outer_r + tooth_height
            else:
                # Tooth valley
                r = outer_r
            x = center + r * math.cos(angle)
            y = center + r * math.sin(angle)
            points.append(f"{x:.1f},{y:.1f}")

        gear_path = " ".join(points)
        return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="{size}" height="{size}">
  <polygon points="{gear_path}" fill="none" stroke="currentColor" stroke-width="2"/>
  <circle cx="{center}" cy="{center}" r="{inner_r}" fill="currentColor"/>
</svg>'''

    @staticmethod
    def gear_mechanism_bg(width: int = 1920, height: int = 1080, gear_count: int = 5, seed: int = 42) -> str:
        """Generate a background pattern of interlocking gears."""
        import random
        rng = random.Random(seed)
        gears = []

        positions = [
            (0.05, 0.1, 120, 8),
            (0.08, 0.6, 80, 6),
            (0.85, 0.25, 150, 10),
            (0.9, 0.8, 100, 8),
            (0.4, 0.85, 60, 6),
        ]

        for i, (x_pct, y_pct, size, teeth) in enumerate(positions[:gear_count]):
            x = width * x_pct
            y = height * y_pct
            center = size / 2
            outer_r = size * 0.45
            tooth_height = outer_r * 0.15

            points = []
            for j in range(teeth * 2):
                angle = (math.pi / teeth) * j - math.pi / 2
                r = outer_r + tooth_height if j % 2 == 0 else outer_r
                px = center + r * math.cos(angle)
                py = center + r * math.sin(angle)
                points.append(f"{px:.1f},{py:.1f}")

            gear_path = " ".join(points)
            rotation_speed = 20 + i * 5
            direction = "-" if i % 2 else ""

            gears.append(f'''<g transform="translate({x:.0f},{y:.0f})" opacity="0.12">
    <animateTransform attributeName="transform" type="rotate" from="0 {center} {center}" to="{direction}360 {center} {center}" dur="{rotation_speed}s" repeatCount="indefinite" additive="sum"/>
    <polygon points="{gear_path}" fill="none" stroke="rgba(184,115,51,0.8)" stroke-width="3"/>
    <circle cx="{center}" cy="{center}" r="{size*0.15}" fill="rgba(184,115,51,0.6)"/>
</g>''')

        return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" preserveAspectRatio="xMidYMid slice">
  {chr(10).join(gears)}
</svg>'''

    @staticmethod
    def flow_line_pattern(width: int = 1200, height: int = 100, nodes: int = 5) -> str:
        """Generate a horizontal data flow line with animated pulses."""
        node_spacing = width / (nodes + 1)
        path_d = f"M 0,{height/2}"
        nodes_svg = []

        for i in range(nodes):
            x = node_spacing * (i + 1)
            path_d += f" L {x},{height/2}"
            nodes_svg.append(f'<circle cx="{x}" cy="{height/2}" r="6" fill="rgba(152,193,217,0.8)"/>')

        path_d += f" L {width},{height/2}"

        return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">
  <defs>
    <linearGradient id="flowGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="rgba(152,193,217,0)"/>
      <stop offset="50%" stop-color="rgba(152,193,217,0.8)"/>
      <stop offset="100%" stop-color="rgba(152,193,217,0)"/>
    </linearGradient>
  </defs>
  <path d="{path_d}" fill="none" stroke="rgba(152,193,217,0.3)" stroke-width="2"/>
  <path d="{path_d}" fill="none" stroke="url(#flowGrad)" stroke-width="2" stroke-dasharray="20 40">
    <animate attributeName="stroke-dashoffset" from="0" to="-60" dur="1.5s" repeatCount="indefinite"/>
  </path>
  {chr(10).join(nodes_svg)}
</svg>'''

    @staticmethod
    def status_jewel_svg(size: int = 16, status: str = "active") -> str:
        """Generate a status jewel indicator."""
        colors = {
            "active": "#22C55E",
            "pending": "#F59E0B",
            "error": "#EF4444",
            "inactive": "#6B7280",
        }
        color = colors.get(status, colors["inactive"])
        center = size / 2

        return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="{size}" height="{size}">
  <defs>
    <radialGradient id="jewelGrad_{status}">
      <stop offset="30%" stop-color="{color}" stop-opacity="1"/>
      <stop offset="100%" stop-color="{color}" stop-opacity="0.6"/>
    </radialGradient>
    <filter id="jewelGlow_{status}">
      <feGaussianBlur stdDeviation="1.5" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
  <circle cx="{center}" cy="{center}" r="{size*0.4}" fill="url(#jewelGrad_{status})" filter="url(#jewelGlow_{status})"/>
  <circle cx="{center*0.7}" cy="{center*0.7}" r="{size*0.1}" fill="rgba(255,255,255,0.4)"/>
</svg>'''


# ═══════════════════════════════════════════════════════════════════════════════
# LOGO GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════

class SlateLogoGenerator:
    """
    Procedural SVG logo generator for S.L.A.T.E.

    Design concept: Layered hexagonal lattice with neural pathways —
    represents the "synchronized living architecture" of interconnected agents.
    """

    @staticmethod
    # Modified: 2026-02-08T02:39:00Z | Author: COPILOT | Change: support theme accent colors in logo
    def generate(size: int = 128, variant: str = "full",
                 accent: str = "#B87333", accent_dim: str = "#8B5E2B") -> str:
        """Generate SLATE logo SVG (hexagonal lattice variant)."""
        half = size / 2
        hex_points = []
        for i in range(6):
            angle = math.pi / 3 * i - math.pi / 6
            hex_points.append((
                half + half * 0.65 * math.cos(angle),
                half + half * 0.65 * math.sin(angle)
            ))
        hex_str = " ".join(f"{x:.1f},{y:.1f}" for x, y in hex_points)
        inner_nodes = []
        for ring in range(3):
            r = half * (0.15 + ring * 0.18)
            count = 6 * (ring + 1)
            for i in range(count):
                angle = (2 * math.pi / count) * i + ring * 0.2
                cx = half + r * math.cos(angle)
                cy = half + r * math.sin(angle)
                node_r = 1.5 - ring * 0.3
                opacity = 0.8 - ring * 0.2
                inner_nodes.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{node_r}" fill="{accent}" opacity="{opacity}"/>')
        connections = []
        for ring in range(2):
            r1 = half * (0.15 + ring * 0.18)
            r2 = half * (0.15 + (ring + 1) * 0.18)
            count = 6 * (ring + 1)
            for i in range(count):
                angle1 = (2 * math.pi / count) * i + ring * 0.2
                angle2 = (2 * math.pi / (count + 6)) * i + (ring + 1) * 0.2
                x1, y1 = half + r1 * math.cos(angle1), half + r1 * math.sin(angle1)
                x2, y2 = half + r2 * math.cos(angle2), half + r2 * math.sin(angle2)
                connections.append(
                    f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                    f'stroke="{accent}" stroke-width="0.5" opacity="0.2"/>'
                )
        center_glow = (
            f'<circle cx="{half}" cy="{half}" r="{half*0.12}" fill="url(#centerGlow)"/>'
            f'<circle cx="{half}" cy="{half}" r="{half*0.06}" fill="{accent}" opacity="0.9"/>'
        )
        defs = (
            f'<defs>'
            f'<radialGradient id="centerGlow"><stop offset="0%" stop-color="{accent}" stop-opacity="0.5"/>'
            f'<stop offset="100%" stop-color="{accent}" stop-opacity="0"/></radialGradient>'
            f'<linearGradient id="hexGrad" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="{accent}" stop-opacity="0.12"/>'
            f'<stop offset="100%" stop-color="{accent_dim}" stop-opacity="0.04"/></linearGradient>'
            f'</defs>'
        )
        body = (
            f'<polygon points="{hex_str}" fill="url(#hexGrad)" stroke="{accent}" stroke-width="1.2" opacity="0.7"/>'
            f'{"".join(connections)}{"".join(inner_nodes)}{center_glow}'
        )
        if variant == "icon":
            return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="{size}" height="{size}">{defs}{body}</svg>'
        elif variant == "full":
            total_w = size + 220
            return (
                f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total_w} {size}" width="{total_w}" height="{size}">'
                f'{defs}{body}'
                f'<text x="{size + 16}" y="{half - 8}" fill="#F8F8F8" font-family="Georgia, serif" '
                f'font-size="{size*0.28}" font-weight="700" letter-spacing="0.08em">S.L.A.T.E.</text>'
                f'<text x="{size + 16}" y="{half + size*0.16}" fill="#B0B0B0" font-family="Georgia, serif" '
                f'font-size="{size*0.1}" font-weight="400" letter-spacing="0.15em">SYNCHRONIZED LIVING ARCHITECTURE</text>'
                f'</svg>'
            )
        else:
            return (
                f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 60" width="400" height="60">'
                f'<text x="0" y="38" fill="#F8F8F8" font-family="Georgia, serif" '
                f'font-size="36" font-weight="700" letter-spacing="0.08em">S.L.A.T.E.</text>'
                f'<text x="0" y="55" fill="#B0B0B0" font-family="Georgia, serif" '
                f'font-size="11" font-weight="400" letter-spacing="0.15em">SYNCHRONIZED LIVING ARCHITECTURE</text>'
                f'</svg>'
            )


# ═══════════════════════════════════════════════════════════════════════════════
# ATHENA LOGO GENERATOR
# Modified: 2026-02-08T03:00:00Z | Author: COPILOT | Change: dedicated Athena owl+shield logo
# ═══════════════════════════════════════════════════════════════════════════════

class AthenaLogoGenerator:
    """
    Procedural SVG logo generator for SLATE-ATHENA identity.

    Design concept: Owl of Athena perched on a shield — minimalist line art
    inspired by ancient Greek pottery/coin art. The owl's eyes are concentric
    circles (representing wisdom/vigilance), sitting atop an inverted
    triangular shield (representing strategic protection). A subtle spear
    line crosses behind, referencing Athena's martial aspect.

    The logo is generated entirely as SVG paths — no raster assets.
    Scales from 16px favicon to 512px hero without quality loss.
    """

    @staticmethod
    def generate(size: int = 128, variant: str = "full",
                 gold: str = "#D4AF37", gold_dim: str = "#B08A2E",
                 aegean: str = "#1A3A52", white: str = "#F8F8F8") -> str:
        """Generate Athena owl+shield logo SVG.

        Variants:
          - "icon": Owl mark only (square)
          - "full": Owl + S.L.A.T.E. wordmark
          - "wordmark": Text with Greek key underline
        """
        s = size  # shorthand
        h = s / 2
        # Scale factor relative to 128-unit grid
        k = s / 128

        # ── Owl body paths (designed on 128×128 grid, scaled by k) ──
        # Ear tufts
        ear_l = f"M{42*k:.1f},{38*k:.1f} L{50*k:.1f},{22*k:.1f} L{56*k:.1f},{36*k:.1f}"
        ear_r = f"M{86*k:.1f},{38*k:.1f} L{78*k:.1f},{22*k:.1f} L{72*k:.1f},{36*k:.1f}"
        # Head dome
        head = f"M{40*k:.1f},{50*k:.1f} C{40*k:.1f},{30*k:.1f} {52*k:.1f},{24*k:.1f} {64*k:.1f},{24*k:.1f} C{76*k:.1f},{24*k:.1f} {88*k:.1f},{30*k:.1f} {88*k:.1f},{50*k:.1f}"
        # Body (rounded trapezoid)
        body = (
            f"M{40*k:.1f},{50*k:.1f} "
            f"C{38*k:.1f},{62*k:.1f} {40*k:.1f},{82*k:.1f} {48*k:.1f},{90*k:.1f} "
            f"L{80*k:.1f},{90*k:.1f} "
            f"C{88*k:.1f},{82*k:.1f} {90*k:.1f},{62*k:.1f} {88*k:.1f},{50*k:.1f}"
        )
        # Breast feather chevrons
        chevrons = []
        for i in range(3):
            y_off = 64 + i * 8
            chevrons.append(
                f"M{54*k:.1f},{y_off*k:.1f} L{64*k:.1f},{(y_off+5)*k:.1f} L{74*k:.1f},{y_off*k:.1f}"
            )
        chevron_paths = " ".join(chevrons)
        # Feet / talons
        feet_l = f"M{52*k:.1f},{90*k:.1f} L{48*k:.1f},{98*k:.1f} M{52*k:.1f},{90*k:.1f} L{54*k:.1f},{98*k:.1f}"
        feet_r = f"M{76*k:.1f},{90*k:.1f} L{74*k:.1f},{98*k:.1f} M{76*k:.1f},{90*k:.1f} L{80*k:.1f},{98*k:.1f}"
        # Wing hints
        wing_l = f"M{40*k:.1f},{55*k:.1f} C{30*k:.1f},{60*k:.1f} {28*k:.1f},{72*k:.1f} {36*k:.1f},{80*k:.1f}"
        wing_r = f"M{88*k:.1f},{55*k:.1f} C{98*k:.1f},{60*k:.1f} {100*k:.1f},{72*k:.1f} {92*k:.1f},{80*k:.1f}"
        # Spear (diagonal behind owl)
        spear = f"M{18*k:.1f},{104*k:.1f} L{110*k:.1f},{14*k:.1f}"
        spear_tip = f"M{108*k:.1f},{18*k:.1f} L{110*k:.1f},{14*k:.1f} L{113*k:.1f},{20*k:.1f}"

        # ── Eyes (concentric circles — the signature element) ──
        eye_r_size = 7 * k
        eye_lx, eye_rx = 52 * k, 76 * k
        eye_y = 46 * k
        eyes = (
            # Left eye — outer ring
            f'<circle cx="{eye_lx:.1f}" cy="{eye_y:.1f}" r="{eye_r_size:.1f}" fill="none" stroke="{gold}" stroke-width="{1.5*k:.1f}"/>'
            # Left eye — iris
            f'<circle cx="{eye_lx:.1f}" cy="{eye_y:.1f}" r="{4*k:.1f}" fill="{gold}" opacity="0.7"/>'
            # Left eye — pupil
            f'<circle cx="{eye_lx:.1f}" cy="{eye_y:.1f}" r="{2*k:.1f}" fill="{aegean}"/>'
            # Right eye — outer ring
            f'<circle cx="{eye_rx:.1f}" cy="{eye_y:.1f}" r="{eye_r_size:.1f}" fill="none" stroke="{gold}" stroke-width="{1.5*k:.1f}"/>'
            # Right eye — iris
            f'<circle cx="{eye_rx:.1f}" cy="{eye_y:.1f}" r="{4*k:.1f}" fill="{gold}" opacity="0.7"/>'
            # Right eye — pupil
            f'<circle cx="{eye_rx:.1f}" cy="{eye_y:.1f}" r="{2*k:.1f}" fill="{aegean}"/>'
        )
        # Beak
        beak = f'<path d="M{61*k:.1f},{52*k:.1f} L{64*k:.1f},{58*k:.1f} L{67*k:.1f},{52*k:.1f}" fill="none" stroke="{gold}" stroke-width="{1.2*k:.1f}" stroke-linejoin="round"/>'

        # ── Shield outline (subtle, behind owl) ──
        shield = (
            f'<path d="M{30*k:.1f},{36*k:.1f} L{64*k:.1f},{108*k:.1f} L{98*k:.1f},{36*k:.1f} Z" '
            f'fill="none" stroke="{gold}" stroke-width="{0.8*k:.1f}" opacity="0.18"/>'
        )

        # ── Greek key border (decorative bottom bar) ──
        gk_y = 112 * k
        gk_step = 6 * k
        greek_key_d = f"M{32*k:.1f},{gk_y:.1f}"
        for i in range(8):
            x = 32 * k + i * gk_step * 2
            greek_key_d += (
                f" l{gk_step:.1f},0 l0,{-gk_step*0.6:.1f}"
                f" l{-gk_step*0.5:.1f},0 l0,{gk_step*0.6:.1f}"
                f" l{gk_step:.1f},0"
            )

        stroke_w = max(1.5, 2 * k)

        defs = (
            f'<defs>'
            f'<radialGradient id="athenaGlow">'
            f'<stop offset="0%" stop-color="{gold}" stop-opacity="0.30"/>'
            f'<stop offset="100%" stop-color="{gold}" stop-opacity="0"/>'
            f'</radialGradient>'
            f'<linearGradient id="athenaBodyGrad" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0%" stop-color="{gold}" stop-opacity="0.08"/>'
            f'<stop offset="100%" stop-color="{gold_dim}" stop-opacity="0.02"/>'
            f'</linearGradient>'
            f'</defs>'
        )

        owl_group = (
            # Background glow
            f'<circle cx="{h:.1f}" cy="{55*k:.1f}" r="{42*k:.1f}" fill="url(#athenaGlow)"/>'
            # Shield behind owl
            f'{shield}'
            # Spear behind owl
            f'<path d="{spear}" stroke="{gold}" stroke-width="{0.7*k:.1f}" opacity="0.22"/>'
            f'<path d="{spear_tip}" fill="none" stroke="{gold}" stroke-width="{1*k:.1f}" opacity="0.30"/>'
            # Body fill (subtle)
            f'<path d="{body}" fill="url(#athenaBodyGrad)" stroke="none"/>'
            # Head + body outline
            f'<path d="{head}" fill="none" stroke="{gold}" stroke-width="{stroke_w:.1f}" stroke-linecap="round"/>'
            f'<path d="{body}" fill="none" stroke="{gold}" stroke-width="{stroke_w:.1f}" stroke-linecap="round"/>'
            # Ear tufts
            f'<path d="{ear_l}" fill="none" stroke="{gold}" stroke-width="{stroke_w:.1f}" stroke-linecap="round"/>'
            f'<path d="{ear_r}" fill="none" stroke="{gold}" stroke-width="{stroke_w:.1f}" stroke-linecap="round"/>'
            # Wings
            f'<path d="{wing_l}" fill="none" stroke="{gold}" stroke-width="{1*k:.1f}" opacity="0.5"/>'
            f'<path d="{wing_r}" fill="none" stroke="{gold}" stroke-width="{1*k:.1f}" opacity="0.5"/>'
            # Breast chevrons
            f'<path d="{chevron_paths}" fill="none" stroke="{gold}" stroke-width="{0.8*k:.1f}" opacity="0.4"/>'
            # Eyes (signature)
            f'{eyes}'
            # Beak
            f'{beak}'
            # Feet
            f'<path d="{feet_l}" fill="none" stroke="{gold}" stroke-width="{1*k:.1f}" opacity="0.5"/>'
            f'<path d="{feet_r}" fill="none" stroke="{gold}" stroke-width="{1*k:.1f}" opacity="0.5"/>'
            # Greek key bottom
            f'<path d="{greek_key_d}" fill="none" stroke="{gold}" stroke-width="{0.6*k:.1f}" opacity="0.25"/>'
        )

        if variant == "icon":
            return (
                f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {s} {s}" '
                f'width="{s}" height="{s}">{defs}{owl_group}</svg>'
            )
        elif variant == "full":
            total_w = s + int(s * 2.2)
            text_x = s + 12 * k
            title_y = h - 4 * k
            sub_y = h + 14 * k
            return (
                f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total_w} {s}" '
                f'width="{total_w}" height="{s}">{defs}{owl_group}'
                f'<text x="{text_x:.0f}" y="{title_y:.0f}" fill="{white}" '
                f'font-family="Georgia, \'Times New Roman\', serif" '
                f'font-size="{s*0.24:.0f}" font-weight="700" letter-spacing="0.10em">'
                f'S.L.A.T.E.</text>'
                f'<text x="{text_x:.0f}" y="{sub_y:.0f}" fill="{gold}" opacity="0.7" '
                f'font-family="Georgia, \'Times New Roman\', serif" '
                f'font-size="{s*0.07:.0f}" font-weight="400" letter-spacing="0.22em">'
                f'WISDOM MEETS PRECISION</text>'
                f'</svg>'
            )
        else:  # wordmark
            kw = 60 / 128
            bar_y = 46
            return (
                f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 60" width="400" height="60">'
                f'<text x="0" y="36" fill="{white}" font-family="Georgia, \'Times New Roman\', serif" '
                f'font-size="34" font-weight="700" letter-spacing="0.10em">S.L.A.T.E.</text>'
                f'<line x1="0" y1="{bar_y}" x2="240" y2="{bar_y}" stroke="{gold}" stroke-width="1" opacity="0.4"/>'
                f'<text x="0" y="56" fill="{gold}" opacity="0.6" '
                f'font-family="Georgia, \'Times New Roman\', serif" '
                f'font-size="10" font-weight="400" letter-spacing="0.22em">'
                f'WISDOM MEETS PRECISION</text>'
                f'</svg>'
            )


# ═══════════════════════════════════════════════════════════════════════════════
# BUILD PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════

def build_design_assets(output_dir: str = None) -> Dict[str, str]:
    """Build all design assets and return paths."""
    if output_dir is None:
        output_dir = str(WORKSPACE_ROOT / "slate_web" / "generated")

    os.makedirs(output_dir, exist_ok=True)
    assets = {}

    # 1. Design tokens CSS (dark + light + athena)
    dark_css = SlateDesignTokens.to_css("dark")
    light_css = SlateDesignTokens.to_css("light")
    athena_css = SlateDesignTokens.to_css("athena")
    tokens_path = os.path.join(output_dir, "tokens.css")
    with open(tokens_path, "w", encoding="utf-8") as f:
        f.write(f"/* SLATE Design Tokens - Generated {datetime.now(timezone.utc).isoformat()} */\n\n")
        f.write("/* Dark Theme (default) */\n")
        f.write(dark_css + "\n\n")
        f.write("/* Light Theme */\n")
        f.write("[data-theme='light'] " + light_css.replace(":root", "") + "\n\n")
        f.write("/* Athena Theme */\n")
        f.write("[data-theme='athena'] " + athena_css.replace(":root", "") + "\n")
    assets["tokens_css"] = tokens_path

    # Modified: 2026-02-08T03:15:00Z | Author: COPILOT | Change: export Athena owl logo variants
    # 2. Logo variants (lattice + Athena owl)
    for variant in ["icon", "full", "wordmark"]:
        logo_svg = SlateLogoGenerator.generate(128 if variant != "wordmark" else 60, variant)
        logo_path = os.path.join(output_dir, f"logo-{variant}.svg")
        with open(logo_path, "w", encoding="utf-8") as f:
            f.write(logo_svg)
        assets[f"logo_{variant}"] = logo_path

    # 2b. Athena owl logo variants
    athena = SlateDesignTokens.ATHENA
    for variant in ["icon", "full", "wordmark"]:
        owl_svg = AthenaLogoGenerator.generate(
            128 if variant != "wordmark" else 60, variant,
            gold=athena["gold"], gold_dim=athena["gold_dim"],
            aegean=athena["aegean"], white=athena["thunderbolt"]
        )
        owl_path = os.path.join(output_dir, f"athena-{variant}.svg")
        with open(owl_path, "w", encoding="utf-8") as f:
            f.write(owl_svg)
        assets[f"athena_{variant}"] = owl_path

    # 3. Background patterns
    patterns = {
        "constellation": GeometricPatternGenerator.constellation_grid(),
        "hexmesh": GeometricPatternGenerator.hex_mesh(),
        "crystalline": GeometricPatternGenerator.crystalline_field(),
        "gears": WatchmakerPatternGenerator.gear_mechanism_bg(),
        "flowline": WatchmakerPatternGenerator.flow_line_pattern(),
    }
    for name, svg in patterns.items():
        pat_path = os.path.join(output_dir, f"pattern-{name}.svg")
        with open(pat_path, "w", encoding="utf-8") as f:
            f.write(svg)
        assets[f"pattern_{name}"] = pat_path

    # 4. Status jewel variants
    for status in ["active", "pending", "error", "inactive"]:
        jewel_svg = WatchmakerPatternGenerator.status_jewel_svg(16, status)
        jewel_path = os.path.join(output_dir, f"jewel-{status}.svg")
        with open(jewel_path, "w", encoding="utf-8") as f:
            f.write(jewel_svg)
        assets[f"jewel_{status}"] = jewel_path

    # 5. Token JSON export (for VS Code theme generation)
    tokens_json = SlateDesignTokens.generate_tokens("dark")
    json_path = os.path.join(output_dir, "tokens.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(tokens_json, f, indent=2)
    assets["tokens_json"] = json_path

    print(f"[SLATE Design System] Built {len(assets)} assets -> {output_dir}")
    return assets


if __name__ == "__main__":
    assets = build_design_assets()
    for name, path in assets.items():
        print(f"  {name}: {path}")
