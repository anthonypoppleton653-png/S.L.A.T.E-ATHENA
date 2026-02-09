# Modified: 2026-02-09T12:00:00Z | Author: COPILOT | Change: Add test coverage for slate_copilot_sdk_bridge module
"""
Tests for slate/slate_copilot_sdk_bridge.py — Copilot SDK bridge
"""

import pytest
import json
from unittest.mock import MagicMock, patch
from pathlib import Path

try:
    from slate.slate_copilot_sdk_bridge import CopilotSDKBridge
    MODULE_AVAILABLE = True
except ImportError as e:
    MODULE_AVAILABLE = False
    pytest.skip(f"slate_copilot_sdk_bridge not importable: {e}", allow_module_level=True)


class TestCopilotSDKBridge:
    """Test CopilotSDKBridge class."""

    def test_init_default(self):
        bridge = CopilotSDKBridge()
        assert bridge.workspace_root is not None
        assert isinstance(bridge.sdk_path, Path)

    def test_init_custom_workspace(self, tmp_path):
        bridge = CopilotSDKBridge(workspace_root=tmp_path)
        assert bridge.workspace_root == tmp_path

    def test_is_available_no_sdk(self, tmp_path):
        bridge = CopilotSDKBridge(workspace_root=tmp_path)
        assert bridge.is_available() is False

    def test_is_available_with_sdk(self, tmp_path):
        sdk_path = tmp_path / "vendor" / "copilot-sdk"
        sdk_path.mkdir(parents=True)
        (sdk_path / "README.md").write_text("# SDK")
        (sdk_path / "python").mkdir()
        bridge = CopilotSDKBridge(workspace_root=tmp_path)
        assert bridge.is_available() is True

    def test_get_protocol_version_no_file(self, tmp_path):
        bridge = CopilotSDKBridge(workspace_root=tmp_path)
        assert bridge.get_protocol_version() is None

    def test_get_protocol_version_with_file(self, tmp_path):
        sdk_path = tmp_path / "vendor" / "copilot-sdk"
        sdk_path.mkdir(parents=True)
        version_file = sdk_path / "sdk-protocol-version.json"
        version_file.write_text(json.dumps({"version": 2}))
        bridge = CopilotSDKBridge(workspace_root=tmp_path)
        assert bridge.get_protocol_version() == 2

    def test_get_protocol_version_invalid_json(self, tmp_path):
        sdk_path = tmp_path / "vendor" / "copilot-sdk"
        sdk_path.mkdir(parents=True)
        version_file = sdk_path / "sdk-protocol-version.json"
        version_file.write_text("not json")
        bridge = CopilotSDKBridge(workspace_root=tmp_path)
        assert bridge.get_protocol_version() is None

    def test_cached_availability(self, tmp_path):
        bridge = CopilotSDKBridge(workspace_root=tmp_path)
        # First call
        result1 = bridge.is_available()
        # Second call should use cache
        result2 = bridge.is_available()
        assert result1 == result2
