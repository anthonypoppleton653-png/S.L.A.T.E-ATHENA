#!/usr/bin/env python3
# Modified: 2026-02-09T22:00:00Z | Author: COPILOT | Change: Create morph_manager.py (T-025-017)
"""
SLATE Morph Manager
===================

Manages SLATE Morph identity — the customization layer that transforms
a SLATE fork into a branded, purpose-built project while retaining
the SLATE core engine underneath.

Features:
  - morph.yaml read/write/validate
  - Custom branding application (colors → design tokens → CSS/theme)
  - README generation (AI-powered via Ollama)
  - GitHub Pages setup for morph landing page
  - Fork creation with morph identity overlay
  - Brand propagation to all outputs (dashboard, CLI, VSCode theme)

Usage:
  python slate/morph_manager.py --status          # Show current morph config
  python slate/morph_manager.py --init             # Interactive morph initialization
  python slate/morph_manager.py --validate         # Validate morph.yaml schema
  python slate/morph_manager.py --apply-brand      # Apply brand to all outputs
  python slate/morph_manager.py --generate-readme   # AI-generated README
  python slate/morph_manager.py --setup-pages       # Configure GitHub Pages
  python slate/morph_manager.py --json             # JSON output (machine readable)
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ─── Paths ──────────────────────────────────────────────────────────────────
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
MORPH_CONFIG = WORKSPACE_ROOT / ".slate_config" / "morph.yaml"
IDENTITY_DIR = WORKSPACE_ROOT / ".slate_identity"
DESIGN_TOKENS_JSON = WORKSPACE_ROOT / "design-tokens.json"
DESIGN_TOKENS_PY = WORKSPACE_ROOT / "slate" / "design_tokens.py"
GENERATED_DIR = WORKSPACE_ROOT / "slate_web" / "generated"


# ─── Schema Defaults ────────────────────────────────────────────────────────
DEFAULT_MORPH = {
    "morph": {
        "name": "S.L.A.T.E.",
        "description": "Synchronized Living Architecture for Transformation and Evolution",
        "version": "3.0.0",
        "upstream": "SynchronizedLivingArchitecture/S.L.A.T.E",
        "created": datetime.now().strftime("%Y-%m-%d"),
        "author": "",
        "license": "MIT",
        "brand": {
            "primary_color": "#B87333",
            "secondary_color": "#3B82F6",
            "surface_color": "#0C0C0C",
            "accent_color": "#10B981",
            "logo_path": "",
            "favicon_path": "",
            "project_title": "S.L.A.T.E.",
            "tagline": "Local-First AI Agent Orchestration",
        },
        "systems": {
            "core": True,
            "dashboard": True,
            "ollama": True,
            "gpu_compute": True,
            "github_runner": False,
            "docker": False,
            "kubernetes": False,
            "chromadb": True,
            "spec_kit": True,
            "avatar_3d": False,
            "energy_scheduler": True,
            "morph_sdk": False,
        },
        "protected_paths": [
            "README.md",
            ".slate_config/morph.yaml",
            ".slate_identity/",
            "docs/pages/index.html",
        ],
        "sync": {
            "auto": False,
            "frequency": "weekly",
            "strategy": "preserve_morph",
            "notify_on_conflict": True,
        },
        "contract": {
            "accepted": False,
            "accepted_at": "",
            "distribution": {
                "slate_foundation_pct": 5,
                "upstream_contributors_pct": 10,
                "morph_owner_pct": 85,
            },
        },
    }
}

# Valid hex color pattern
HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")

# Valid sync strategies
VALID_STRATEGIES = {"preserve_morph", "prefer_upstream", "manual_merge"}

# Valid sync frequencies
VALID_FREQUENCIES = {"daily", "weekly", "manual"}

# Required system keys
REQUIRED_SYSTEMS = {"core", "dashboard", "ollama"}


# ─── Data Classes ────────────────────────────────────────────────────────────

@dataclass
class MorphBrand:
    """Brand configuration extracted from morph.yaml."""
    primary_color: str = "#B87333"
    secondary_color: str = "#3B82F6"
    surface_color: str = "#0C0C0C"
    accent_color: str = "#10B981"
    logo_path: str = ""
    favicon_path: str = ""
    project_title: str = "S.L.A.T.E."
    tagline: str = "Local-First AI Agent Orchestration"


@dataclass
class MorphIdentity:
    """Full morph identity parsed from morph.yaml."""
    name: str = "S.L.A.T.E."
    description: str = ""
    version: str = "3.0.0"
    upstream: str = "SynchronizedLivingArchitecture/S.L.A.T.E"
    created: str = ""
    author: str = ""
    license: str = "MIT"
    brand: MorphBrand = field(default_factory=MorphBrand)
    systems: Dict[str, bool] = field(default_factory=dict)
    protected_paths: List[str] = field(default_factory=list)
    sync_strategy: str = "preserve_morph"
    sync_frequency: str = "weekly"
    sync_auto: bool = False
    contract_accepted: bool = False


@dataclass
class ValidationResult:
    """Result of morph.yaml validation."""
    valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# ─── YAML Helpers (no PyYAML dependency) ─────────────────────────────────────

def _load_yaml_simple(path: Path) -> Dict[str, Any]:
    """
    Load a morph.yaml with a lightweight parser.
    Falls back to PyYAML if available, otherwise uses regex-based parser.
    """
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")

    # Try PyYAML first
    try:
        import yaml
        return yaml.safe_load(text) or {}
    except ImportError:
        pass

    # Fallback: simple YAML parser for morph.yaml format
    return _parse_yaml_fallback(text)


def _parse_yaml_fallback(text: str) -> Dict[str, Any]:
    """Simple YAML parser for the morph.yaml structure. Handles nested dicts, lists, scalars."""
    result: Dict[str, Any] = {}
    stack: list = [(result, -1)]  # (current_dict, indent_level)

    for line in text.splitlines():
        # Skip comments and blank lines
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(line) - len(stripped)

        # Pop stack to find parent at correct indent
        while len(stack) > 1 and stack[-1][1] >= indent:
            stack.pop()

        current = stack[-1][0]

        # List item
        if stripped.startswith("- "):
            val = stripped[2:].strip().strip('"').strip("'")
            if isinstance(current, list):
                current.append(val)
            continue

        # Key-value
        if ":" in stripped:
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.split("#")[0].strip()  # Remove inline comments

            if not val:
                # Nested dict or list — peek next line
                # For simplicity, assume dict
                child: Any = {}
                if isinstance(current, dict):
                    current[key] = child
                stack.append((child, indent))
            else:
                # Scalar value
                val = val.strip('"').strip("'")
                # Type coercion
                if val.lower() == "true":
                    val = True
                elif val.lower() == "false":
                    val = False
                elif val.isdigit():
                    val = int(val)
                elif re.match(r"^\d+\.\d+$", val):
                    val = float(val)

                if isinstance(current, dict):
                    current[key] = val

    return result


def _dump_yaml_simple(data: Dict[str, Any], path: Path, header: str = "") -> None:
    """Write morph.yaml with proper formatting."""
    try:
        import yaml

        class MorphDumper(yaml.SafeDumper):
            pass

        def _str_representer(dumper, data):
            if "\n" in data:
                return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
            return dumper.represent_scalar("tag:yaml.org,2002:str", data)

        MorphDumper.add_representer(str, _str_representer)

        content = header + yaml.dump(data, Dumper=MorphDumper, default_flow_style=False,
                                     sort_keys=False, allow_unicode=True)
    except ImportError:
        # Fallback: manual YAML writer
        content = header + _serialize_yaml_fallback(data)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _serialize_yaml_fallback(data: Any, indent: int = 0) -> str:
    """Serialize dict/list/scalar to YAML string."""
    lines = []
    prefix = "  " * indent

    if isinstance(data, dict):
        for key, val in data.items():
            if isinstance(val, dict):
                lines.append(f"{prefix}{key}:")
                lines.append(_serialize_yaml_fallback(val, indent + 1))
            elif isinstance(val, list):
                lines.append(f"{prefix}{key}:")
                for item in val:
                    lines.append(f"{prefix}  - \"{item}\"" if isinstance(item, str) else f"{prefix}  - {item}")
            elif isinstance(val, bool):
                lines.append(f"{prefix}{key}: {'true' if val else 'false'}")
            elif isinstance(val, str):
                lines.append(f'{prefix}{key}: "{val}"')
            else:
                lines.append(f"{prefix}{key}: {val}")
    return "\n".join(lines)


# ─── Morph Manager ───────────────────────────────────────────────────────────

class MorphManager:
    """
    Manages the SLATE Morph identity layer.

    Reads/writes .slate_config/morph.yaml, applies branding
    to design tokens and dashboard, and manages fork identity.
    """

    def __init__(self, workspace: Path = WORKSPACE_ROOT):
        self.workspace = workspace
        self.config_path = workspace / ".slate_config" / "morph.yaml"
        self.identity_dir = workspace / ".slate_identity"
        self._config: Optional[Dict[str, Any]] = None

    # ── Config I/O ──────────────────────────────────────────────────────

    def load_config(self) -> Dict[str, Any]:
        """Load morph.yaml, return morph dict."""
        if self._config is not None:
            return self._config
        raw = _load_yaml_simple(self.config_path)
        self._config = raw.get("morph", raw)
        return self._config

    def save_config(self, config: Dict[str, Any]) -> None:
        """Save morph config back to morph.yaml."""
        header = (
            "# SLATE Morph Configuration\n"
            f"# Modified: {datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')} | Author: COPILOT | Change: Updated via morph_manager\n"
            "# NOTE: All AIs modifying this file must add a dated comment.\n"
            "# ──────────────────────────────────────────────────────────\n\n"
        )
        _dump_yaml_simple({"morph": config}, self.config_path, header)
        self._config = config

    def config_exists(self) -> bool:
        """Check if morph.yaml exists."""
        return self.config_path.exists()

    # ── Identity ────────────────────────────────────────────────────────

    def get_identity(self) -> MorphIdentity:
        """Parse morph.yaml into a MorphIdentity dataclass."""
        cfg = self.load_config()
        brand_data = cfg.get("brand", {})
        brand = MorphBrand(
            primary_color=brand_data.get("primary_color", "#B87333"),
            secondary_color=brand_data.get("secondary_color", "#3B82F6"),
            surface_color=brand_data.get("surface_color", "#0C0C0C"),
            accent_color=brand_data.get("accent_color", "#10B981"),
            logo_path=brand_data.get("logo_path", ""),
            favicon_path=brand_data.get("favicon_path", ""),
            project_title=brand_data.get("project_title", "S.L.A.T.E."),
            tagline=brand_data.get("tagline", ""),
        )
        sync = cfg.get("sync", {})
        contract = cfg.get("contract", {})

        return MorphIdentity(
            name=cfg.get("name", "S.L.A.T.E."),
            description=cfg.get("description", ""),
            version=cfg.get("version", "3.0.0"),
            upstream=cfg.get("upstream", ""),
            created=cfg.get("created", ""),
            author=cfg.get("author", ""),
            license=cfg.get("license", "MIT"),
            brand=brand,
            systems=cfg.get("systems", {}),
            protected_paths=cfg.get("protected_paths", []),
            sync_strategy=sync.get("strategy", "preserve_morph"),
            sync_frequency=sync.get("frequency", "weekly"),
            sync_auto=sync.get("auto", False),
            contract_accepted=contract.get("accepted", False),
        )

    def is_default_morph(self) -> bool:
        """Check if this is an unmodified default SLATE (no custom morph)."""
        if not self.config_exists():
            return True
        identity = self.get_identity()
        return identity.name == "S.L.A.T.E." and not identity.author

    # ── Validation ──────────────────────────────────────────────────────

    def validate(self) -> ValidationResult:
        """Validate morph.yaml against the expected schema."""
        result = ValidationResult()

        if not self.config_exists():
            result.valid = False
            result.errors.append("morph.yaml not found at .slate_config/morph.yaml")
            return result

        try:
            cfg = self.load_config()
        except Exception as e:
            result.valid = False
            result.errors.append(f"Failed to parse morph.yaml: {e}")
            return result

        # Required fields
        for key in ("name", "version", "upstream"):
            if not cfg.get(key):
                result.errors.append(f"Missing required field: morph.{key}")
                result.valid = False

        # Brand validation
        brand = cfg.get("brand", {})
        for color_key in ("primary_color", "secondary_color", "surface_color", "accent_color"):
            color = brand.get(color_key, "")
            if color and not HEX_COLOR_RE.match(color):
                result.errors.append(f"Invalid hex color for brand.{color_key}: '{color}'")
                result.valid = False

        # Logo path validation
        logo = brand.get("logo_path", "")
        if logo:
            logo_abs = self.workspace / logo
            if not logo_abs.exists():
                result.warnings.append(f"Logo file not found: {logo}")

        # Systems validation
        systems = cfg.get("systems", {})
        if not systems.get("core", True):
            result.errors.append("systems.core must be true — SLATE core cannot be disabled")
            result.valid = False

        # Sync validation
        sync = cfg.get("sync", {})
        strategy = sync.get("strategy", "preserve_morph")
        if strategy not in VALID_STRATEGIES:
            result.errors.append(f"Invalid sync.strategy: '{strategy}' — must be one of {VALID_STRATEGIES}")
            result.valid = False

        frequency = sync.get("frequency", "weekly")
        if frequency not in VALID_FREQUENCIES:
            result.errors.append(f"Invalid sync.frequency: '{frequency}' — must be one of {VALID_FREQUENCIES}")
            result.valid = False

        # Contract distribution
        contract = cfg.get("contract", {})
        dist = contract.get("distribution", {})
        if dist:
            total = sum(v for v in dist.values() if isinstance(v, (int, float)))
            if total != 100:
                result.warnings.append(
                    f"Contract distribution sums to {total}%, expected 100%"
                )

        # Protected paths should include morph.yaml
        protected = cfg.get("protected_paths", [])
        if ".slate_config/morph.yaml" not in protected:
            result.warnings.append(
                "morph.yaml is not in protected_paths — it may be overwritten by upstream sync"
            )

        return result

    # ── Brand Application ───────────────────────────────────────────────

    def apply_brand(self) -> Dict[str, bool]:
        """
        Apply morph brand colors to design tokens and propagate.

        Flow:
          1. Read morph.yaml brand section
          2. Patch design-tokens.json with morph colors
          3. Run TokenPropagator to regenerate CSS, theme, etc.
          4. Update dashboard title/tagline
        """
        identity = self.get_identity()
        results: Dict[str, bool] = {}

        # Step 1: Patch design-tokens.json
        results["design-tokens.json"] = self._patch_design_tokens(identity.brand)

        # Step 2: Propagate tokens to CSS, VSCode theme, etc.
        results["token_propagation"] = self._run_token_propagation()

        # Step 3: Update identity directory
        results["identity_dir"] = self._ensure_identity_dir(identity)

        return results

    def _patch_design_tokens(self, brand: MorphBrand) -> bool:
        """Patch design-tokens.json with morph brand colors."""
        if not DESIGN_TOKENS_JSON.exists():
            print("  ⚠ design-tokens.json not found — skipping brand patch")
            return False

        try:
            tokens = json.loads(DESIGN_TOKENS_JSON.read_text(encoding="utf-8"))

            # Patch color tokens
            colors = tokens.get("colors", {})
            if brand.primary_color:
                colors["primary"] = brand.primary_color
                # Generate light/dark variants
                colors["primary_light"] = self._lighten_hex(brand.primary_color, 0.2)
                colors["primary_dark"] = self._darken_hex(brand.primary_color, 0.2)
            if brand.secondary_color:
                colors["secondary"] = brand.secondary_color
                colors["secondary_light"] = self._lighten_hex(brand.secondary_color, 0.15)
                colors["secondary_dark"] = self._darken_hex(brand.secondary_color, 0.15)
            if brand.surface_color:
                colors["surface"] = brand.surface_color
            if brand.accent_color:
                colors["accent"] = brand.accent_color

            tokens["colors"] = colors

            # Patch metadata
            meta = tokens.get("metadata", {})
            meta["morph_name"] = brand.project_title
            meta["morph_tagline"] = brand.tagline
            tokens["metadata"] = meta

            DESIGN_TOKENS_JSON.write_text(
                json.dumps(tokens, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            print(f"  ✓ Patched design-tokens.json with morph brand")
            return True
        except Exception as e:
            print(f"  ✗ Failed to patch design-tokens.json: {e}")
            return False

    def _run_token_propagation(self) -> bool:
        """Run the token propagator to regenerate all outputs."""
        propagator_script = WORKSPACE_ROOT / "slate" / "token_propagator.py"
        if not propagator_script.exists():
            print("  ⚠ token_propagator.py not found — skipping propagation")
            return False

        try:
            # Try importing directly
            sys.path.insert(0, str(WORKSPACE_ROOT))
            from slate.token_propagator import TokenPropagator
            propagator = TokenPropagator()
            results = propagator.propagate()
            return all(results.values()) if results else False
        except Exception as e:
            # Fallback: run as subprocess
            py = _get_python_exe()
            result = subprocess.run(
                [str(py), str(propagator_script)],
                capture_output=True, text=True, timeout=30,
                cwd=str(WORKSPACE_ROOT)
            )
            return result.returncode == 0

    def _ensure_identity_dir(self, identity: MorphIdentity) -> bool:
        """Create .slate_identity/ with brand assets."""
        try:
            self.identity_dir.mkdir(parents=True, exist_ok=True)

            # Write identity metadata
            meta_file = self.identity_dir / "identity.json"
            meta = {
                "name": identity.name,
                "description": identity.description,
                "version": identity.version,
                "author": identity.author,
                "brand": asdict(identity.brand),
                "generated_at": datetime.now().isoformat(),
            }
            meta_file.write_text(json.dumps(meta, indent=2), encoding="utf-8")

            # Generate brand CSS variables
            css_file = self.identity_dir / "brand.css"
            css = self._generate_brand_css(identity.brand)
            css_file.write_text(css, encoding="utf-8")

            print(f"  ✓ Identity directory updated: .slate_identity/")
            return True
        except Exception as e:
            print(f"  ✗ Failed to create identity dir: {e}")
            return False

    def _generate_brand_css(self, brand: MorphBrand) -> str:
        """Generate CSS custom properties from morph brand."""
        return f"""/* SLATE Morph Brand — Auto-generated by morph_manager.py */
/* Modified: {datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')} | Author: COPILOT */
:root {{
  --morph-primary: {brand.primary_color};
  --morph-primary-light: {self._lighten_hex(brand.primary_color, 0.2)};
  --morph-primary-dark: {self._darken_hex(brand.primary_color, 0.2)};
  --morph-secondary: {brand.secondary_color};
  --morph-secondary-light: {self._lighten_hex(brand.secondary_color, 0.15)};
  --morph-secondary-dark: {self._darken_hex(brand.secondary_color, 0.15)};
  --morph-surface: {brand.surface_color};
  --morph-accent: {brand.accent_color};
  --morph-title: "{brand.project_title}";
  --morph-tagline: "{brand.tagline}";
}}
"""

    # ── README Generation ───────────────────────────────────────────────

    def generate_readme(self, use_ai: bool = True) -> bool:
        """
        Generate a README.md for this morph.

        If use_ai is True and Ollama is available, uses slate-fast
        to generate a compelling project description.
        """
        identity = self.get_identity()
        readme_path = self.workspace / "README.md"

        # Try AI generation first
        ai_description = ""
        if use_ai:
            ai_description = self._generate_ai_description(identity)

        description = ai_description or identity.description

        # Active systems list
        active = [k for k, v in identity.systems.items() if v]
        systems_md = "\n".join(f"  - **{s.replace('_', ' ').title()}**" for s in active)

        readme = f"""# {identity.brand.project_title}

> {identity.brand.tagline}

{description}

## Built with [S.L.A.T.E.](https://github.com/{identity.upstream})

**{identity.name}** is a SLATE Morph — a customized fork of the Synchronized Living
Architecture for Transformation and Evolution framework.

### Active Systems

{systems_md}

### Quick Start

```bash
# Clone and install
git clone <your-fork-url>
cd {identity.name.lower().replace(' ', '-').replace('.', '')}
python install_slate.py

# Check status
python slate/slate_status.py --quick
```

### Configuration

- **Morph Config**: `.slate_config/morph.yaml`
- **Permissions**: `.slate_config/permissions.yaml`
- **Energy**: `.slate_config/energy.yaml`
- **Thermal**: `.slate_config/thermal.yaml`

### License

{identity.license}

---

*Built with S.L.A.T.E. v3.0.0 — Local-First AI Agent Orchestration*
"""

        try:
            readme_path.write_text(readme, encoding="utf-8")
            print(f"  ✓ Generated README.md ({len(readme)} bytes)")
            return True
        except Exception as e:
            print(f"  ✗ Failed to write README.md: {e}")
            return False

    def _generate_ai_description(self, identity: MorphIdentity) -> str:
        """Use Ollama slate-fast to generate a project description."""
        try:
            import urllib.request

            prompt = (
                f"Write a 2-3 sentence project description for a software project called "
                f"'{identity.name}'. It is described as: '{identity.description}'. "
                f"It is an AI-powered application built on the SLATE framework. "
                f"Keep it professional, concise, and compelling. No markdown. No quotes."
            )

            payload = json.dumps({
                "model": "slate-fast",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.7, "num_predict": 150},
            }).encode("utf-8")

            req = urllib.request.Request(
                "http://127.0.0.1:11434/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("response", "").strip()
        except Exception:
            return ""

    # ── GitHub Pages ────────────────────────────────────────────────────

    def setup_github_pages(self) -> bool:
        """
        Configure GitHub Pages for the morph's landing page.

        Creates docs/pages/index.html with morph branding if it doesn't exist.
        """
        identity = self.get_identity()
        pages_dir = self.workspace / "docs" / "pages"
        index_path = pages_dir / "index.html"

        # Don't overwrite existing custom page
        if index_path.exists():
            print("  ℹ docs/pages/index.html already exists — skipping")
            return True

        pages_dir.mkdir(parents=True, exist_ok=True)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{identity.brand.project_title}</title>
    <style>
        :root {{
            --primary: {identity.brand.primary_color};
            --secondary: {identity.brand.secondary_color};
            --surface: {identity.brand.surface_color};
            --accent: {identity.brand.accent_color};
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--surface);
            color: #e0e0e0;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }}
        .hero {{
            text-align: center;
            padding: 4rem 2rem;
            max-width: 800px;
        }}
        h1 {{
            font-size: 3.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 1rem;
        }}
        .tagline {{
            font-size: 1.25rem;
            color: rgba(255,255,255,0.6);
            margin-bottom: 2rem;
        }}
        .badge {{
            display: inline-block;
            padding: 0.5rem 1.5rem;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 2rem;
            font-size: 0.875rem;
            color: var(--accent);
        }}
        .cta {{
            margin-top: 2rem;
            display: inline-block;
            padding: 0.75rem 2rem;
            background: var(--primary);
            color: #000;
            text-decoration: none;
            border-radius: 0.5rem;
            font-weight: 600;
            transition: transform 0.2s;
        }}
        .cta:hover {{ transform: translateY(-2px); }}
    </style>
</head>
<body>
    <div class="hero">
        <h1>{identity.brand.project_title}</h1>
        <p class="tagline">{identity.brand.tagline}</p>
        <span class="badge">Built with S.L.A.T.E. v3.0.0</span>
        <br>
        <a href="https://github.com/{identity.upstream}" class="cta">
            View on GitHub
        </a>
    </div>
</body>
</html>
"""
        try:
            index_path.write_text(html, encoding="utf-8")
            print(f"  ✓ Created docs/pages/index.html with morph branding")
            return True
        except Exception as e:
            print(f"  ✗ Failed to create GitHub Pages: {e}")
            return False

    # ── Interactive Init ────────────────────────────────────────────────

    def init_interactive(self) -> bool:
        """Interactive morph initialization — prompts user for identity."""

        print("\n╔══════════════════════════════════════════════════════════╗")
        print("║          S.L.A.T.E. MORPH INITIALIZATION                ║")
        print("║    Transform Your Fork Into a Branded Project            ║")
        print("╚══════════════════════════════════════════════════════════╝\n")

        cfg = dict(DEFAULT_MORPH["morph"])

        # Project identity
        name = input("  Project name [S.L.A.T.E.]: ").strip()
        if name:
            cfg["name"] = name
            cfg["brand"] = dict(cfg["brand"])
            cfg["brand"]["project_title"] = name

        desc = input("  Description: ").strip()
        if desc:
            cfg["description"] = desc

        author = input("  Author/Organization: ").strip()
        if author:
            cfg["author"] = author

        # Brand colors
        print("\n  ── Brand Colors (hex format, e.g. #3B82F6) ──")
        primary = input(f"  Primary color [{cfg['brand']['primary_color']}]: ").strip()
        if primary and HEX_COLOR_RE.match(primary):
            cfg["brand"]["primary_color"] = primary

        secondary = input(f"  Secondary color [{cfg['brand']['secondary_color']}]: ").strip()
        if secondary and HEX_COLOR_RE.match(secondary):
            cfg["brand"]["secondary_color"] = secondary

        tagline = input(f"  Tagline [{cfg['brand']['tagline']}]: ").strip()
        if tagline:
            cfg["brand"]["tagline"] = tagline

        # Systems
        print("\n  ── Active Systems (y/n) ──")
        systems = dict(cfg.get("systems", DEFAULT_MORPH["morph"]["systems"]))
        optional_systems = [k for k in systems if k != "core"]
        for sys_name in optional_systems:
            default = "y" if systems[sys_name] else "n"
            choice = input(f"  {sys_name.replace('_', ' ').title()} [{default}]: ").strip().lower()
            if choice in ("y", "yes"):
                systems[sys_name] = True
            elif choice in ("n", "no"):
                systems[sys_name] = False
        cfg["systems"] = systems

        # Sync strategy
        print("\n  ── Upstream Sync ──")
        print("  1. preserve_morph  — Keep your identity, merge safe core updates")
        print("  2. prefer_upstream — Accept upstream, re-apply morph after")
        print("  3. manual_merge    — Always prompt for conflict resolution")
        strat_choice = input("  Strategy [1]: ").strip()
        strat_map = {"1": "preserve_morph", "2": "prefer_upstream", "3": "manual_merge"}
        cfg["sync"] = dict(cfg.get("sync", DEFAULT_MORPH["morph"]["sync"]))
        cfg["sync"]["strategy"] = strat_map.get(strat_choice, "preserve_morph")

        freq = input("  Sync frequency (daily/weekly/manual) [weekly]: ").strip().lower()
        if freq in VALID_FREQUENCIES:
            cfg["sync"]["frequency"] = freq

        cfg["created"] = datetime.now().strftime("%Y-%m-%d")

        # Save
        self.save_config(cfg)
        print(f"\n  ✓ Morph config saved to .slate_config/morph.yaml")

        # Apply brand
        print("\n  Applying brand...")
        self.apply_brand()

        return True

    # ── Status ──────────────────────────────────────────────────────────

    def status(self, as_json: bool = False) -> Dict[str, Any]:
        """Report current morph status."""
        if not self.config_exists():
            info = {
                "configured": False,
                "message": "No morph.yaml found — run 'python slate/morph_manager.py --init'",
            }
            if as_json:
                return info
            print("\n  ℹ No morph configuration found.")
            print("    Run: python slate/morph_manager.py --init")
            return info

        identity = self.get_identity()
        validation = self.validate()
        active_systems = [k for k, v in identity.systems.items() if v]

        info = {
            "configured": True,
            "valid": validation.valid,
            "name": identity.name,
            "version": identity.version,
            "author": identity.author or "(not set)",
            "description": identity.description,
            "is_default": self.is_default_morph(),
            "brand": {
                "primary": identity.brand.primary_color,
                "secondary": identity.brand.secondary_color,
                "surface": identity.brand.surface_color,
                "accent": identity.brand.accent_color,
                "title": identity.brand.project_title,
                "tagline": identity.brand.tagline,
            },
            "active_systems": active_systems,
            "system_count": f"{len(active_systems)}/{len(identity.systems)}",
            "sync": {
                "strategy": identity.sync_strategy,
                "frequency": identity.sync_frequency,
                "auto": identity.sync_auto,
            },
            "contract_accepted": identity.contract_accepted,
            "protected_paths": identity.protected_paths,
            "validation_errors": validation.errors,
            "validation_warnings": validation.warnings,
        }

        if as_json:
            return info

        # Pretty print
        is_custom = "Custom Morph" if not info["is_default"] else "Default SLATE"
        valid_icon = "✓" if validation.valid else "✗"

        print(f"\n  ╔══ MORPH STATUS {'═' * 40}")
        print(f"  ║ Name:        {identity.name}")
        print(f"  ║ Version:     {identity.version}")
        print(f"  ║ Author:      {identity.author or '(not set)'}")
        print(f"  ║ Type:        {is_custom}")
        print(f"  ║ Valid:       {valid_icon} {'Yes' if validation.valid else 'No'}")
        print(f"  ╠══ BRAND {'═' * 46}")
        print(f"  ║ Title:       {identity.brand.project_title}")
        print(f"  ║ Tagline:     {identity.brand.tagline}")
        print(f"  ║ Primary:     {identity.brand.primary_color}")
        print(f"  ║ Secondary:   {identity.brand.secondary_color}")
        print(f"  ║ Surface:     {identity.brand.surface_color}")
        print(f"  ║ Accent:      {identity.brand.accent_color}")
        print(f"  ╠══ SYSTEMS ({info['system_count']}) {'═' * (38 - len(info['system_count']))}")
        for s in active_systems:
            print(f"  ║ ✓ {s.replace('_', ' ').title()}")
        print(f"  ╠══ SYNC {'═' * 47}")
        print(f"  ║ Strategy:    {identity.sync_strategy}")
        print(f"  ║ Frequency:   {identity.sync_frequency}")
        print(f"  ║ Auto:        {'Yes' if identity.sync_auto else 'No'}")
        print(f"  ╠══ CONTRACT {'═' * 44}")
        print(f"  ║ Accepted:    {'Yes' if identity.contract_accepted else 'No'}")
        if identity.contract_accepted:
            dist = self.load_config().get("contract", {}).get("distribution", {})
            print(f"  ║ Foundation:  {dist.get('slate_foundation_pct', 5)}%")
            print(f"  ║ Contributors:{dist.get('upstream_contributors_pct', 10)}%")
            print(f"  ║ Owner:       {dist.get('morph_owner_pct', 85)}%")

        if validation.errors:
            print(f"  ╠══ ERRORS {'═' * 45}")
            for err in validation.errors:
                print(f"  ║ ✗ {err}")
        if validation.warnings:
            print(f"  ╠══ WARNINGS {'═' * 43}")
            for warn in validation.warnings:
                print(f"  ║ ⚠ {warn}")

        print(f"  ╚{'═' * 56}")

        return info

    # ── Color Utilities ─────────────────────────────────────────────────

    @staticmethod
    def _lighten_hex(hex_color: str, factor: float = 0.2) -> str:
        """Lighten a hex color by factor (0.0 = no change, 1.0 = white)."""
        try:
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            r = min(255, int(r + (255 - r) * factor))
            g = min(255, int(g + (255 - g) * factor))
            b = min(255, int(b + (255 - b) * factor))
            return f"#{r:02X}{g:02X}{b:02X}"
        except (ValueError, IndexError):
            return hex_color

    @staticmethod
    def _darken_hex(hex_color: str, factor: float = 0.2) -> str:
        """Darken a hex color by factor (0.0 = no change, 1.0 = black)."""
        try:
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            r = max(0, int(r * (1 - factor)))
            g = max(0, int(g * (1 - factor)))
            b = max(0, int(b * (1 - factor)))
            return f"#{r:02X}{g:02X}{b:02X}"
        except (ValueError, IndexError):
            return hex_color


# ─── Utilities ───────────────────────────────────────────────────────────────

def _get_python_exe() -> Path:
    """Get the SLATE venv Python executable."""
    venv_py = WORKSPACE_ROOT / ".venv" / "Scripts" / "python.exe"
    if venv_py.exists():
        return venv_py
    venv_py = WORKSPACE_ROOT / ".venv" / "bin" / "python"
    if venv_py.exists():
        return venv_py
    return Path(sys.executable)


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="SLATE Morph Manager — Manage project identity and branding"
    )
    parser.add_argument("--status", action="store_true", help="Show morph status")
    parser.add_argument("--init", action="store_true", help="Interactive morph initialization")
    parser.add_argument("--validate", action="store_true", help="Validate morph.yaml")
    parser.add_argument("--apply-brand", action="store_true", help="Apply brand to all outputs")
    parser.add_argument("--generate-readme", action="store_true", help="Generate README.md")
    parser.add_argument("--setup-pages", action="store_true", help="Setup GitHub Pages")
    parser.add_argument("--json", action="store_true", help="JSON output")

    args = parser.parse_args()
    mgr = MorphManager()

    if args.init:
        mgr.init_interactive()
    elif args.validate:
        result = mgr.validate()
        if args.json:
            print(json.dumps({"valid": result.valid, "errors": result.errors,
                              "warnings": result.warnings}, indent=2))
        else:
            icon = "✓" if result.valid else "✗"
            print(f"\n  {icon} morph.yaml validation: {'PASS' if result.valid else 'FAIL'}")
            for e in result.errors:
                print(f"    ✗ {e}")
            for w in result.warnings:
                print(f"    ⚠ {w}")
    elif args.apply_brand:
        results = mgr.apply_brand()
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            ok = all(results.values())
            print(f"\n  {'✓' if ok else '⚠'} Brand application {'complete' if ok else 'partial'}")
    elif args.generate_readme:
        mgr.generate_readme()
    elif args.setup_pages:
        mgr.setup_github_pages()
    else:
        info = mgr.status(as_json=args.json)
        if args.json:
            print(json.dumps(info, indent=2))


if __name__ == "__main__":
    main()
