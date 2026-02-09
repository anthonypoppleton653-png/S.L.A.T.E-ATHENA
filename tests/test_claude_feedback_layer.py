# tests/test_claude_feedback_layer.py

import pytest
from slate.claude_feedback_layer import (
    EventType,
    PatternType,
    ToolEvent,
    PatternInsight,
)

def test_tool_event_to_dict_and_from_dict():
    event = ToolEvent(
        id="123",
        tool_name="example_tool",
        tool_input={"input_key": "input_value"},
    )
    assert event.to_dict() == {
        "id": "123",
        "tool_name": "example_tool",
        "tool_input": {"input_key": "input_value"},
        "success": True,
        "timestamp": event.timestamp,
    }

    new_event = ToolEvent.from_dict(event.to_dict())
    assert isinstance(new_event, ToolEvent)
    assert new_event.id == "123"
    assert new_event.tool_name == "example_tool"
    assert new_event.tool_input == {"input_key": "input_value"}

def test_pattern_insight_to_dict_and_from_dict():
    insight = PatternInsight(
        id="456",
        pattern_type=PatternType.REPETITIVE_ACTION,
        description="Repetitive action detected",
    )
    assert insight.to_dict() == {
        "id": "456",
        "pattern_type": "repetitive_action",
        "description": "Repetitive action detected",
        "frequency": 1,
        "confidence": 0.0,
        "affected_tools": [],
        "first_seen": insight.first_seen,
        "last_seen": insight.last_seen,
    }

    new_insight = PatternInsight.from_dict(insight.to_dict())
    assert isinstance(new_insight, PatternInsight)
    assert new_insight.id == "456"
    assert new_insight.pattern_type == PatternType.REPETITIVE_ACTION
    assert new_insight.description == "Repetitive action detected"

def test_event_type_and_pattern_type_enums():
    assert EventType.TOOL_EXECUTED.value == "tool_executed"
    assert PatternType.REPETITIVE_ACTION.value == "repetitive_action"