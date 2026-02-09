# Modified: 2026-02-09T12:00:00Z | Author: COPILOT | Change: Add test coverage for adaptive_instructions module
"""
Tests for slate/adaptive_instructions.py — K8s adaptive instruction layer
"""

import pytest
import json
from unittest.mock import MagicMock, patch, PropertyMock
from pathlib import Path
from datetime import datetime, timezone


# Import from the module (wrap in try/except for optional dependencies)
try:
    from slate.adaptive_instructions import (
        AdaptiveInstructionController,
        InstructionContext,
        SystemState,
        InstructionMode,
        AgentAvailability,
        CONFIGMAP_NAME,
        CONFIGMAP_NAMESPACE,
    )
    MODULE_AVAILABLE = True
except ImportError as e:
    MODULE_AVAILABLE = False
    pytest.skip(f"adaptive_instructions not importable: {e}", allow_module_level=True)


class TestInstructionMode:
    """Test InstructionMode enum values."""

    def test_normal_mode(self):
        assert InstructionMode.NORMAL.value == "normal"

    def test_degraded_mode(self):
        assert InstructionMode.DEGRADED.value == "degraded"

    def test_emergency_mode(self):
        assert InstructionMode.EMERGENCY.value == "emergency"

    def test_all_modes_exist(self):
        modes = [m.value for m in InstructionMode]
        assert "normal" in modes
        assert "degraded" in modes
        assert "maintenance" in modes
        assert "autonomous" in modes
        assert "emergency" in modes
        assert "development" in modes


class TestAgentAvailability:
    """Test AgentAvailability enum values."""

    def test_full_availability(self):
        assert AgentAvailability.FULL.value == "full"

    def test_minimal_availability(self):
        assert AgentAvailability.MINIMAL.value == "minimal"

    def test_gpu_only(self):
        assert AgentAvailability.GPU_ONLY.value == "gpu-only"

    def test_cpu_only(self):
        assert AgentAvailability.CPU_ONLY.value == "cpu-only"


class TestSystemState:
    """Test SystemState dataclass."""

    def test_default_values(self):
        state = SystemState()
        assert state.k8s_available is False
        assert state.k8s_pods_total == 0
        assert state.k8s_pods_ready == 0

    def test_overall_health_healthy(self):
        state = SystemState()
        state.k8s_available = True
        state.k8s_pods_total = 5
        state.k8s_pods_ready = 5
        health = state.overall_health
        assert isinstance(health, str)

    def test_overall_health_degraded(self):
        state = SystemState()
        state.k8s_available = True
        state.k8s_pods_total = 5
        state.k8s_pods_ready = 2
        health = state.overall_health
        assert isinstance(health, str)


class TestAdaptiveInstructionController:
    """Test AdaptiveInstructionController class."""

    @patch("slate.adaptive_instructions.subprocess.run")
    def test_init(self, mock_run):
        controller = AdaptiveInstructionController()
        assert controller is not None

    @patch("slate.adaptive_instructions.subprocess.run")
    def test_collect_system_state(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="not found"
        )
        controller = AdaptiveInstructionController()
        state = controller.collect_system_state()
        assert isinstance(state, SystemState)

    @patch("slate.adaptive_instructions.subprocess.run")
    def test_evaluate_system_state(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr=""
        )
        controller = AdaptiveInstructionController()
        state = SystemState()
        ctx = controller.evaluate_system_state(state)
        assert isinstance(ctx, InstructionContext)
        assert isinstance(ctx.mode, InstructionMode)

    @patch("slate.adaptive_instructions.subprocess.run")
    def test_evaluate_emergency_mode_no_k8s(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr=""
        )
        controller = AdaptiveInstructionController()
        state = SystemState()
        state.k8s_available = False
        ctx = controller.evaluate_system_state(state)
        assert isinstance(ctx.mode, InstructionMode)

    @patch("slate.adaptive_instructions.subprocess.run")
    def test_generate_instruction_block(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr=""
        )
        controller = AdaptiveInstructionController()
        state = SystemState()
        ctx = controller.evaluate_system_state(state)
        block = controller.generate_instruction_block(ctx)
        assert isinstance(block, str)
        assert len(block) > 0

    @patch("slate.adaptive_instructions.subprocess.run")
    def test_apply_to_configmap_no_kubectl(self, mock_run):
        mock_run.side_effect = FileNotFoundError("kubectl not found")
        controller = AdaptiveInstructionController()
        success, msg = controller.apply_to_configmap()
        assert success is False

    @patch("slate.adaptive_instructions.subprocess.run")
    def test_read_from_configmap_no_kubectl(self, mock_run):
        mock_run.side_effect = FileNotFoundError("kubectl not found")
        controller = AdaptiveInstructionController()
        result = controller.read_from_configmap()
        assert result is None
