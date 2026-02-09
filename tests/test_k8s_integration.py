# Modified: 2026-02-10T12:00:00Z | Author: COPILOT | Change: Fix tests — remove nonexistent discover_services/get_pod_status, use actual API
# tests/test_k8s_integration.py

import asyncio
import urllib.error
import pytest
from unittest.mock import patch, MagicMock
from slate.k8s_integration import (
    ServiceStatus,
    ServiceHealth,
    SlateService,
    DEFAULT_SERVICES,
    SlateK8sIntegration,
)

@pytest.fixture
def mock_subprocess():
    with patch('subprocess.run') as mock_run:
        yield mock_run

@pytest.fixture
def mock_urllib_error():
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.side_effect = urllib.error.URLError("mock error")
        yield mock_urlopen

@pytest.fixture
def k8s_integration():
    return SlateK8sIntegration()

# Test ServiceHealth initialization and properties
def test_service_health_init():
    health = ServiceHealth(name="test", status=ServiceStatus.HEALTHY, url="http://example.com")
    assert health.name == "test"
    assert health.status == ServiceStatus.HEALTHY
    assert health.url == "http://example.com"
    assert health.latency_ms == 0.0
    assert health.last_check == ""
    assert health.error is None

# Test SlateService initialization and properties
def test_slate_service_init():
    service = SlateService(name="test", service_name="test-svc", port=80, health_endpoint="/health", description="Test service")
    assert service.name == "test"
    assert service.service_name == "test-svc"
    assert service.port == 80
    assert service.health_endpoint == "/health"
    assert service.url == "http://test-svc:80"
    assert service.health_url == "http://test-svc:80/health"

# Test get_pod_info returns dict
def test_get_pod_info(k8s_integration, mock_subprocess):
    mock_subprocess.return_value.stdout = '{"status": {"phase": "Running"}}'
    mock_subprocess.return_value.returncode = 0
    result = k8s_integration.get_pod_info()
    assert isinstance(result, dict)

# Test is_k8s_environment
def test_is_k8s_environment(k8s_integration):
    result = k8s_integration.is_k8s_environment()
    assert isinstance(result, bool)

# Test get_integration_status returns expected keys
def test_get_integration_status(k8s_integration):
    result = k8s_integration.get_integration_status()
    assert isinstance(result, dict)
    assert "environment" in result
    assert "services" in result