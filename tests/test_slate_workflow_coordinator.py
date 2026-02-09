# Modified: 2026-02-08T18:00:00Z | Author: COPILOT | Change: Add test coverage for slate_workflow_coordinator.py
"""Tests for slate/slate_workflow_coordinator.py — WorkflowCoordinator, dataclasses, config."""
import sys
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestConstants:
    """Test module-level constants."""

    def test_workspace_root(self):
        from slate.slate_workflow_coordinator import WORKSPACE_ROOT
        assert isinstance(WORKSPACE_ROOT, Path)

    def test_state_file_path(self):
        from slate.slate_workflow_coordinator import STATE_FILE
        assert isinstance(STATE_FILE, (str, Path))

    def test_workflows_dir(self):
        from slate.slate_workflow_coordinator import WORKFLOWS_DIR
        assert isinstance(WORKFLOWS_DIR, Path)

    def test_workflow_config_has_entries(self):
        from slate.slate_workflow_coordinator import WORKFLOW_CONFIG
        assert isinstance(WORKFLOW_CONFIG, dict)
        assert len(WORKFLOW_CONFIG) >= 5
        for name, config in WORKFLOW_CONFIG.items():
            assert 'category' in config
            assert 'priority' in config
            assert 'gpu_required' in config

    def test_workflow_config_categories(self):
        from slate.slate_workflow_coordinator import WORKFLOW_CONFIG
        categories = {c['category'] for c in WORKFLOW_CONFIG.values()}
        assert len(categories) >= 2

    def test_optimal_sequence_has_phases(self):
        from slate.slate_workflow_coordinator import OPTIMAL_SEQUENCE
        assert isinstance(OPTIMAL_SEQUENCE, (list, dict))
        if isinstance(OPTIMAL_SEQUENCE, list):
            assert len(OPTIMAL_SEQUENCE) >= 3
        else:
            assert len(OPTIMAL_SEQUENCE) >= 3


class TestWorkflowRun:
    """Test WorkflowRun dataclass."""

    def test_create_run(self):
        from slate.slate_workflow_coordinator import WorkflowRun
        run = WorkflowRun(
            workflow='ci.yml',
            run_id='12345',
            status='completed',
            conclusion='success'
        )
        assert run.workflow == 'ci.yml'
        assert run.status == 'completed'

    def test_run_defaults(self):
        from slate.slate_workflow_coordinator import WorkflowRun
        run = WorkflowRun(
            workflow='nightly.yml',
            run_id='999',
            status='in_progress'
        )
        assert run.conclusion is None or run.conclusion == ''


class TestExecutionPlan:
    """Test ExecutionPlan dataclass."""

    def test_create_plan(self):
        from slate.slate_workflow_coordinator import ExecutionPlan
        plan = ExecutionPlan(
            phases=[['ci.yml'], ['slate.yml']],
            total_estimated_minutes=30,
            gpu_utilization=0.5,
            model_switches=2
        )
        assert len(plan.phases) == 2
        assert plan.total_estimated_minutes == 30


class TestWorkflowCoordinator:
    """Test WorkflowCoordinator class."""

    def test_init(self):
        from slate.slate_workflow_coordinator import WorkflowCoordinator
        coord = WorkflowCoordinator()
        assert hasattr(coord, 'get_workflow_list')
        assert hasattr(coord, 'generate_execution_plan')

    def test_get_workflow_list(self):
        from slate.slate_workflow_coordinator import WorkflowCoordinator
        coord = WorkflowCoordinator()
        workflows = coord.get_workflow_list()
        assert isinstance(workflows, list)
        # Should find at least some .yml files in .github/workflows/
        assert len(workflows) >= 1

    def test_generate_execution_plan(self):
        from slate.slate_workflow_coordinator import WorkflowCoordinator
        coord = WorkflowCoordinator()
        plan = coord.generate_execution_plan()
        assert hasattr(plan, 'phases')
        assert hasattr(plan, 'total_estimated_minutes')
        assert plan.total_estimated_minutes >= 0

    def test_generate_execution_plan_specific(self):
        from slate.slate_workflow_coordinator import WorkflowCoordinator, WORKFLOW_CONFIG
        coord = WorkflowCoordinator()
        names = list(WORKFLOW_CONFIG.keys())[:2]
        plan = coord.generate_execution_plan(names)
        assert hasattr(plan, 'phases')

    def test_load_state_missing(self):
        from slate.slate_workflow_coordinator import WorkflowCoordinator
        coord = WorkflowCoordinator()
        state = coord._load_state()
        assert isinstance(state, dict)

    def test_check_workflow_available(self):
        from slate.slate_workflow_coordinator import WorkflowCoordinator
        coord = WorkflowCoordinator()
        # Should return bool without error
        result = coord.check_workflow_available('ci.yml')
        assert isinstance(result, bool)

    @patch('slate.slate_workflow_coordinator.WorkflowCoordinator._run_gh')
    def test_get_recent_runs_mock(self, mock_gh):
        from slate.slate_workflow_coordinator import WorkflowCoordinator
        mock_result = MagicMock()
        mock_result.stdout = json.dumps([])
        mock_result.returncode = 0
        mock_gh.return_value = mock_result
        coord = WorkflowCoordinator()
        runs = coord.get_recent_runs(limit=5)
        assert isinstance(runs, list)

    def test_analyze_workflow_efficiency(self):
        from slate.slate_workflow_coordinator import WorkflowCoordinator
        coord = WorkflowCoordinator()
        result = coord.analyze_workflow_efficiency()
        assert isinstance(result, dict)
