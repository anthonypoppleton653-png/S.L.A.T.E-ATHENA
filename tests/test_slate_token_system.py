# tests/test_slate_token_system.py

import pytest
from slate.slate_token_system import TokenType, DEFAULT_TTL, TOKEN_PREFIXES, AGENTS, SERVICES, Token

def test_token_type_enum():
    assert TokenType.SERVICE.value == "service"
    assert TokenType.AGENT.value == "agent"

def test_default_ttl():
    assert DEFAULT_TTL[TokenType.SERVICE] == 720
    assert DEFAULT_TTL[TokenType.AGENT] == 168

def test_token_prefixes():
    assert TOKEN_PREFIXES[TokenType.SERVICE] == "slsvc"
    assert TOKEN_PREFIXES[TokenType.AGENT] == "slagt"

def test_agent_and_service_identifiers():
    assert AGENTS == [
        "ALPHA", "BETA", "GAMMA", "DELTA",
        "COPILOT", "COPILOT_CHAT", "ANTIGRAVITY", "CLAUDECODE"
    ]
    assert SERVICES == [
        "dashboard", "ollama", "chromadb", "agent-router",
        "autonomous-loop", "copilot-bridge", "workflow",
        "metrics", "mcp-server", "foundry-local", "github-runner"
    ]

def test_token_initialization():
    token = Token("test_id", TokenType.SERVICE, "Test Service")
    assert token.id == "test_id"
    assert token.token_type == TokenType.SERVICE.value
    assert token.name == "Test Service"