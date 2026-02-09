# tests/test_github_achievements.py

import pytest
from slate.github_achievements import (
    AchievementTier,
    AchievementStatus,
    GitHubAchievement,
    AchievementProgress,
)

@pytest.fixture
def sample_achievement():
    return GitHubAchievement(
        id="pull_shark",
        name="Pull Shark",
        description="Open PRs that get merged",
        icon="🦈",
        category="contributions",
        tiers={"bronze": 5, "silver": 20, "gold": 50},
    )

@pytest.fixture
def sample_progress(sample_achievement):
    return AchievementProgress(
        achievement_id=sample_achievement.id,
        current_count=10,
        current_tier=AchievementTier.SILVER,
        status=AchievementStatus.IN_PROGRESS,
    )

def test_git_hub_achievement_to_dict(sample_achievement):
    assert sample_achievement.to_dict() == {
        "id": "pull_shark",
        "name": "Pull Shark",
        "description": "Open PRs that get merged",
        "icon": "🦈",
        "category": "contributions",
        "tiers": {"bronze": 5, "silver": 20, "gold": 50},
    }

def test_achievement_progress_to_dict(sample_progress):
    assert sample_progress.to_dict() == {
        "achievement_id": "pull_shark",
        "current_count": 10,
        "current_tier": AchievementTier.SILVER.value,
        "status": AchievementStatus.IN_PROGRESS.value,
        "last_updated": sample_progress.last_updated,
    }

def test_achievement_progress_from_dict(sample_progress):
    data = sample_progress.to_dict()
    new_progress = AchievementProgress.from_dict(data)
    assert new_progress == sample_progress