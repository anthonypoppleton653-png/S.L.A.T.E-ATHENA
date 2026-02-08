# Modified: 2026-02-08T08:00:00Z | Author: COPILOT | Change: Add test coverage for slate_chromadb module
"""
Tests for slate/slate_chromadb.py — ChromaDB vector store integration,
collection management, text chunking, indexing, search, and status.
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from slate.slate_chromadb import (
    COLLECTIONS,
    WORKSPACE_ROOT,
    SlateChromaDB,
)


# ── COLLECTIONS config ──────────────────────────────────────────────────


class TestCollections:
    """Tests for collection configuration constants."""

    def test_has_expected_collections(self):
        expected = {"slate_code", "slate_docs", "slate_workflows", "slate_config"}
        assert set(COLLECTIONS.keys()) == expected

    def test_each_collection_has_required_keys(self):
        for name, config in COLLECTIONS.items():
            assert "description" in config, f"{name} missing description"
            assert "dirs" in config, f"{name} missing dirs"
            assert "extensions" in config, f"{name} missing extensions"
            assert "chunk_size" in config, f"{name} missing chunk_size"

    def test_chunk_sizes_are_positive(self):
        for name, config in COLLECTIONS.items():
            assert config["chunk_size"] > 0, f"{name} chunk_size must be positive"


# ── SlateChromaDB init ─────────────────────────────────────────────────


class TestSlateChromaDBInit:
    """Tests for SlateChromaDB initialization."""

    def test_workspace_set(self):
        db = SlateChromaDB()
        assert db.workspace == WORKSPACE_ROOT

    def test_db_path_exists(self):
        db = SlateChromaDB()
        assert db.db_path.exists()

    def test_state_is_dict(self):
        db = SlateChromaDB()
        assert isinstance(db.state, dict)


# ── _chunk_text ─────────────────────────────────────────────────────────


class TestChunkText:
    """Tests for SlateChromaDB._chunk_text()."""

    def test_short_text_single_chunk(self):
        db = SlateChromaDB()
        chunks = db._chunk_text("hello world", max_chars=500)
        assert len(chunks) == 1
        assert chunks[0] == "hello world"

    def test_empty_text(self):
        db = SlateChromaDB()
        chunks = db._chunk_text("", max_chars=500)
        assert len(chunks) >= 1

    def test_long_text_splits(self):
        db = SlateChromaDB()
        # Create text with many lines
        lines = [f"line {i}: " + "x" * 40 for i in range(50)]
        text = "\n".join(lines)
        chunks = db._chunk_text(text, max_chars=200)
        assert len(chunks) > 1

    def test_chunks_cover_all_content(self):
        db = SlateChromaDB()
        text = "line1\nline2\nline3\nline4\nline5"
        chunks = db._chunk_text(text, max_chars=15)
        # All original lines should appear in at least one chunk
        combined = "\n".join(chunks)
        for line in ["line1", "line2", "line3", "line4", "line5"]:
            assert line in combined

    def test_respects_max_chars_approximately(self):
        db = SlateChromaDB()
        lines = [f"line{i}" for i in range(100)]
        text = "\n".join(lines)
        chunks = db._chunk_text(text, max_chars=50)
        # Each chunk should be roughly within limits (may exceed slightly)
        for chunk in chunks:
            # Allow some overflow due to line-based splitting
            assert len(chunk) < 200


# ── _file_hash ──────────────────────────────────────────────────────────


class TestFileHash:
    """Tests for SlateChromaDB._file_hash()."""

    def test_returns_string(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello")
        db = SlateChromaDB()
        h = db._file_hash(f)
        assert isinstance(h, str)
        assert len(h) == 16  # Truncated SHA-256

    def test_same_content_same_hash(self, tmp_path):
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        f1.write_text("same content")
        f2.write_text("same content")
        db = SlateChromaDB()
        assert db._file_hash(f1) == db._file_hash(f2)

    def test_different_content_different_hash(self, tmp_path):
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        f1.write_text("content A")
        f2.write_text("content B")
        db = SlateChromaDB()
        assert db._file_hash(f1) != db._file_hash(f2)


# ── State management ───────────────────────────────────────────────────


class TestStateManagement:
    """Tests for state save/load."""

    def test_load_state_returns_dict(self):
        db = SlateChromaDB()
        state = db._load_state()
        assert isinstance(state, dict)

    def test_state_has_expected_keys(self):
        db = SlateChromaDB()
        state = db._load_state()
        # Default state should have these
        expected_keys = {"last_full_index", "last_incremental", "file_hashes",
                         "total_indexed", "total_chunks"}
        # Either loaded or default should have them
        if "file_hashes" not in state:
            # First run, partial state is OK
            pass
        else:
            assert expected_keys.issubset(state.keys())


# ── Collection management ──────────────────────────────────────────────


class TestCollectionManagement:
    """Tests for collection get/create/list."""

    def test_get_or_create_collection(self):
        db = SlateChromaDB()
        col = db.get_or_create_collection("test_collection_unit")
        assert col is not None
        assert col.name == "test_collection_unit"
        # Cleanup
        try:
            db.client.delete_collection("test_collection_unit")
        except Exception:
            pass

    def test_list_collections_returns_list(self):
        db = SlateChromaDB()
        cols = db.list_collections()
        assert isinstance(cols, list)

    def test_list_collections_items_have_keys(self):
        db = SlateChromaDB()
        # Create a test collection
        db.get_or_create_collection("test_list_unit")
        cols = db.list_collections()
        if cols:
            assert "name" in cols[0]
            assert "count" in cols[0]
        # Cleanup
        try:
            db.client.delete_collection("test_list_unit")
        except Exception:
            pass


# ── get_status ──────────────────────────────────────────────────────────


class TestGetStatus:
    """Tests for SlateChromaDB.get_status()."""

    def test_returns_dict(self):
        db = SlateChromaDB()
        status = db.get_status()
        assert isinstance(status, dict)

    def test_has_available_key(self):
        db = SlateChromaDB()
        status = db.get_status()
        assert "available" in status

    def test_available_has_details(self):
        db = SlateChromaDB()
        status = db.get_status()
        if status.get("available"):
            assert "db_path" in status
            assert "collections" in status
            assert "total_documents" in status
            assert "embedding_model" in status


# ── print_status ────────────────────────────────────────────────────────


class TestPrintStatus:
    """Tests for SlateChromaDB.print_status()."""

    def test_prints_output(self, capsys):
        db = SlateChromaDB()
        db.print_status()
        captured = capsys.readouterr()
        assert "ChromaDB" in captured.out

    def test_prints_status_label(self, capsys):
        db = SlateChromaDB()
        db.print_status()
        captured = capsys.readouterr()
        # Should have either "Active" or "ERROR"
        assert "Active" in captured.out or "ERROR" in captured.out


# ── index_collection ───────────────────────────────────────────────────


class TestIndexCollection:
    """Tests for SlateChromaDB.index_collection()."""

    def test_unknown_collection_returns_error(self):
        db = SlateChromaDB()
        result = db.index_collection("nonexistent_collection")
        assert "error" in result

    @patch.object(SlateChromaDB, "_embed_batch")
    def test_index_returns_stats(self, mock_embed):
        mock_embed.return_value = [[0.0] * 768]
        db = SlateChromaDB()
        result = db.index_collection("slate_code", incremental=True)
        assert "collection" in result
        assert result["collection"] == "slate_code"
        assert "files_indexed" in result
        assert "chunks_added" in result


# ── CLI main ────────────────────────────────────────────────────────────


class TestMain:
    """Tests for main() CLI entry point."""

    @patch("sys.argv", ["slate_chromadb.py", "--status"])
    def test_status_flag(self, capsys):
        from slate.slate_chromadb import main
        main()
        captured = capsys.readouterr()
        assert "ChromaDB" in captured.out

    @patch("sys.argv", ["slate_chromadb.py", "--json"])
    def test_json_flag(self, capsys):
        from slate.slate_chromadb import main
        main()
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "available" in data
