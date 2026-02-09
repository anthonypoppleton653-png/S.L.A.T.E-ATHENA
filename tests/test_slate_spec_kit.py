# tests/test_slate_spec_kit.py

import pytest
from pathlib import Path
from slate.slate_spec_kit import SpecParser, SpecSection, ParsedSpec

@pytest.fixture
def sample_spec_path():
    """Fixture for a sample spec.md file."""
    return Path(__file__).parent / "sample.spec.md"

def test_parse_metadata(sample_spec_path):
    """Test parsing metadata from spec header."""
    parser = SpecParser()
    with open(sample_spec_path, "r") as f:
        content = f.read()

    metadata = parser.parse_metadata(content)
    assert metadata == {
        "status": "draft",
        "created": "2026-01-01",
        "author": "John Doe"
    }

def test_parse_sections(sample_spec_path):
    """Test parsing sections from spec content."""
    parser = SpecParser()
    with open(sample_spec_path, "r") as f:
        content = f.read()

    parsed_spec = ParsedSpec(
        spec_id="001-sample-spec",
        spec_path=sample_spec_path,
        title="Sample Specification",
        metadata={},
        sections=[]
    )
    parser.parse_sections(content, parsed_spec)

    assert len(parsed_spec.sections) == 3
    assert parsed_spec.sections[0].title == "Introduction"
    assert parsed_spec.sections[1].title == "Design Principles"
    assert parsed_spec.sections[2].title == "Implementation Details"

def test_get_all_sections_flat():
    """Test getting all sections flattened."""
    spec = ParsedSpec(
        spec_id="001-sample-spec",
        spec_path=Path("sample.spec.md"),
        title="Sample Specification",
        metadata={},
        sections=[
            SpecSection(level=2, title="Introduction", anchor="introduction", content="..."),
            SpecSection(level=3, title="Purpose", anchor="purpose", content="...")
        ]
    )
    assert spec.get_all_sections_flat() == [
        SpecSection(level=2, title="Introduction", anchor="introduction", content="..."),
        SpecSection(level=3, title="Purpose", anchor="purpose", content="...")
    ]