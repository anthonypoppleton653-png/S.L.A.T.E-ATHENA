# Modified: 2026-02-08T22:10:00Z | Author: COPILOT | Change: Add test coverage for slate/k8s_entrypoints.py
"""
Tests for slate/k8s_entrypoints.py — K8s service entrypoint module.
Tests focus on handler factories, SERVICES mapping, and CLI parsing
without starting real HTTP servers.
"""

import http.server
import json
import io
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestK8sEntrypointsImport:
    """Test that the module imports correctly."""

    def test_import_module(self):
        import slate.k8s_entrypoints
        assert hasattr(slate.k8s_entrypoints, 'SERVICES')
        assert hasattr(slate.k8s_entrypoints, 'main')

    def test_services_map_populated(self):
        from slate.k8s_entrypoints import SERVICES
        expected = {"core", "agent-router", "autonomous", "workflow", "dashboard"}
        assert expected == set(SERVICES.keys())

    def test_services_all_callable(self):
        from slate.k8s_entrypoints import SERVICES
        for name, func in SERVICES.items():
            assert callable(func), f"Service {name} is not callable"

    def test_version_defined(self):
        from slate.k8s_entrypoints import VERSION
        assert VERSION == "2.4.0"

    def test_workspace_env(self):
        from slate.k8s_entrypoints import WORKSPACE
        assert isinstance(WORKSPACE, str)


class TestJsonHandlerFactory:
    """Test the _json_handler_factory helper."""

    def test_factory_returns_handler_class(self):
        from slate.k8s_entrypoints import _json_handler_factory
        HandlerClass = _json_handler_factory("test-component", 8080)
        assert issubclass(HandlerClass, http.server.BaseHTTPRequestHandler)

    def test_factory_with_extra_routes(self):
        from slate.k8s_entrypoints import _json_handler_factory
        routes = {"/api/custom": lambda handler: {"custom": True}}
        HandlerClass = _json_handler_factory("test", 8080, extra_routes=routes)
        assert issubclass(HandlerClass, http.server.BaseHTTPRequestHandler)

    def test_handler_health_endpoint(self):
        from slate.k8s_entrypoints import _json_handler_factory
        HandlerClass = _json_handler_factory("test-comp", 9999)

        # Create mock request
        handler = _make_handler(HandlerClass, "GET", "/api/health")
        response = json.loads(handler._response_body)
        assert response["status"] == "ok"
        assert response["component"] == "test-comp"
        assert "version" in response
        assert "uptime" in response

    def test_handler_root_endpoint(self):
        from slate.k8s_entrypoints import _json_handler_factory
        HandlerClass = _json_handler_factory("root-test", 9999)

        handler = _make_handler(HandlerClass, "GET", "/")
        response = json.loads(handler._response_body)
        assert response["status"] == "ok"
        assert response["component"] == "root-test"

    def test_handler_status_endpoint(self):
        from slate.k8s_entrypoints import _json_handler_factory
        HandlerClass = _json_handler_factory("status-test", 9999)

        handler = _make_handler(HandlerClass, "GET", "/api/status")
        response = json.loads(handler._response_body)
        assert response["component"] == "status-test"
        assert "workspace" in response

    def test_handler_404_for_unknown_path(self):
        from slate.k8s_entrypoints import _json_handler_factory
        HandlerClass = _json_handler_factory("test", 9999)

        handler = _make_handler(HandlerClass, "GET", "/nonexistent")
        response = json.loads(handler._response_body)
        assert "error" in response
        assert handler._response_code == 404

    def test_handler_custom_route(self):
        from slate.k8s_entrypoints import _json_handler_factory

        def custom_handler(_handler):
            return {"custom": "data", "works": True}

        HandlerClass = _json_handler_factory("custom-test", 9999,
                                              extra_routes={"/api/custom": custom_handler})

        handler = _make_handler(HandlerClass, "GET", "/api/custom")
        response = json.loads(handler._response_body)
        assert response["custom"] == "data"
        assert response["works"] is True

    def test_handler_post_custom_route(self):
        from slate.k8s_entrypoints import _json_handler_factory

        def post_handler(_handler, data=None):
            return {"received": data}

        HandlerClass = _json_handler_factory("post-test", 9999,
                                              extra_routes={"/api/submit": post_handler})

        body = json.dumps({"key": "value"}).encode()
        handler = _make_handler(HandlerClass, "POST", "/api/submit", body=body)
        response = json.loads(handler._response_body)
        assert response["received"]["key"] == "value"


class TestMainCLI:
    """Test main() CLI argument parsing."""

    def test_main_requires_service(self):
        from slate.k8s_entrypoints import main
        with pytest.raises(SystemExit):
            with patch("sys.argv", ["k8s_entrypoints.py"]):
                main()

    def test_main_rejects_invalid_service(self):
        from slate.k8s_entrypoints import main
        with pytest.raises(SystemExit):
            with patch("sys.argv", ["k8s_entrypoints.py", "--service", "invalid"]):
                main()

    def test_main_calls_correct_service(self):
        from slate.k8s_entrypoints import main, SERVICES
        mock_func = MagicMock()
        with patch.dict(SERVICES, {"core": mock_func}):
            with patch("sys.argv", ["k8s_entrypoints.py", "--service", "core"]):
                main()
            mock_func.assert_called_once()


class TestRequestCounter:
    """Test that request counter increments."""

    def test_counter_increments(self):
        from slate.k8s_entrypoints import _json_handler_factory
        HandlerClass = _json_handler_factory("counter-test", 9999)

        h1 = _make_handler(HandlerClass, "GET", "/api/health")
        r1 = json.loads(h1._response_body)

        h2 = _make_handler(HandlerClass, "GET", "/api/health")
        r2 = json.loads(h2._response_body)

        assert r2["requests"] > r1["requests"]


# ── Helpers ──────────────────────────────────────────────────────────────

def _make_handler(HandlerClass, method, path, body=None):
    """Create a mock handler to test HTTP request processing."""
    handler = MagicMock(spec=HandlerClass)
    handler.path = path
    handler.headers = {"Content-Length": str(len(body)) if body else "0"}
    handler._response_body = ""
    handler._response_code = 200

    if body:
        handler.rfile = io.BytesIO(body)

    def mock_respond(code, data):
        handler._response_code = code
        handler._response_body = json.dumps(data, default=str)

    handler._respond = mock_respond
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()
    handler.wfile = io.BytesIO()

    if method == "GET":
        HandlerClass.do_GET(handler)
    elif method == "POST":
        HandlerClass.do_POST(handler)

    return handler
