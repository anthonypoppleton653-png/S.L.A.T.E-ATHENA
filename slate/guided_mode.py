# Modified slate/guided_mode.py

from pathlib import Path
import sys
from typing import Tuple, Union
import unittest
from unittest.mock import patch, MagicMock
from urllib.parse import urlparse

sys.path.append(str(Path(__file__).parent.parent))
from slate.guided_mode import (
    GuidedModeState,
    StepStatus,
    StepResult,
    GuidedStep,
    GUIDED_STEPS,
    _normalize_url,
    initialize_guided_mode,
    process_step
)

class TestGuidedMode(unittest.TestCase):

    def setUp(self) -> None:
        self.step = GUIDED_STEPS[0]
        self.valid_url = "https://example.com/path"
        self.empty_url = ""
        self.invalid_scheme_url = "ftp://example.com"

    # ... (existing test methods)

    def test_normalize_url_missing_scheme(self) -> None:
        """Test that _normalize_url raises ValueError for URLs missing scheme."""
        with self.assertRaises(ValueError):
            _normalize_url("example.com/path")

    def test_process_step_invalid_step_type(self) -> None:
        """Test that process_step raises TypeError when step is not an instance of GuidedStep."""
        invalid_step = MagicMock()
        with self.assertRaises(TypeError):
            process_step(invalid_step, GuidedModeState.IN_PROGRESS)

    def test_process_step_valid_input(self) -> None:
        """Test that process_step returns StepResult when given valid inputs."""
        step_result = process_step(self.step, GuidedModeState.IN_PROGRESS)
        self.assertIsInstance(step_result, StepResult)

    def test_guided_mode_state_transitions_invalid(self) -> None:
        """Test that GuidedModeState raises errors for invalid transitions."""
        state = GuidedModeState(GuidedModeState.INITIALIZING)

        # ... (existing tests)

    def test_initialize_guided_mode(self) -> None:
        """Test that initialize_guided_mode returns an instance of GuidedModeState with default initial state."""
        state = initialize_guided_mode()
        self.assertIsInstance(state, GuidedModeState)
        self.assertEqual(state.current_state, GuidedModeState.INITIALIZING)

    def test_initialize_guided_mode_with_initial_state(self) -> None:
        """Test that initialize_guided_mode accepts an initial state argument and returns the expected instance."""
        custom_state = GuidedModeState(GuidedModeState.IN_PROGRESS)
        state = initialize_guided_mode(initial_state=custom_state)
        self.assertIsInstance(state, GuidedModeState)
        self.assertEqual(state.current_state, GuidedModeState.IN_PROGRESS)

    def test_initialize_guided_mode_with_invalid_initial_state(self) -> None:
        """Test that initialize_guided_mode raises ValueError when given an invalid initial state."""
        with self.assertRaises(ValueError):
            initialize_guided_mode(initial_state="invalid")

    def test_guided_mode_state_transitions_valid(self) -> None:
        """Test that GuidedModeState transitions between valid states."""
        state = GuidedModeState(GuidedModeState.INITIALIZING)
        state.transition_to(GuidedModeState.IN_PROGRESS)
        self.assertEqual(state.current_state, GuidedModeState.IN_PROGRESS)

    def test_guided_mode_state_transitions_invalid(self) -> None:
        """Test that GuidedModeState raises ValueError when transitioning to an invalid state."""
        state = GuidedModeState(GuidedModeState.INITIALIZING)
        with self.assertRaises(ValueError):
            state.transition_to("invalid")

    def test_guided_step_properties(self) -> None:
        """Test that GuidedStep has the expected properties."""
        step = GUIDED_STEPS[0]
        self.assertIsInstance(step.url, str)
        self.assertIsInstance(step.status, StepStatus)
        self.assertIsInstance(step.result, StepResult)

if __name__ == "__main__":
    unittest.main()