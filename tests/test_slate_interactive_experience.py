# tests/test_slate_interactive_experience.py

import pytest
from slate.slate_interactive_experience import InteractionOption, InteractionNode, NodeType, EmotionalTone

@pytest.fixture
def sample_option():
    return InteractionOption(
        id="1",
        label="Sample Option",
        description="This is a sample option.",
        icon="icon"
    )

@pytest.fixture
def sample_node(sample_option):
    return InteractionNode(
        id="hub",
        node_type=NodeType.HUB,
        title="Hub Node",
        narrative="Welcome to the hub!",
        options=[sample_option]
    )

def test_interaction_option_initialization(sample_option):
    assert sample_option.id == "1"
    assert sample_option.label == "Sample Option"
    assert sample_option.description == "This is a sample option."
    assert sample_option.icon == "icon"

def test_interaction_node_initialization(sample_node):
    assert sample_node.id == "hub"
    assert sample_node.node_type == NodeType.HUB
    assert sample_node.title == "Hub Node"
    assert sample_node.narrative == "Welcome to the hub!"
    assert len(sample_node.options) == 1

def test_interaction_node_add_option(sample_node):
    new_option = InteractionOption(
        id="2",
        label="New Option",
        description="This is a new option.",
        icon="new_icon"
    )
    sample_node.options.append(new_option)
    assert len(sample_node.options) == 2