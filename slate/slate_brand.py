#!/usr/bin/env python3
"""
SLATE Brand Identity Engine
============================

Manages the SLATE brand identity system: design tokens, logo assets,
theme consistency, branded CLI output, and brand health validation.

This module ties together all brand surfaces:
- .slate_identity/design-tokens.json  (source of truth)
- .slate_identity/design-tokens.css   (web distribution)
- .slate_identity/theme.css           (procedural theme)
- .slate_identity/theme-locked.css    (locked theme)
- .slate_identity/logos/              (SVG logo assets)
- .slate_identity/config.json         (identity configuration)
- slate/design_tokens.py              (Python token module)
- docs/pages/                         (GitHub Pages brand)

Brand Philosophy: Watchmaker + Blueprint + Living System
"Systems evolve with progress" — beauty emerges from function.
"""
# Modified: 2026-02-09T18:00:00Z | Author: Claude Opus 4.6 | Change: Create brand engine module

import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

WORKSPACE_ROOT = Path(__file__).parent.parent
IDENTITY_DIR = WORKSPACE_ROOT / ".slate_identity"
TOKENS_JSON = IDENTITY_DIR / "design-tokens.json"
TOKENS_CSS = IDENTITY_DIR / "design-tokens.css"
THEME_CSS = IDENTITY_DIR / "theme.css"
THEME_LOCKED_CSS = IDENTITY_DIR / "theme-locked.css"
CONFIG_JSON = IDENTITY_DIR / "config.json"
LOGOS_DIR = IDENTITY_DIR / "logos"
PAGES_DIR = WORKSPACE_ROOT / "docs" / "pages"

# ── SLATE Brand Colors (ANSI Terminal) ─────────────────────────────────

# ANSI 256-color codes closest to SLATE palette
ANSI = {
    "primary":   "\033[38;2;184;90;60m",     # #B85A3C warm rust
    "secondary": "\033[38;2;93;93;116m",      # #5D5D74 muted purple
    "tertiary":  "\033[38;2;107;142;35m",     # #6B8E23 olive green
    "blueprint": "\033[38;2;13;27;42m",       # #0D1B2A deep navy
    "accent":    "\033[38;2;79;195;247m",     # #4FC3F7 blueprint cyan
    "success":   "\033[38;2;76;175;80m",      # #4CAF50
    "warning":   "\033[38;2;255;152;0m",      # #FF9800
    "error":     "\033[38;2;244;67;54m",      # #F44336
    "info":      "\033[38;2;33;150;243m",     # #2196F3
    "dim":       "\033[38;2;125;120;115m",    # #7D7873 outline
    "surface":   "\033[38;2;232;226;222m",    # #E8E2DE on_surface_dark
    "bold":      "\033[1m",
    "reset":     "\033[0m",
}


# ── Data Classes ───────────────────────────────────────────────────────

@dataclass
class BrandAsset:
    """Represents a brand asset with its status."""
    name: str
    path: str
    exists: bool
    size_bytes: int = 0
    category: str = "unknown"

    @property
    def status(self) -> str:
        if not self.exists:
            return "missing"
        if self.size_bytes < 10:
            return "empty"
        return "ok"


@dataclass
class TokenValidation:
    """Result of design token consistency check."""
    source: str
    target: str
    total_tokens: int = 0
    matched: int = 0
    missing: list = field(default_factory=list)
    extra: list = field(default_factory=list)

    @property
    def consistent(self) -> bool:
        return len(self.missing) == 0

    @property
    def percentage(self) -> float:
        if self.total_tokens == 0:
            return 100.0
        return round(self.matched / self.total_tokens * 100, 1)


@dataclass
class BrandReport:
    """Complete brand health report."""
    timestamp: str
    assets: list
    token_validations: list
    logo_count: int = 0
    theme_count: int = 0
    pages_branded: int = 0
    overall_health: str = "unknown"


# ── Brand Engine ───────────────────────────────────────────────────────

class SLATEBrand:
    """SLATE Brand Identity Engine."""

    def __init__(self):
        self.tokens = self._load_tokens()
        self.config = self._load_config()

    def _load_tokens(self) -> dict:
        """Load design tokens from JSON source of truth."""
        if not TOKENS_JSON.exists():
            return {}
        try:
            return json.loads(TOKENS_JSON.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _load_config(self) -> dict:
        """Load identity configuration."""
        if not CONFIG_JSON.exists():
            return {}
        try:
            return json.loads(CONFIG_JSON.read_text(encoding="utf-8"))
        except Exception:
            return {}

    # ── Asset Inventory ────────────────────────────────────────────────

    def inventory_assets(self) -> list[BrandAsset]:
        """Inventory all brand assets and their status."""
        assets = []

        # Design token files
        token_files = [
            ("Design Tokens (JSON)", TOKENS_JSON, "tokens"),
            ("Design Tokens (CSS)", TOKENS_CSS, "tokens"),
            ("Identity Config", CONFIG_JSON, "config"),
        ]
        for name, path, cat in token_files:
            exists = path.exists()
            size = path.stat().st_size if exists else 0
            assets.append(BrandAsset(name=name, path=str(path.relative_to(WORKSPACE_ROOT)), exists=exists, size_bytes=size, category=cat))

        # Theme files
        theme_files = [
            ("Procedural Theme", THEME_CSS, "theme"),
            ("Locked Theme", THEME_LOCKED_CSS, "theme"),
        ]
        for name, path, cat in theme_files:
            exists = path.exists()
            size = path.stat().st_size if exists else 0
            assets.append(BrandAsset(name=name, path=str(path.relative_to(WORKSPACE_ROOT)), exists=exists, size_bytes=size, category=cat))

        # Logo files
        if LOGOS_DIR.exists():
            for logo in sorted(LOGOS_DIR.glob("*.svg")):
                assets.append(BrandAsset(
                    name=logo.stem,
                    path=str(logo.relative_to(WORKSPACE_ROOT)),
                    exists=True,
                    size_bytes=logo.stat().st_size,
                    category="logo",
                ))

        # Root logo
        root_logo = IDENTITY_DIR / "logo.svg"
        if root_logo.exists():
            assets.append(BrandAsset(
                name="Root Logo",
                path=str(root_logo.relative_to(WORKSPACE_ROOT)),
                exists=True,
                size_bytes=root_logo.stat().st_size,
                category="logo",
            ))

        # Pages logo
        pages_logo = PAGES_DIR / "assets" / "slate-logo-v2.svg"
        if pages_logo.exists():
            assets.append(BrandAsset(
                name="Pages Logo (v2)",
                path=str(pages_logo.relative_to(WORKSPACE_ROOT)),
                exists=True,
                size_bytes=pages_logo.stat().st_size,
                category="logo",
            ))

        # Python token module
        py_tokens = WORKSPACE_ROOT / "slate" / "design_tokens.py"
        if py_tokens.exists():
            assets.append(BrandAsset(
                name="Python Token Module",
                path="slate/design_tokens.py",
                exists=True,
                size_bytes=py_tokens.stat().st_size,
                category="tokens",
            ))

        # GitHub Pages
        if PAGES_DIR.exists():
            for page in sorted(PAGES_DIR.glob("*.html")):
                assets.append(BrandAsset(
                    name=f"Page: {page.stem}",
                    path=str(page.relative_to(WORKSPACE_ROOT)),
                    exists=True,
                    size_bytes=page.stat().st_size,
                    category="page",
                ))

        return assets

    # ── Token Validation ───────────────────────────────────────────────

    def validate_tokens_css(self) -> TokenValidation:
        """Validate JSON tokens match CSS custom properties."""
        validation = TokenValidation(source="design-tokens.json", target="design-tokens.css")

        if not TOKENS_CSS.exists():
            validation.missing = ["CSS file not found"]
            return validation

        css_content = TOKENS_CSS.read_text(encoding="utf-8")

        # Flatten JSON tokens to expected CSS variable names
        expected_vars = []
        for category, values in self.tokens.items():
            if isinstance(values, dict):
                for key, val in values.items():
                    css_name = f"--slate-{key.replace('_', '-')}"
                    expected_vars.append(css_name)

        validation.total_tokens = len(expected_vars)

        for var_name in expected_vars:
            if var_name in css_content:
                validation.matched += 1
            else:
                validation.missing.append(var_name)

        return validation

    def validate_primary_color(self) -> dict:
        """Verify the primary color #B85A3C appears across all surfaces."""
        primary = self.tokens.get("colors", {}).get("primary", "#B85A3C")
        results = {}

        # Check JSON tokens
        results["design-tokens.json"] = primary in json.dumps(self.tokens)

        # Check CSS tokens
        if TOKENS_CSS.exists():
            results["design-tokens.css"] = primary in TOKENS_CSS.read_text(encoding="utf-8")

        # Check themes
        if THEME_CSS.exists():
            results["theme.css"] = primary.lower() in THEME_CSS.read_text(encoding="utf-8").lower()
        if THEME_LOCKED_CSS.exists():
            content = THEME_LOCKED_CSS.read_text(encoding="utf-8").lower()
            results["theme-locked.css"] = primary.lower() in content

        # Check GitHub Pages
        index_html = PAGES_DIR / "index.html"
        if index_html.exists():
            results["pages/index.html"] = primary.lower() in index_html.read_text(encoding="utf-8").lower()

        # Check avatar page
        avatar_html = PAGES_DIR / "avatar.html"
        if avatar_html.exists():
            results["pages/avatar.html"] = primary.lower() in avatar_html.read_text(encoding="utf-8").lower()

        return results

    # ── Brand Health Report ────────────────────────────────────────────

    def generate_report(self) -> BrandReport:
        """Generate a comprehensive brand health report."""
        assets = self.inventory_assets()
        token_validation = self.validate_tokens_css()
        color_check = self.validate_primary_color()

        logo_count = sum(1 for a in assets if a.category == "logo" and a.status == "ok")
        theme_count = sum(1 for a in assets if a.category == "theme" and a.status == "ok")
        pages_count = sum(1 for a in assets if a.category == "page" and a.status == "ok")

        # Calculate overall health
        total_checks = 0
        passed = 0

        # Asset existence
        for a in assets:
            if a.category in ("tokens", "theme", "config"):
                total_checks += 1
                if a.status == "ok":
                    passed += 1

        # Token consistency
        total_checks += 1
        if token_validation.percentage >= 90:
            passed += 1

        # Primary color propagation
        color_surfaces = list(color_check.values())
        total_checks += len(color_surfaces)
        passed += sum(1 for v in color_surfaces if v)

        # Logos
        total_checks += 1
        if logo_count >= 3:
            passed += 1

        if total_checks == 0:
            health = "unknown"
        elif passed / total_checks >= 0.9:
            health = "excellent"
        elif passed / total_checks >= 0.7:
            health = "good"
        elif passed / total_checks >= 0.5:
            health = "fair"
        else:
            health = "poor"

        return BrandReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            assets=assets,
            token_validations=[token_validation],
            logo_count=logo_count,
            theme_count=theme_count,
            pages_branded=pages_count,
            overall_health=health,
        )

    # ── Branded CLI Output ─────────────────────────────────────────────

    @staticmethod
    def _c(color: str, text: str) -> str:
        """Colorize text with SLATE brand colors (ANSI true color)."""
        code = ANSI.get(color, "")
        reset = ANSI["reset"]
        return f"{code}{text}{reset}"

    def print_banner(self):
        """Print the SLATE branded banner."""
        c = self._c
        print()
        print(c("primary", "  ============================================================"))
        print(c("primary", "    S.L.A.T.E.") + c("dim", " | Synchronized Living Architecture"))
        print(c("primary", "    ") + c("accent", "Brand Identity System"))
        print(c("primary", "  ============================================================"))

    def print_status(self):
        """Print branded status report to CLI."""
        c = self._c
        report = self.generate_report()

        self.print_banner()
        print()

        # Overall health
        health_color = {
            "excellent": "success", "good": "success",
            "fair": "warning", "poor": "error", "unknown": "dim",
        }.get(report.overall_health, "dim")
        print(f"  Brand Health: {c(health_color, report.overall_health.upper())}")
        print()

        # Primary color
        primary = self.tokens.get("colors", {}).get("primary", "#B85A3C")
        print(f"  Primary Color: {c('primary', primary)}")
        color_check = self.validate_primary_color()
        for surface, present in color_check.items():
            icon = c("success", "[OK]") if present else c("error", "[!!]")
            print(f"    {icon} {surface}")
        print()

        # Assets
        print(f"  Assets: {len(report.assets)} total")
        categories = {}
        for a in report.assets:
            categories.setdefault(a.category, []).append(a)

        for cat in ["tokens", "config", "theme", "logo", "page"]:
            items = categories.get(cat, [])
            if not items:
                continue
            ok = sum(1 for i in items if i.status == "ok")
            total = len(items)
            print(f"    {cat.title():12s}: {ok}/{total}")
        print()

        # Token consistency
        for tv in report.token_validations:
            icon = c("success", "[OK]") if tv.consistent else c("warning", "[..]")
            print(f"  Token Sync: {icon} {tv.source} -> {tv.target}")
            print(f"    {tv.matched}/{tv.total_tokens} tokens ({tv.percentage}%)")
            if tv.missing and len(tv.missing) <= 5:
                for m in tv.missing:
                    print(f"    {c('warning', '  missing')}: {m}")
            elif tv.missing:
                print(f"    {c('warning', f'  {len(tv.missing)} missing tokens')}")
        print()

        # Design system specs
        print("  Design Specs:")
        specs = [
            ("007", "Unified Design System", "complete"),
            ("012", "Watchmaker 3D Dashboard", "complete"),
            ("013", "Engineering Drawing Theme", "complete"),
            ("014", "Watchmaker Golden Ratio UI", "complete"),
            ("022", "Brand Identity System", "in_progress"),
            ("023", "Avatar System", "in_progress"),
            ("024", "TRELLIS.2 3D Integration", "available"),
        ]
        for num, name, status in specs:
            if status == "complete":
                icon = c("success", "[OK]")
            elif status == "in_progress":
                icon = c("warning", "[..]")
            else:
                icon = c("dim", "[--]")
            print(f"    {icon} Spec {num}: {name}")
        print()

        print(c("primary", "  ============================================================"))
        print()

    def export_report_json(self) -> dict:
        """Export brand report as JSON-serializable dict."""
        report = self.generate_report()
        return {
            "timestamp": report.timestamp,
            "overall_health": report.overall_health,
            "logo_count": report.logo_count,
            "theme_count": report.theme_count,
            "pages_branded": report.pages_branded,
            "primary_color": self.tokens.get("colors", {}).get("primary", "#B85A3C"),
            "color_propagation": self.validate_primary_color(),
            "assets": [
                {
                    "name": a.name,
                    "path": a.path,
                    "status": a.status,
                    "category": a.category,
                    "size_bytes": a.size_bytes,
                }
                for a in report.assets
            ],
            "token_sync": [
                {
                    "source": tv.source,
                    "target": tv.target,
                    "percentage": tv.percentage,
                    "missing_count": len(tv.missing),
                }
                for tv in report.token_validations
            ],
        }


# ── Module-Level Helpers ───────────────────────────────────────────────

_brand: Optional[SLATEBrand] = None


def get_brand() -> SLATEBrand:
    """Get or create the brand singleton."""
    global _brand
    if _brand is None:
        _brand = SLATEBrand()
    return _brand


# ── CLI ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="SLATE Brand Identity Engine")
    parser.add_argument("--status", action="store_true", help="Show brand status report")
    parser.add_argument("--json", action="store_true", help="Export report as JSON")
    parser.add_argument("--validate", action="store_true", help="Validate token consistency")
    parser.add_argument("--assets", action="store_true", help="List all brand assets")
    parser.add_argument("--colors", action="store_true", help="Check primary color propagation")

    args = parser.parse_args()
    brand = get_brand()

    if args.json:
        report = brand.export_report_json()
        print(json.dumps(report, indent=2))
    elif args.validate:
        tv = brand.validate_tokens_css()
        print(f"Token Sync: {tv.source} -> {tv.target}")
        print(f"  Matched: {tv.matched}/{tv.total_tokens} ({tv.percentage}%)")
        if tv.missing:
            print(f"  Missing ({len(tv.missing)}):")
            for m in tv.missing[:10]:
                print(f"    - {m}")
            if len(tv.missing) > 10:
                print(f"    ... and {len(tv.missing) - 10} more")
        else:
            print("  All tokens consistent!")
    elif args.assets:
        assets = brand.inventory_assets()
        for a in assets:
            icon = "[OK]" if a.status == "ok" else "[!!]" if a.status == "missing" else "[..]"
            size = f"{a.size_bytes:,}B" if a.size_bytes > 0 else "---"
            print(f"  {icon} {a.category:8s} | {a.name:30s} | {size:>10s} | {a.path}")
    elif args.colors:
        check = brand.validate_primary_color()
        primary = brand.tokens.get("colors", {}).get("primary", "#B85A3C")
        print(f"Primary Color: {primary}")
        for surface, present in check.items():
            icon = "[OK]" if present else "[!!]"
            print(f"  {icon} {surface}")
    else:
        brand.print_status()
