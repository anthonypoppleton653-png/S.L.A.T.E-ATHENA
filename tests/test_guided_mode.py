# tests/test_guided_mode.py
# Tests for SLATE Guided Mode Engine

import pytest
import py_compile
from pathlib import Path


GUIDED_MODE_PATH = Path(__file__).parent.parent / "slate" / "guided_mode.py"


def test_guided_mode_exists():
    """Verify guided_mode.py exists."""
    assert GUIDED_MODE_PATH.exists()


def test_guided_mode_syntax():
    """Verify valid Python syntax."""
    py_compile.compile(str(GUIDED_MODE_PATH), doraise=True)


def test_guided_mode_no_external_bindings():
    """Verify no 0.0.0.0 bindings."""
    content = GUIDED_MODE_PATH.read_text(encoding="utf-8")
    assert "0.0.0.0" not in content


def test_guided_mode_importable():
    """Verify guided_mode can be imported with core exports."""
    from slate.guided_mode import GuidedModeState, StepStatus, GuidedStep
    assert GuidedModeState is not None
    assert StepStatus is not None
    assert GuidedStep is not None


def test_guided_mode_state_enum():
    """Verify GuidedModeState enum has expected values."""
    from slate.guided_mode import GuidedModeState
    states = [s for s in GuidedModeState]
    assert len(states) >= 2
    assert GuidedModeState.INACTIVE in states
    assert GuidedModeState.EXECUTING in states


def test_step_status_enum():
    """Verify StepStatus enum has expected values."""
    from slate.guided_mode import StepStatus
    statuses = [s for s in StepStatus]
    assert StepStatus.PENDING in statuses


def test_guided_steps_list():
    """Verify GUIDED_STEPS is a non-empty list."""
    from slate.guided_mode import GUIDED_STEPS
    assert isinstance(GUIDED_STEPS, list)
    assert len(GUIDED_STEPS) > 0


def test_normalize_url():
    """Verify _normalize_url adds http:// prefix."""
    from slate.guided_mode import _normalize_url
    assert _normalize_url("http://127.0.0.1:11434") == "http://127.0.0.1:11434"
    assert _normalize_url("127.0.0.1:11434") == "http://127.0.0.1:11434"
