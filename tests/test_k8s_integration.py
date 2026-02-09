# tests/test_k8s_integration.py

import asyncio
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
    service = SlateService(name="test", service_name="test-svc", port=80, health_endpoint="/health")
    assert service.name == "test"
    assert service.service_name == "test-svc"
    assert service.port == 80
    assert service.health_endpoint == "/health"
    assert service.url == "http://test-svc:80"
    assert service.health_url == "http://test-svc:80/health"

# Test SlateK8sIntegration discovery_services method with mock subprocess.run
async def test_discover_services(mock_subprocess):
    mock_subprocess.return_value.stdout = b'{"services": [{"name": "test", ' \
                                         b'"service_name": "test-svc", "port": 80}]}'
    k8s = SlateK8sIntegration()
    services = await k8s.discover_services()
    assert len(services) == 1
    assert services[0].name == "test"
    assert services[0].service_name == "test-svc"
    assert services[0].port == 80

# Test SlateK8sIntegration check_all_services method with mock urllib.request.urlopen and error handling
async def test_check_all_services_health(k8s_integration, mock_urllib_error):
    k8s = k8s_integration
    services = DEFAULT_SERVICES
    health_results = await k8s.check_all_services(services)
    assert len(health_results) == len(services)
    for health in health_results:
        assert health.error == "mock error"
        assert health.status == ServiceStatus.UNHEALTHY

# Test SlateK8sIntegration check_all_services method with healthy services
async def test_check_all_services_healthy(k8s_integration, mock_urllib_error):
    k8s = k8s_integration
    services = DEFAULT_SERVICES
    mock_urllib_error.side_effect = None  # Remove error for this test
    health_results = await k8s.check_all_services(services)
    assert len(health_results) == len(services)
    for health in health_results:
        assert health.error is None
        assert health.status in (ServiceStatus.HEALTHY, ServiceStatus.DEGRADED)

# Test SlateK8sIntegration get_pod_status method with mock subprocess.run and expected output
def test_get_pod_status(mock_subprocess):
    mock_subprocess.return_value.stdout = b'{"status": {"phase": "Running"}}'
    k8s = SlateK8sIntegration()
    pod_status = k8s.get_pod_status("test-pod")
    assert pod_status == "Running"