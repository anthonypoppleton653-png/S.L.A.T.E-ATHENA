# tests/test_project_onboarding.py

import pytest
from pathlib import Path
from slate.project_onboarding import (
    OnboardingPhase,
    ProjectInfo,
    DirectoryStructure,
    OnboardingState,
    ONBOARDING_STEPS
)

def test_onboarding_phase_enums():
    assert len(OnboardingPhase) == 9
    assert OnboardingPhase.WELCOME.value == "welcome"
    assert OnboardingPhase.COMPLETE.value == "complete"

def test_project_info_initialization():
    project = ProjectInfo()
    assert project.name == ""
    assert project.description == ""
    assert project.type == "general"
    assert project.language == "python"
    assert project.version == "0.1.0"
    assert project.license == "MIT"

def test_directory_structure_initialization():
    directories = DirectoryStructure()
    assert directories.root == Path(__file__).parent.parent
    assert directories.source_dir == "src"
    assert directories.tests_dir == "tests"
    assert directories.docs_dir == "docs"
    assert directories.config_dir == "config"
    assert not directories.has_venv
    assert not directories.has_git
    assert not directories.has_docker

def test_onboarding_state_initialization():
    state = OnboardingState()
    assert state.phase == OnboardingPhase.WELCOME
    assert state.step_index == 0
    assert isinstance(state.project, ProjectInfo)
    assert isinstance(state.directories, DirectoryStructure)
    assert state.completed_phases == []
    assert state.user_preferences == {}
    assert state.started_at is None
    assert state.completed_at is None

def test_onboarding_steps():
    welcome_steps = ONBOARDING_STEPS[OnboardingPhase.WELCOME]
    assert len(welcome_steps) == 1
    assert welcome_steps[0]["id"] == "welcome_intro"
    assert welcome_steps[0]["title"] == "Welcome to S.L.A.T.E."
    assert welcome_steps[0]["content_type"] == "hero"
    assert welcome_steps[0]["auto_advance"] is False

@pytest.mark.skip(reason="Integration tests for onboarding steps are complex and require UI interaction")
def test_onboarding_steps_with_ui():
    # This test would interact with the UI to validate onboarding steps, but it's skipped here
    pass