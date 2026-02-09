# tests/test_guided_workflow.py

import os
import pytest
from slate.guided_workflow import (
    JobTemplate,
    JobCategory,
    WorkflowStage,
    _normalize_url,
    OLLAMA_URL,
    K8S_MODE,
)

def test_job_template_initialization():
    template = JobTemplate(
        id="test_id",
        name="Test Template",
        description="A test job template.",
        category=JobCategory.CODE_CHANGE,
        workflow="ci.yml"
    )
    assert template.id == "test_id"
    assert template.name == "Test Template"
    assert template.description == "A test job template."
    assert template.category == JobCategory.CODE_CHANGE
    assert template.workflow == "ci.yml"

def test_normalize_url():
    assert _normalize_url("http://example.com") == "http://example.com"
    assert _normalize_url("https://example.com") == "https://example.com"
    assert _normalize_url("example.com") == "http://example.com"

def test_ollama_url_env_var():
    # _normalize_url(None) raises AttributeError because None has no .startswith
    with pytest.raises((AttributeError, TypeError)):
        _normalize_url(None)
    assert OLLAMA_URL == "http://127.0.0.1:11434"

def test_k8s_mode_env_var():
    # K8S_MODE is a module-level constant, verify it's a bool
    assert isinstance(K8S_MODE, bool)

def test_workflow_stage_enum():
    assert WorkflowStage.TASK_QUEUE.value == "task_queue"
    assert WorkflowStage.RUNNER_PICKUP.value == "runner"
    assert WorkflowStage.WORKFLOW_EXEC.value == "workflow"
    assert WorkflowStage.VALIDATION.value == "validation"
    assert WorkflowStage.COMPLETION.value == "completion"

def test_job_category_enum():
    assert JobCategory.CODE_CHANGE.value == "code_change"
    assert JobCategory.BUG_FIX.value == "bug_fix"
    assert JobCategory.NEW_FEATURE.value == "new_feature"
    assert JobCategory.DOCUMENTATION.value == "documentation"
    assert JobCategory.TESTING.value == "testing"
    assert JobCategory.AI_ANALYSIS.value == "ai_analysis"
    assert JobCategory.MAINTENANCE.value == "maintenance"
    assert JobCategory.DEPLOYMENT.value == "deployment"
    assert JobCategory.PROJECT_PLANNING.value == "project_planning"