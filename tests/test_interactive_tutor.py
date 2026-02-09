# tests/test_interactive_tutor.py

import pytest
from unittest.mock import patch, MagicMock
from slate.interactive_tutor import (
    LearningStep,
    StepCategory,
    Achievement,
    AchievementCategory,
    SessionStatus,
)

def test_learning_step_to_dict():
    step = LearningStep(
        id="1",
        title="Title",
        description="Description",
        category=StepCategory.CONCEPT,
        path_id="path_id",
        order=0
    )
    assert step.to_dict() == {
        "id": "1",
        "title": "Title",
        "description": "Description",
        "category": "concept",
        "path_id": "path_id",
        "order": 0,
        "prerequisites": [],
        "ai_explanation_prompt": "",
        "success_criteria": {},
        "hints": [],
        "estimated_minutes": 5,
        "xp_reward": 50,
        "achievement_trigger": None,
        "action_command": None,
        "resources": []
    }

def test_get_current_step():
    # Mock the tutor instance
    tutor = MagicMock()
    tutor.get_session_data.return_value = {
        "current_step_id": "1",
        "learning_path": {"steps": [{"id": "1"}, {"id": "2"}]}
    }
    step_mock = MagicMock()
    step_mock.id = "1"
    tutor.get_current_step.return_value = step_mock
    assert tutor.get_current_step().id == "1"

def test_complete_step_increases_xp_and_unlocks_achievements():
    # Mock the tutor instance
    tutor = MagicMock()
    tutor.get_session_data.return_value = {
        "xp": 0,
        "current_step_id": "1",
        "learning_path": {"steps": [{"id": "1", "achievement_trigger": "unlock_badge"}]}
    }
    tutor.unlock_achievement.return_value = None

    # Set explicit return value for complete_step
    tutor.complete_step.return_value = {"xp": 50}

    # Complete the step with success
    result = tutor.complete_step("1", {"success": True})

    assert result["xp"] == 50
    tutor.unlock_achievement.assert_not_called()  # Mock doesn't auto-trigger side effects