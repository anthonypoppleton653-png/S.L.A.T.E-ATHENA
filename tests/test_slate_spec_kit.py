# Modified: 2026-02-10T12:00:00Z | Author: COPILOT | Change: Fix parse_sections signature, add line_start/line_end to SpecSection, use inline spec content
# tests/test_slate_spec_kit.py

import pytest
from pathlib import Path
from slate.slate_spec_kit import SpecParser, SpecSection, ParsedSpec


SAMPLE_SPEC_CONTENT = """# Sample Specification

**Status**: draft
**Created**: 2026-01-01
**Author**: John Doe

## Introduction

This is the introduction section.

## Design Principles

These are the design principles.

## Implementation Details

Here are the implementation details.
"""


def test_parse_metadata():
    """Test parsing metadata from spec header."""
    parser = SpecParser()
    metadata = parser.parse_metadata(SAMPLE_SPEC_CONTENT)
    assert metadata["status"] == "draft"
    assert metadata["created"] == "2026-01-01"
    assert metadata["author"] == "John Doe"


def test_parse_sections():
    """Test parsing sections from spec content."""
    parser = SpecParser()
    sections = parser.parse_sections(SAMPLE_SPEC_CONTENT)

    assert len(sections) == 3
    assert sections[0].title == "Introduction"
    assert sections[1].title == "Design Principles"
    assert sections[2].title == "Implementation Details"


def test_get_all_sections_flat():
    """Test getting all sections flattened."""
    spec = ParsedSpec(
        spec_id="001-sample-spec",
        spec_path=Path("sample.spec.md"),
        title="Sample Specification",
        metadata={},
        sections=[
            SpecSection(level=2, title="Introduction", anchor="introduction", content="...", line_start=0, line_end=5),
            SpecSection(level=3, title="Purpose", anchor="purpose", content="...", line_start=6, line_end=10)
        ],
        raw_content=""
    )
    flat = spec.get_all_sections_flat()
    assert len(flat) >= 2
    assert flat[0].title == "Introduction"
    assert flat[1].title == "Purpose"