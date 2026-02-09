#!/usr/bin/env python3
# Modified: 2026-02-09T04:30:00Z | Author: Claude | Change: Create autogen SDK integration for SLATE
"""
Vendor Microsoft AutoGen SDK Import Helper
==========================================
Imports Agent, AgentRuntime, and messaging primitives from the vendored
autogen fork at vendor/autogen/python/packages/autogen-core/src.

Problem:
    AutoGen's package structure requires proper path setup for imports.
    The vendored fork needs explicit path handling.

Solution:
    sys.path manipulation to import from vendor/autogen submodule.

Usage:
    from slate.vendor_autogen_sdk import (
        Agent, BaseAgent, AgentRuntime,
        AgentId, AgentType, AgentProxy,
        MessageContext, TopicId,
        SDK_AVAILABLE,
    )

Integration Points:
    - slate_unified_autonomous.py: Multi-agent conversation loops
    - slate/guided_workflow.py: Agent-based task execution
    - slate/action_guard.py: Guardrail integration
"""

import sys
from pathlib import Path
from typing import Any, Optional

WORKSPACE_ROOT = Path(__file__).parent.parent.resolve()
AUTOGEN_CORE_SRC = WORKSPACE_ROOT / "vendor" / "autogen" / "python" / "packages" / "autogen-core" / "src"
AUTOGEN_AGENTCHAT_SRC = WORKSPACE_ROOT / "vendor" / "autogen" / "python" / "packages" / "autogen-agentchat" / "src"

# Sentinel for SDK availability
SDK_AVAILABLE = False

# Core types - populated by _import_sdk()
Agent: Any = None
BaseAgent: Any = None
AgentRuntime: Any = None
AgentId: Any = None
AgentType: Any = None
AgentProxy: Any = None
ClosureAgent: Any = None
ClosureContext: Any = None
MessageContext: Any = None
TopicId: Any = None
Subscription: Any = None
DefaultSubscription: Any = None
CancellationToken: Any = None

# AgentChat types (higher-level abstractions)
AssistantAgent: Any = None
UserProxyAgent: Any = None
GroupChat: Any = None
GroupChatManager: Any = None


def _import_sdk() -> bool:
    """
    Import autogen SDK classes using sys.path manipulation.

    Returns True if successful, False otherwise.
    """
    global SDK_AVAILABLE
    global Agent, BaseAgent, AgentRuntime, AgentId, AgentType, AgentProxy
    global ClosureAgent, ClosureContext, MessageContext, TopicId
    global Subscription, DefaultSubscription, CancellationToken
    global AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager

    if not AUTOGEN_CORE_SRC.exists():
        return False

    # Store original state
    original_path = sys.path.copy()
    stashed_modules = {}

    try:
        # Stash any conflicting modules
        for mod_name in list(sys.modules.keys()):
            if mod_name.startswith("autogen"):
                stashed_modules[mod_name] = sys.modules.pop(mod_name)

        # Add vendor paths
        sys.path.insert(0, str(AUTOGEN_CORE_SRC))
        if AUTOGEN_AGENTCHAT_SRC.exists():
            sys.path.insert(0, str(AUTOGEN_AGENTCHAT_SRC))

        # Mock the version metadata lookup to prevent PackageNotFoundError
        import importlib.metadata
        _original_version = importlib.metadata.version
        def _mock_version(name):
            if name in ("autogen_core", "autogen_agentchat", "autogen-core", "autogen-agentchat"):
                return "0.4.0.dev0"  # Return dev version for vendored SDK
            return _original_version(name)
        importlib.metadata.version = _mock_version

        # Import core types directly from submodules to avoid __init__.py metadata issues
        from autogen_core._agent import Agent as _Agent
        from autogen_core._agent_id import AgentId as _AgentId
        from autogen_core._agent_type import AgentType as _AgentType
        from autogen_core._agent_proxy import AgentProxy as _AgentProxy
        from autogen_core._message_context import MessageContext as _MessageContext
        from autogen_core._topic import TopicId as _TopicId
        from autogen_core._subscription import Subscription as _Subscription
        from autogen_core._default_subscription import DefaultSubscription as _DefaultSubscription
        from autogen_core._cancellation_token import CancellationToken as _CancellationToken

        Agent = _Agent
        AgentId = _AgentId
        AgentType = _AgentType
        AgentProxy = _AgentProxy
        MessageContext = _MessageContext
        TopicId = _TopicId
        Subscription = _Subscription
        DefaultSubscription = _DefaultSubscription
        CancellationToken = _CancellationToken

        # Try to import BaseAgent and runtime
        try:
            from autogen_core._base_agent import BaseAgent as _BaseAgent
            from autogen_core._agent_runtime import AgentRuntime as _AgentRuntime
            from autogen_core._closure_agent import ClosureAgent as _ClosureAgent, ClosureContext as _ClosureContext
            BaseAgent = _BaseAgent
            AgentRuntime = _AgentRuntime
            ClosureAgent = _ClosureAgent
            ClosureContext = _ClosureContext
        except ImportError:
            pass

        # Try to import AgentChat types (optional)
        try:
            from autogen_agentchat.agents import AssistantAgent as _AssistantAgent
            from autogen_agentchat.agents import UserProxyAgent as _UserProxyAgent
            from autogen_agentchat.teams import RoundRobinGroupChat as _GroupChat
            AssistantAgent = _AssistantAgent
            UserProxyAgent = _UserProxyAgent
            GroupChat = _GroupChat
        except ImportError:
            pass

        SDK_AVAILABLE = True
        return True

    except Exception as e:
        import logging
        logging.getLogger(__name__).debug(f"AutoGen SDK import failed: {e}")
        return False

    finally:
        # Restore original state
        sys.path = original_path
        for mod_name, mod in stashed_modules.items():
            sys.modules[mod_name] = mod


def get_sdk_status() -> dict:
    """Get status of AutoGen SDK integration."""
    return {
        "available": SDK_AVAILABLE,
        "core_path": str(AUTOGEN_CORE_SRC),
        "core_exists": AUTOGEN_CORE_SRC.exists(),
        "agentchat_path": str(AUTOGEN_AGENTCHAT_SRC),
        "agentchat_exists": AUTOGEN_AGENTCHAT_SRC.exists(),
        "types_loaded": {
            "Agent": Agent is not None,
            "BaseAgent": BaseAgent is not None,
            "AgentRuntime": AgentRuntime is not None,
            "ClosureAgent": ClosureAgent is not None,
            "AssistantAgent": AssistantAgent is not None,
        }
    }


def create_slate_agent(
    name: str,
    description: str,
    handler: Any,
    subscriptions: Optional[list] = None
) -> Optional[Any]:
    """
    Create a SLATE-compatible AutoGen agent.

    Args:
        name: Agent name
        description: Agent description
        handler: Async message handler function
        subscriptions: Optional list of topic subscriptions

    Returns:
        ClosureAgent instance or None if SDK unavailable
    """
    if not SDK_AVAILABLE or ClosureAgent is None:
        return None

    try:
        agent = ClosureAgent(
            description=description,
            closure=handler,
        )
        return agent
    except Exception:
        return None


# Initialize on import
_import_sdk()


if __name__ == "__main__":
    import json
    status = get_sdk_status()
    print("AutoGen SDK Status:")
    print(json.dumps(status, indent=2))
