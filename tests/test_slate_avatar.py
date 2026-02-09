"""Tests for slate_avatar.py — SLATE Avatar System engine."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))

from slate.slate_avatar import (
    AVATAR_NODES,
    AVATAR_CONNECTIONS,
    calculate_avatar_level,
    build_avatar_state,
    export_avatar_state,
)


def test_avatar_nodes_defined():
    """Verify avatar nodes are defined with correct structure."""
    assert len(AVATAR_NODES) == 17
    for node in AVATAR_NODES:
        assert "id" in node
        assert "label" in node
        assert "ring" in node
        assert node["ring"] in (0, 1, 2, 3)  # core=0, inner=1, middle=2, outer=3


def test_avatar_connections_defined():
    """Verify avatar connections reference valid node IDs."""
    node_ids = {n["id"] for n in AVATAR_NODES}
    assert len(AVATAR_CONNECTIONS) == 22
    for conn in AVATAR_CONNECTIONS:
        assert "from" in conn
        assert "to" in conn
        assert conn["from"] in node_ids, f"Unknown source: {conn['from']}"
        assert conn["to"] in node_ids, f"Unknown target: {conn['to']}"


def test_calculate_avatar_level():
    """Test avatar level calculation from tech tree stats."""
    # Mock tech tree with various completion levels
    mock_tree_low = {"nodes": [{"status": "complete"} for _ in range(5)] + [{"status": "available"} for _ in range(15)]}
    mock_tree_high = {"nodes": [{"status": "complete"} for _ in range(18)] + [{"status": "available"} for _ in range(2)]}
    mock_tree_all = {"nodes": [{"status": "complete"} for _ in range(20)]}

    level_low = calculate_avatar_level(mock_tree_low)
    level_high = calculate_avatar_level(mock_tree_high)
    level_all = calculate_avatar_level(mock_tree_all)

    assert 1 <= level_low <= 5
    assert 1 <= level_high <= 5
    assert level_high >= level_low
    assert level_all == 5


def test_build_avatar_state():
    """Test building avatar state without health checks."""
    state = build_avatar_state(check_health=False)
    assert "level" in state
    assert "level_name" in state
    assert "nodes" in state
    assert "connections" in state
    assert "tech_tree" in state
    assert len(state["nodes"]) == 17
    assert len(state["connections"]) == 22