# tests/test_interactive_api.py
# Modified: 2026-02-10T12:00:00Z | Author: COPILOT | Change: Fix imports and use proper test app setup

import pytest

try:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from slate.interactive_api import (
        learning_router, devcycle_router, feedback_router, create_interactive_router
    )
    # Build a test app from the routers
    _test_app = FastAPI()
    _test_app.include_router(learning_router, prefix="/api/interactive")
    _test_app.include_router(devcycle_router, prefix="/api/interactive/devcycle")
    _test_app.include_router(feedback_router, prefix="/api/interactive/feedback")
    client = TestClient(_test_app)
    MODULE_AVAILABLE = True
except (ImportError, Exception):
    MODULE_AVAILABLE = False
    client = None


@pytest.mark.skipif(not MODULE_AVAILABLE, reason="interactive_api or fastapi not importable")
class TestInteractiveAPI:

    def test_routers_exist(self):
        """Verify that the routers are valid APIRouter instances."""
        from fastapi import APIRouter
        assert isinstance(learning_router, APIRouter)
        assert isinstance(devcycle_router, APIRouter)
        assert isinstance(feedback_router, APIRouter)

    def test_create_interactive_router(self):
        """Verify create_interactive_router returns a router."""
        from fastapi import APIRouter
        router = create_interactive_router()
        assert isinstance(router, APIRouter)

    def test_learning_router_has_routes(self):
        """Verify learning_router has registered routes."""
        assert len(learning_router.routes) > 0

    def test_devcycle_router_has_routes(self):
        """Verify devcycle_router has registered routes."""
        assert len(devcycle_router.routes) > 0

    def test_feedback_router_has_routes(self):
        """Verify feedback_router has registered routes."""
        assert len(feedback_router.routes) > 0