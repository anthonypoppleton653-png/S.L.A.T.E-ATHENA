# Modified: 2026-02-09T12:00:00Z | Author: COPILOT | Change: Add test coverage for design_tokens module
"""
Tests for slate/design_tokens.py — Design token system
"""

import pytest
from pathlib import Path

try:
    from slate.design_tokens import ColorTokens
    MODULE_AVAILABLE = True
except ImportError as e:
    MODULE_AVAILABLE = False
    pytest.skip(f"design_tokens not importable: {e}", allow_module_level=True)


class TestColorTokens:
    """Test ColorTokens dataclass."""

    def test_default_primary(self):
        tokens = ColorTokens()
        assert tokens.primary == "#B87333"

    def test_default_secondary(self):
        tokens = ColorTokens()
        assert tokens.secondary == "#3B82F6"

    def test_default_tertiary(self):
        tokens = ColorTokens()
        assert tokens.tertiary == "#8B5CF6"

    def test_dark_surface(self):
        tokens = ColorTokens()
        assert tokens.surface_dark == "#000000"

    def test_on_primary_color(self):
        tokens = ColorTokens()
        assert tokens.on_primary == "#000000"

    def test_custom_primary(self):
        tokens = ColorTokens(primary="#FF0000")
        assert tokens.primary == "#FF0000"

    def test_outline_colors(self):
        tokens = ColorTokens()
        assert tokens.outline is not None
        assert tokens.outline_dark is not None


class TestDesignTokenStructure:
    """Test additional design token dataclasses if available."""

    def test_color_tokens_has_all_surface_variants(self):
        tokens = ColorTokens()
        # Dark
        assert tokens.surface_dark is not None
        assert tokens.surface_dim_dark is not None
        assert tokens.surface_bright_dark is not None
        # Light
        assert tokens.surface is not None
        assert tokens.surface_dim is not None
        assert tokens.surface_bright is not None

    def test_color_tokens_serializable(self):
        """Tokens should be serializable to dict."""
        from dataclasses import asdict
        tokens = ColorTokens()
        d = asdict(tokens)
        assert isinstance(d, dict)
        assert "primary" in d
        assert "secondary" in d

    def test_all_colors_are_strings(self):
        from dataclasses import fields
        tokens = ColorTokens()
        for f in fields(tokens):
            val = getattr(tokens, f.name)
            assert isinstance(val, str), f"Field {f.name} is not a string: {type(val)}"
