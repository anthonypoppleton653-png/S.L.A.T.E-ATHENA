# Modified: 2026-02-09T12:00:00Z | Author: COPILOT | Change: Add test coverage for dev_cycle_engine module
"""
Tests for slate/dev_cycle_engine.py — Development cycle engine
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path

try:
    from slate.dev_cycle_engine import (
        DevCycleStage,
        ActivityStatus,
        StageActivity,
        DevCycleState,
        DevCycleEngine,
        STAGE_METADATA,
    )
    MODULE_AVAILABLE = True
except ImportError as e:
    MODULE_AVAILABLE = False
    pytest.skip(f"dev_cycle_engine not importable: {e}", allow_module_level=True)


class TestDevCycleStage:
    """Test DevCycleStage enum."""

    def test_plan_stage(self):
        assert DevCycleStage.PLAN.value == "plan"

    def test_code_stage(self):
        assert DevCycleStage.CODE.value == "code"

    def test_test_stage(self):
        assert DevCycleStage.TEST.value == "test"

    def test_deploy_stage(self):
        assert DevCycleStage.DEPLOY.value == "deploy"

    def test_feedback_stage(self):
        assert DevCycleStage.FEEDBACK.value == "feedback"

    def test_all_five_stages(self):
        stages = list(DevCycleStage)
        assert len(stages) == 5


class TestActivityStatus:
    """Test ActivityStatus enum."""

    def test_pending_status(self):
        assert ActivityStatus.PENDING.value == "pending"

    def test_active_status(self):
        assert ActivityStatus.ACTIVE.value == "active"

    def test_complete_status(self):
        assert ActivityStatus.COMPLETE.value == "complete"


class TestStageMetadata:
    """Test stage metadata map."""

    def test_metadata_has_all_stages(self):
        for stage in DevCycleStage:
            assert stage in STAGE_METADATA, f"Missing metadata for stage: {stage}"

    def test_metadata_has_icon(self):
        for stage, meta in STAGE_METADATA.items():
            assert "icon" in meta

    def test_metadata_has_color(self):
        for stage, meta in STAGE_METADATA.items():
            assert "color" in meta

    def test_metadata_has_description(self):
        for stage, meta in STAGE_METADATA.items():
            assert "description" in meta

    def test_metadata_has_integrations(self):
        for stage, meta in STAGE_METADATA.items():
            assert "integrations" in meta
            assert isinstance(meta["integrations"], list)


class TestStageActivity:
    """Test StageActivity dataclass."""

    def test_create_activity(self):
        activity = StageActivity(
            title="Write tests",
            description="Add pytest coverage",
            stage=DevCycleStage.TEST
        )
        assert activity.title == "Write tests"
        assert activity.stage == DevCycleStage.TEST

    def test_activity_to_dict(self):
        activity = StageActivity(
            title="Deploy",
            description="Push to K8s",
            stage=DevCycleStage.DEPLOY
        )
        d = activity.to_dict()
        assert isinstance(d, dict)
        assert d["title"] == "Deploy"


class TestDevCycleEngine:
    """Test DevCycleEngine class."""

    def test_init(self, tmp_path):
        engine = DevCycleEngine(state_dir=tmp_path)
        assert engine is not None

    @pytest.mark.asyncio
    async def test_get_current_state(self, tmp_path):
        engine = DevCycleEngine(state_dir=tmp_path)
        state = await engine.get_current_state()
        assert isinstance(state, DevCycleState)

    @pytest.mark.asyncio
    async def test_get_current_stage(self, tmp_path):
        engine = DevCycleEngine(state_dir=tmp_path)
        stage = await engine.get_current_stage()
        assert isinstance(stage, DevCycleStage)
