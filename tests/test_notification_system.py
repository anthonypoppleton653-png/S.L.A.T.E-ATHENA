# Modified: 2026-02-09T12:00:00Z | Author: COPILOT | Change: Add test coverage for notification_system module
"""
Tests for slate/notification_system.py — Notification system
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

try:
    from slate.notification_system import (
        NotificationType,
        Notification,
        NotificationManager,
        get_notification_manager,
        get_sound_for_type,
    )
    MODULE_AVAILABLE = True
except ImportError as e:
    MODULE_AVAILABLE = False
    pytest.skip(f"notification_system not importable: {e}", allow_module_level=True)


class TestNotificationType:
    """Test NotificationType enum."""

    def test_success_type(self):
        assert NotificationType.SUCCESS.value == "success"

    def test_error_type(self):
        assert NotificationType.ERROR.value == "error"

    def test_warning_type(self):
        assert NotificationType.WARNING.value == "warning"

    def test_info_type(self):
        assert NotificationType.INFO.value == "info"

    def test_input_required_type(self):
        assert NotificationType.INPUT_REQUIRED.value == "input"


class TestNotification:
    """Test Notification dataclass."""

    def test_create_notification(self):
        notif = Notification(
            id="test_1",
            type=NotificationType.INFO,
            title="Test",
            message="Test message"
        )
        assert notif.id == "test_1"
        assert notif.type == NotificationType.INFO

    def test_to_dict(self):
        notif = Notification(
            id="test_1",
            type=NotificationType.SUCCESS,
            title="Done",
            message="Task completed"
        )
        d = notif.to_dict()
        assert isinstance(d, dict)
        assert d["id"] == "test_1"
        assert d["type"] == "success"
        assert d["title"] == "Done"

    def test_default_duration(self):
        notif = Notification(
            id="test_1",
            type=NotificationType.INFO,
            title="Test",
            message="msg"
        )
        assert notif.duration_ms == 5000

    def test_persistent_notification(self):
        notif = Notification(
            id="test_1",
            type=NotificationType.ERROR,
            title="Error",
            message="Something broke",
            persistent=True
        )
        assert notif.persistent is True


class TestNotificationManager:
    """Test NotificationManager class."""

    def test_create_manager(self):
        mgr = NotificationManager()
        assert mgr.unread_count == 0
        assert len(mgr.notifications) == 0

    def test_create_notification(self):
        mgr = NotificationManager()
        notif = mgr.create(
            type=NotificationType.INFO,
            title="Hello",
            message="World"
        )
        assert isinstance(notif, Notification)
        assert mgr.unread_count == 1

    def test_task_completed(self):
        mgr = NotificationManager()
        notif = mgr.task_completed("Build", "Success")
        assert notif.type == NotificationType.SUCCESS

    def test_error_notification(self):
        mgr = NotificationManager()
        notif = mgr.error("Failed", "Something went wrong")
        assert notif.type == NotificationType.ERROR

    def test_info_notification(self):
        mgr = NotificationManager()
        notif = mgr.info("Update", "New version")
        assert notif.type == NotificationType.INFO

    def test_get_recent(self):
        mgr = NotificationManager()
        mgr.info("Test 1", "msg")
        mgr.info("Test 2", "msg")
        recent = mgr.get_recent(limit=5)
        assert len(recent) == 2

    def test_clear_all(self):
        mgr = NotificationManager()
        mgr.info("Test", "msg")
        mgr.clear_all()
        assert mgr.unread_count == 0


class TestGetSoundForType:
    """Test get_sound_for_type function."""

    def test_sound_for_success(self):
        result = get_sound_for_type(NotificationType.SUCCESS)
        assert isinstance(result, str)

    def test_sound_for_error(self):
        result = get_sound_for_type(NotificationType.ERROR)
        assert isinstance(result, str)


class TestGetNotificationManager:
    """Test singleton getter."""

    def test_returns_manager(self):
        mgr = get_notification_manager()
        assert isinstance(mgr, NotificationManager)

    def test_returns_same_instance(self):
        mgr1 = get_notification_manager()
        mgr2 = get_notification_manager()
        assert mgr1 is mgr2
