#!/usr/bin/env python3
# Modified: 2026-02-09T06:00:00Z | Author: COPILOT | Change: Create tests for schematic API and Phase 2 widgets
"""
Tests for SLATE Schematic API endpoints and dashboard widget integration.

Covers:
  - REST API endpoints (templates, system-state, widgets)
  - Widget CSS/JS generation
  - WebSocket manager
  - Dashboard template Phase 2 widgets (compact, card, modal, status overlay)
"""

import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure workspace root on path
WORKSPACE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))


# ── Schematic API Module Tests ────────────────────────────────────────────────

class TestSchematicAPIImports:
    """Test that schematic API module imports correctly."""

    def test_import_router(self):
        from slate.schematic_api import router
        assert router is not None

    def test_import_templates(self):
        from slate.schematic_api import TEMPLATES
        assert isinstance(TEMPLATES, dict)
        assert len(TEMPLATES) >= 1

    def test_import_ws_manager(self):
        from slate.schematic_api import ws_manager, SchematicWebSocketManager
        assert isinstance(ws_manager, SchematicWebSocketManager)

    def test_import_helper_functions(self):
        from slate.schematic_api import get_widget_css, get_widget_js
        assert callable(get_widget_css)
        assert callable(get_widget_js)


class TestSchematicTemplates:
    """Test template registry."""

    def test_system_template_exists(self):
        from slate.schematic_api import TEMPLATES
        assert "system" in TEMPLATES

    def test_inference_template_exists(self):
        from slate.schematic_api import TEMPLATES
        assert "inference" in TEMPLATES

    def test_cicd_template_exists(self):
        from slate.schematic_api import TEMPLATES
        assert "cicd" in TEMPLATES

    def test_template_has_name(self):
        from slate.schematic_api import TEMPLATES
        for tid, tmpl in TEMPLATES.items():
            assert "name" in tmpl, f"Template {tid} missing 'name'"

    def test_template_has_config(self):
        from slate.schematic_api import TEMPLATES
        for tid, tmpl in TEMPLATES.items():
            assert "config" in tmpl, f"Template {tid} missing 'config'"


class TestWidgetCSS:
    """Test widget CSS generation."""

    def test_css_not_empty(self):
        from slate.schematic_api import get_widget_css
        css = get_widget_css()
        assert len(css) > 0

    def test_css_has_widget_class(self):
        from slate.schematic_api import get_widget_css
        css = get_widget_css()
        assert ".schematic-widget" in css

    def test_css_has_header_class(self):
        from slate.schematic_api import get_widget_css
        css = get_widget_css()
        assert ".schematic-header" in css

    def test_css_has_content_class(self):
        from slate.schematic_api import get_widget_css
        css = get_widget_css()
        assert ".schematic-content" in css

    def test_css_has_status_class(self):
        from slate.schematic_api import get_widget_css
        css = get_widget_css()
        assert ".schematic-status" in css

    def test_css_has_compact_class(self):
        from slate.schematic_api import get_widget_css
        css = get_widget_css()
        assert ".schematic-compact" in css

    def test_css_has_pulse_animation(self):
        from slate.schematic_api import get_widget_css
        css = get_widget_css()
        assert "@keyframes pulse" in css


class TestWidgetJS:
    """Test widget JavaScript generation."""

    def test_js_not_empty(self):
        from slate.schematic_api import get_widget_js
        js = get_widget_js()
        assert len(js) > 0

    def test_js_has_schematic_widget_class(self):
        from slate.schematic_api import get_widget_js
        js = get_widget_js()
        assert "class SchematicWidget" in js

    def test_js_has_websocket_connection(self):
        from slate.schematic_api import get_widget_js
        js = get_widget_js()
        assert "WebSocket" in js

    def test_js_has_auto_reconnect(self):
        from slate.schematic_api import get_widget_js
        js = get_widget_js()
        assert "connectWebSocket" in js

    def test_js_has_update_schematic(self):
        from slate.schematic_api import get_widget_js
        js = get_widget_js()
        assert "updateSchematic" in js

    def test_js_connects_to_correct_endpoint(self):
        from slate.schematic_api import get_widget_js
        js = get_widget_js()
        assert "/api/schematic/ws/live" in js


class TestSVGGeneration:
    """Test SVG generation functions."""

    def test_generate_from_system_state(self):
        from slate.schematic_api import generate_from_system_state
        svg = generate_from_system_state()
        assert isinstance(svg, str)
        assert len(svg) > 0
        assert "<svg" in svg or "svg" in svg.lower()

    def test_build_from_template_system(self):
        from slate.schematic_api import build_from_template
        svg = build_from_template("system")
        assert isinstance(svg, str)
        assert len(svg) > 0

    def test_build_from_template_inference(self):
        from slate.schematic_api import build_from_template
        svg = build_from_template("inference")
        assert isinstance(svg, str)
        assert len(svg) > 0

    def test_build_from_template_cicd(self):
        from slate.schematic_api import build_from_template
        svg = build_from_template("cicd")
        assert isinstance(svg, str)
        assert len(svg) > 0


class TestWebSocketManager:
    """Test SchematicWebSocketManager."""

    def test_manager_init(self):
        from slate.schematic_api import SchematicWebSocketManager
        mgr = SchematicWebSocketManager()
        assert mgr.active_connections == []

    @pytest.mark.asyncio
    async def test_manager_disconnect_nonexistent(self):
        from slate.schematic_api import SchematicWebSocketManager
        mgr = SchematicWebSocketManager()
        mock_ws = MagicMock()
        # Should not raise
        mgr.disconnect(mock_ws)
        assert len(mgr.active_connections) == 0

    @pytest.mark.asyncio
    async def test_manager_broadcast_empty(self):
        from slate.schematic_api import SchematicWebSocketManager
        mgr = SchematicWebSocketManager()
        # Should not raise with no connections
        await mgr.broadcast({"type": "test"})


# ── Dashboard Template Phase 2 Tests ─────────────────────────────────────────

class TestDashboardTemplatePhase2:
    """Test Spec 012 Phase 2 widget integration in dashboard template."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Build full template (HTML + JS) for all tests."""
        from slate_web.dashboard_template import get_full_template
        self.template = get_full_template()

    # ─── Compact Sidebar Widget ───

    def test_compact_widget_html(self):
        assert 'id="sidebar-schematic"' in self.template

    def test_compact_widget_css(self):
        assert ".schematic-compact" in self.template

    def test_compact_widget_click_handler(self):
        assert "openSchematicModal" in self.template

    def test_compact_widget_label(self):
        assert "schematic-compact-label" in self.template

    def test_compact_widget_dot(self):
        assert "sc-dot" in self.template

    # ─── Card Schematic ───

    def test_card_schematic_gpu(self):
        assert 'id="gpu-topology-schematic"' in self.template

    def test_card_schematic_agents(self):
        assert 'id="agent-pipeline-schematic"' in self.template

    def test_card_schematic_css(self):
        assert ".card-schematic" in self.template

    def test_card_schematic_expand_button(self):
        assert "cs-expand" in self.template

    def test_card_schematic_hover_expand(self):
        assert ".card-schematic:hover .cs-expand" in self.template

    # ─── Modal Detail View ───

    def test_modal_overlay_html(self):
        assert 'id="schematic-modal"' in self.template

    def test_modal_has_aria(self):
        assert 'role="dialog"' in self.template
        assert 'aria-modal="true"' in self.template

    def test_modal_close_button(self):
        assert "closeSchematicModal" in self.template

    def test_modal_css(self):
        assert ".schematic-modal-overlay" in self.template
        assert ".schematic-modal" in self.template

    def test_modal_header(self):
        assert "schematic-modal-header" in self.template
        assert "schematic-modal-title" in self.template

    def test_modal_body(self):
        assert "schematic-modal-body" in self.template

    def test_modal_footer(self):
        assert "schematic-modal-footer" in self.template

    def test_modal_backdrop_filter(self):
        assert "backdrop-filter: blur" in self.template

    # ─── Status Overlay ───

    def test_status_overlay_html(self):
        assert "schematic-status-overlay" in self.template

    def test_status_chips(self):
        assert "schematic-status-chip" in self.template

    def test_status_dots(self):
        assert "ssc-dot" in self.template

    def test_status_dot_states(self):
        assert ".ssc-dot.active" in self.template
        assert ".ssc-dot.warning" in self.template
        assert ".ssc-dot.error" in self.template
        assert ".ssc-dot.idle" in self.template

    # ─── JavaScript ───

    def test_js_open_modal(self):
        assert "function openSchematicModal" in self.template

    def test_js_close_modal(self):
        assert "function closeSchematicModal" in self.template

    def test_js_escape_closes_modal(self):
        assert "Escape" in self.template

    def test_js_sidebar_updater(self):
        assert "updateSidebarSchematic" in self.template

    def test_js_status_overlay_updater(self):
        assert "updateSchematicStatusOverlay" in self.template

    def test_js_fetch_template(self):
        assert "/api/schematic/template/" in self.template

    def test_js_fetch_compact_widget(self):
        assert "/api/schematic/widget/compact" in self.template

    def test_js_fetch_system_state(self):
        assert "/api/schematic/system-state" in self.template

    # ─── Responsive ───

    def test_responsive_compact_mobile(self):
        assert ".schematic-compact" in self.template

    def test_responsive_modal_mobile(self):
        # Check mobile modal sizing
        assert "96vw" in self.template or "90vh" in self.template

    # ─── Integration ───

    def test_sidebar_schematic_updates_on_interval(self):
        assert "updateSidebarSchematic" in self.template
        assert "60000" in self.template  # 60s interval

    def test_status_overlay_updates_on_interval(self):
        assert "updateSchematicStatusOverlay" in self.template
        assert "15000" in self.template


class TestGetFullTemplate:
    """Test the full template builder."""

    def test_full_template_builds(self):
        from slate_web.dashboard_template import get_full_template
        html = get_full_template()
        assert isinstance(html, str)
        assert len(html) > 100000  # Should be quite large

    def test_full_template_has_schematic_elements(self):
        from slate_web.dashboard_template import get_full_template
        html = get_full_template()
        assert "schematic-hero" in html
        assert "schematic-modal" in html
        assert "sidebar-schematic" in html

    def test_full_template_is_valid_html(self):
        from slate_web.dashboard_template import get_full_template
        html = get_full_template()
        assert html.strip().startswith("<!DOCTYPE html>")
        assert "</html>" in html


class TestSchematicAPIRouter:
    """Test that the schematic API router has expected routes."""

    def test_router_has_routes(self):
        from slate.schematic_api import router
        routes = [r.path for r in router.routes]
        assert "/templates" in routes or any("/templates" in r for r in routes)

    def test_router_has_widget_endpoint(self):
        from slate.schematic_api import router
        routes = [r.path for r in router.routes]
        assert any("widget" in r for r in routes)

    def test_router_has_websocket(self):
        from slate.schematic_api import router
        routes = [r.path for r in router.routes]
        assert any("ws" in r for r in routes)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
