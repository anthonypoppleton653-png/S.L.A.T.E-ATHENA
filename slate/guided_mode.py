# Modified: Added more tests for guided_mode.py

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import os
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from slate.guided_mode import (
    GuidedModeState,
    StepStatus,
    StepResult,
    GuidedStep,
    GUIDED_STEPS,
    _normalize_url,
    OLLAMA_URL,
    DASHBOARD_URL,
    K8S_MODE,
)

class TestGuidedMode(unittest.TestCase):

    def setUp(self):
        self.mock_step = GuidedStep(
            id="test",
            title="Test Step",
            description="A test step",
            category="test"
        )

    @patch('os.environ.get')
    def test_normalize_url(self, mock_get: MagicMock) -> None:
        mock_get.return_value = "127.0.0.1:11434"

        self.assertEqual(_normalize_url("http://127.0.0.1:11434"), "http://127.0.0.1:11434")
        self.assertEqual(_normalize_url("https://127.0.0.1:11434"), "https://127.0.0.1:11434")
        self.assertEqual(_normalize_url("127.0.0.1:11434"), "http://127.0.0.1:11434")

    def test_guided_step_init(self) -> None:
        step = GuidedStep(**self.mock_step.__dict__)
        self.assertIsInstance(step, GuidedStep)
        self.assertEqual(step.id, "test")
        self.assertEqual(step.status, StepStatus.PENDING)

    def test_guided_mode_state(self) -> None:
        states = [s.value for s in GuidedModeState]
        self.assertIn(GuidedModeState.INACTIVE.value, states)
        self.assertIsInstance(GuidedModeState.INACTIVE, GuidedModeState)

    def test_step_status(self) -> None:
        statuses = [s.value for s in StepStatus]
        self.assertIn(StepStatus.PENDING.value, statuses)
        self.assertIsInstance(StepStatus.PENDING, StepStatus)

    def test_step_result_init(self) -> None:
        result = StepResult(success=True, message="Success")
        self.assertIsInstance(result, StepResult)
        self.assertTrue(result.success)
        self.assertEqual(result.message, "Success")

    def test_guided_steps_initialization(self) -> None:
        self.assertIsInstance(GUIDED_STEPS, list)
        self.assertGreater(len(GUIDED_STEPS), 0)

    # Added tests

    def test_guided_step_update_status(self) -> None:
        step = GuidedStep(**self.mock_step.__dict__)
        step.update_status(StepStatus.COMPLETED)
        self.assertEqual(step.status, StepStatus.COMPLETED)

    def test_guided_mode_state_iteration(self) -> None:
        states = list(GuidedModeState)
        self.assertIn(GuidedModeState.ACTIVE, states)
        self.assertIn(GuidedModeState.INACTIVE, states)

    def test_guided_step_set_result(self) -> None:
        step = GuidedStep(**self.mock_step.__dict__)
        result = StepResult(success=True, message="Success")
        step.set_result(result)
        self.assertIsInstance(step.result, StepResult)
        self.assertTrue(step.result.success)
        self.assertEqual(step.result.message, "Success")

    def test_guided_step_set_status_and_result(self) -> None:
        step = GuidedStep(**self.mock_step.__dict__)
        result = StepResult(success=False, message="Failure")
        step.set_status(StepStatus.FAILED, result)
        self.assertEqual(step.status, StepStatus.FAILED)
        self.assertIsInstance(step.result, StepResult)
        self.assertFalse(step.result.success)
        self.assertEqual(step.result.message, "Failure")

if __name__ == '__main__':
    unittest.main()