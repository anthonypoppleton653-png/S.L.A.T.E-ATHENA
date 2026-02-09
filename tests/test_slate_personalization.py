# Modified: 2026-02-09T12:00:00Z | Author: COPILOT | Change: Add test coverage for slate_personalization module
"""
Tests for slate/slate_personalization.py — User personalization
"""

import pytest
import json
from unittest.mock import MagicMock, patch
from pathlib import Path

try:
    from slate.slate_personalization import COLOR_PALETTES
    MODULE_AVAILABLE = True
except ImportError as e:
    MODULE_AVAILABLE = False
    pytest.skip(f"slate_personalization not importable: {e}", allow_module_level=True)


class TestColorPalettes:
    """Test predefined color palettes."""

    def test_palettes_is_dict(self):
        assert isinstance(COLOR_PALETTES, dict)

    def test_has_midnight_palette(self):
        assert "midnight" in COLOR_PALETTES

    def test_has_aurora_palette(self):
        assert "aurora" in COLOR_PALETTES

    def test_has_ember_palette(self):
        assert "ember" in COLOR_PALETTES

    def test_has_ocean_palette(self):
        assert "ocean" in COLOR_PALETTES

    def test_has_forest_palette(self):
        assert "forest" in COLOR_PALETTES

    def test_palette_has_required_keys(self):
        required_keys = [
            "name", "description", "primary", "secondary",
            "accent", "text", "success", "warning", "error"
        ]
        for palette_name, palette in COLOR_PALETTES.items():
            for key in required_keys:
                assert key in palette, f"{palette_name} missing key: {key}"

    def test_palette_colors_are_strings(self):
        for palette_name, palette in COLOR_PALETTES.items():
            assert isinstance(palette["primary"], str)
            assert isinstance(palette["accent"], str)

    def test_palette_name_matches_key(self):
        """Each palette's name field should match its dict key (capitalized)."""
        for key, palette in COLOR_PALETTES.items():
            assert palette["name"].lower() == key.lower()


class TestPersonalizationConstants:
    """Test module constants."""

    def test_workspace_root(self):
        from slate.slate_personalization import WORKSPACE_ROOT
        assert isinstance(WORKSPACE_ROOT, Path)
