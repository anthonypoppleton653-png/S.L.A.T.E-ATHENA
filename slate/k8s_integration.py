#!/usr/bin/env python3
# Modified: 2026-02-08T12:00:00Z | Author: Claude Opus 4.5 | Change: Create K8s integration module for SLATE Dashboard
# Modified: 2026-02-09T10:00:00Z | Author: COPILOT | Change: Add kubectl-based introspection, instruction-controller service, GPU device plugin detection, deployment rollout status
"""
SLATE Kubernetes Integration Module
====================================

Provides Kubernetes-aware service discovery, health monitoring, and
integration management for the SLATE Dashboard when running in K8s.

Features:
- Automatic service discovery via K8s DNS
- Health monitoring for all SLATE services
- Pod/deployment status introspection via kubectl
- ConfigMap watching for adaptive instructions
- GPU device plugin detection
- Environment-aware configuration

Usage:
    from slate.k8s_integration import get_k8s_integration, SlateK8sIntegration

    k8s = get_k8s_integration()
    if k8s.is_k8s_environment():
        services = await k8s.discover_services()
        health = await k8s.check_all_services()
"""

import asyncio
import json
import logging
import os
import subprocess
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from enum import Enum

# Modified: 2026-02-09T10:00:00Z | Author: COPILOT | Change: Add logger initialization
logger = logging.getLogger("slate.k8s_integration")

__all__ = [
    "SlateK8sIntegration",
    "get_k8s_integration",
    "ServiceHealth",
    "SlateService",
]


class ServiceStatus(Enum):
    """Service health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ServiceHealth:
    """Health status for a SLATE service."""
    name: str
    status: ServiceStatus
    url: str
    latency_ms: float = 0.0
    last_check: str = ""
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SlateService:
    """SLATE service definition for K8s environment."""
    name: str
    service_name: str  # K8s service DNS name
    port: int
    health_endpoint: str
    description: str
    required: bool = True
    protocol: str = "http"

    @property
    def url(self) -> str:
        """Get the full service URL."""
        return f"{self.protocol}://{self.service_name}:{self.port}"

    @property
    def health_url(self) -> str:
        """Get the health check URL."""
        return f"{self.url}{self.health_endpoint}"


# Default SLATE services in Kubernetes
DEFAULT_SERVICES = [
    SlateService(
        name="ollama",
        service_name="ollama-svc",
        port=11434,
        health_endpoint="/api/tags",
        description="Ollama LLM inference service",
        required=True,
    ),
    SlateService(
        name="chromadb",
        service_name="chromadb-svc",
        port=8000,
        health_endpoint="/api/v2/heartbeat",
        description="ChromaDB vector store",
        required=False,
    ),
    SlateService(
        name="dashboard",
        service_name="slate-dashboard-svc",
        port=8080,
        health_endpoint="/health",
        description="SLATE Dashboard UI",
        required=True,
    ),
    SlateService(
        name="agent-router",
        service_name="slate-agent-router-svc",
        port=8081,
        health_endpoint="/health",
        description="Agent routing service",
        required=False,
    ),
    SlateService(
        name="autonomous",
        service_name="slate-autonomous-svc",
        port=8082,
        health_endpoint="/health",
        description="Autonomous loop service",
        required=False,
    ),
    SlateService(
        name="copilot-bridge",
        service_name="slate-copilot-bridge-svc",
        port=8083,
        health_endpoint="/health",
        description="Copilot bridge service",
        required=False,
    ),
    SlateService(
        name="workflow",
        service_name="slate-workflow-svc",
        port=8084,
        health_endpoint="/health",
        description="Workflow manager service",
        required=False,
    ),
    # Modified: 2026-02-09T10:00:00Z | Author: COPILOT | Change: Add instruction-controller and metrics services
    SlateService(
        name="instruction-controller",
        service_name="slate-instruction-controller-svc",
        port=8085,
        health_endpoint="/health",
        description="Adaptive instruction controller",
        required=False,
    ),
    SlateService(
        name="metrics",
        service_name="slate-metrics-svc",
        port=9090,
        health_endpoint="/metrics",
        description="SLATE metrics endpoint",
        required=False,
    ),
]


class SlateK8sIntegration:
    """
    Kubernetes integration for SLATE Dashboard.

    Provides service discovery, health monitoring, and K8s-aware configuration.
    """

    def __init__(self, services: Optional[List[SlateService]] = None):
        """
        Initialize K8s integration.

        Args:
            services: List of SLATE services to monitor. Defaults to all services.
        """
        self.services = services or DEFAULT_SERVICES
        self._health_cache: Dict[str, ServiceHealth] = {}
        self._cache_ttl_seconds = 30
        self._last_check: Optional[datetime] = None

    def is_k8s_environment(self) -> bool:
        """Check if running inside Kubernetes."""
        # Check for K8s environment indicators
        return any([
            os.environ.get("SLATE_K8S") == "true",
            os.environ.get("KUBERNETES_SERVICE_HOST") is not None,
            Path("/var/run/secrets/kubernetes.io/serviceaccount/token").exists(),
        ])

    def get_pod_info(self) -> Dict[str, str]:
        """Get current pod information from environment."""
        return {
            "name": os.environ.get("POD_NAME", "unknown"),
            "namespace": os.environ.get("POD_NAMESPACE", "slate"),
            "ip": os.environ.get("POD_IP", "unknown"),
            "node": os.environ.get("NODE_NAME", "unknown"),
        }

    def get_service_url(self, service_name: str) -> Optional[str]:
        """
        Get URL for a SLATE service.

        Uses environment variable override if available, otherwise K8s DNS.

        Args:
            service_name: Name of the service (e.g., "ollama", "chromadb")

        Returns:
            Service URL or None if not found
        """
        # Check for environment variable override
        env_key = f"{service_name.upper().replace('-', '_')}_HOST"
        if env_value := os.environ.get(env_key):
            return env_value

        # Find service in registry
        for service in self.services:
            if service.name == service_name:
                return service.url

        return None

    async def check_service_health(
        self,
        service: SlateService,
        timeout: float = 5.0,
    ) -> ServiceHealth:
        """
        Check health of a single service.

        Args:
            service: Service to check
            timeout: Request timeout in seconds

        Returns:
            ServiceHealth with status and latency
        """
        import time

        start = time.monotonic()
        url = self.get_service_url(service.name) or service.url
        health_url = f"{url}{service.health_endpoint}"

        try:
            req = urllib.request.Request(health_url, method="GET")
            req.add_header("User-Agent", "SLATE-K8s-Integration/1.0")

            # Run blocking request in thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: urllib.request.urlopen(req, timeout=timeout)
            )

            latency = (time.monotonic() - start) * 1000

            if response.status == 200:
                # Try to parse response for metadata
                try:
                    data = json.loads(response.read().decode())
                    metadata = data if isinstance(data, dict) else {"response": data}
                except Exception:
                    metadata = {}

                return ServiceHealth(
                    name=service.name,
                    status=ServiceStatus.HEALTHY,
                    url=url,
                    latency_ms=latency,
                    last_check=datetime.now(timezone.utc).isoformat(),
                    metadata=metadata,
                )
            else:
                return ServiceHealth(
                    name=service.name,
                    status=ServiceStatus.DEGRADED,
                    url=url,
                    latency_ms=latency,
                    last_check=datetime.now(timezone.utc).isoformat(),
                    error=f"HTTP {response.status}",
                )

        except urllib.error.URLError as e:
            latency = (time.monotonic() - start) * 1000
            return ServiceHealth(
                name=service.name,
                status=ServiceStatus.UNHEALTHY,
                url=url,
                latency_ms=latency,
                last_check=datetime.now(timezone.utc).isoformat(),
                error=str(e.reason),
            )
        except Exception as e:
            latency = (time.monotonic() - start) * 1000
            return ServiceHealth(
                name=service.name,
                status=ServiceStatus.UNKNOWN,
                url=url,
                latency_ms=latency,
                last_check=datetime.now(timezone.utc).isoformat(),
                error=str(e),
            )

    async def check_all_services(
        self,
        use_cache: bool = True,
    ) -> Dict[str, ServiceHealth]:
        """
        Check health of all SLATE services concurrently.

        Args:
            use_cache: Whether to use cached results if within TTL

        Returns:
            Dictionary of service name -> ServiceHealth
        """
        # Check cache
        if use_cache and self._last_check:
            age = (datetime.now(timezone.utc) - self._last_check).total_seconds()
            if age < self._cache_ttl_seconds:
                return self._health_cache

        # Run all health checks concurrently
        tasks = [
            self.check_service_health(service)
            for service in self.services
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Update cache
        self._health_cache = {}
        for service, result in zip(self.services, results):
            if isinstance(result, Exception):
                self._health_cache[service.name] = ServiceHealth(
                    name=service.name,
                    status=ServiceStatus.UNKNOWN,
                    url=service.url,
                    error=str(result),
                    last_check=datetime.now(timezone.utc).isoformat(),
                )
            else:
                self._health_cache[service.name] = result

        self._last_check = datetime.now(timezone.utc)
        return self._health_cache

    def get_integration_status(self) -> Dict[str, Any]:
        """
        Get overall integration status.

        Returns:
            Dictionary with environment info, services, and health summary
        """
        is_k8s = self.is_k8s_environment()

        return {
            "environment": "kubernetes" if is_k8s else "local",
            "pod": self.get_pod_info() if is_k8s else None,
            "services": {
                svc.name: {
                    "url": self.get_service_url(svc.name) or svc.url,
                    "required": svc.required,
                    "description": svc.description,
                }
                for svc in self.services
            },
            "health_cache_age": (
                (datetime.now(timezone.utc) - self._last_check).total_seconds()
                if self._last_check else None
            ),
        }

    async def get_full_status(self) -> Dict[str, Any]:
        """
        Get full status including health checks and cluster introspection.

        Returns:
            Complete status with all service health and K8s cluster state
        """
        health = await self.check_all_services()

        healthy_count = sum(
            1 for h in health.values()
            if h.status == ServiceStatus.HEALTHY
        )
        required_healthy = all(
            health.get(svc.name, ServiceHealth(svc.name, ServiceStatus.UNKNOWN, "")).status == ServiceStatus.HEALTHY
            for svc in self.services
            if svc.required
        )

        result = {
            "environment": "kubernetes" if self.is_k8s_environment() else "local",
            "pod": self.get_pod_info() if self.is_k8s_environment() else None,
            "summary": {
                "total_services": len(self.services),
                "healthy": healthy_count,
                "degraded": sum(1 for h in health.values() if h.status == ServiceStatus.DEGRADED),
                "unhealthy": sum(1 for h in health.values() if h.status == ServiceStatus.UNHEALTHY),
                "all_required_healthy": required_healthy,
            },
            "services": {
                name: {
                    "status": h.status.value,
                    "url": h.url,
                    "latency_ms": h.latency_ms,
                    "last_check": h.last_check,
                    "error": h.error,
                    "metadata": h.metadata,
                }
                for name, h in health.items()
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Enrich with kubectl cluster data if available
        cluster = self.get_cluster_status()
        if cluster:
            result["cluster"] = cluster

        return result

    # ─────────────────────────────────────────────────────────────────────────
    # Modified: 2026-02-09T10:00:00Z | Author: COPILOT | Change: Add kubectl-based cluster introspection methods
    # ─────────────────────────────────────────────────────────────────────────

    def _kubectl(self, *args: str, timeout: int = 10) -> Optional[str]:
        """Run a kubectl command and return stdout, or None on failure."""
        try:
            result = subprocess.run(
                ["kubectl", *args],
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
            )
            if result.returncode == 0:
                return result.stdout.strip()
            logger.debug(f"kubectl {' '.join(args)} failed: {result.stderr}")
            return None
        except FileNotFoundError:
            logger.debug("kubectl not found")
            return None
        except subprocess.TimeoutExpired:
            logger.debug(f"kubectl {' '.join(args)} timed out")
            return None
        except Exception as e:
            logger.debug(f"kubectl error: {e}")
            return None

    def _kubectl_json(self, *args: str) -> Optional[Dict[str, Any]]:
        """Run kubectl with -o json and parse result."""
        output = self._kubectl(*args, "-o", "json")
        if output:
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                return None
        return None

    def get_cluster_status(self) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive K8s cluster status via kubectl.

        Returns:
            Dict with deployments, pods, cronjobs, pvcs, gpu info — or None if kubectl unavailable
        """
        # Test kubectl availability
        version = self._kubectl("version", "--client", "--short")
        if version is None:
            return None

        return {
            "kubectl_version": version,
            "deployments": self._get_deployments(),
            "pods": self._get_pods(),
            "cronjobs": self._get_cronjobs(),
            "pvcs": self._get_pvcs(),
            "configmaps": self._get_configmaps(),
            "gpu": self._detect_gpu_plugin(),
            "events": self._get_recent_events(),
        }

    def _get_deployments(self) -> List[Dict[str, Any]]:
        """Get all SLATE deployments with rollout status."""
        data = self._kubectl_json("get", "deployments", "-n", "slate")
        if not data or "items" not in data:
            return []

        deployments = []
        for dep in data["items"]:
            name = dep.get("metadata", {}).get("name", "unknown")
            spec = dep.get("spec", {})
            status = dep.get("status", {})

            desired = spec.get("replicas", 0)
            ready = status.get("readyReplicas", 0)
            updated = status.get("updatedReplicas", 0)
            available = status.get("availableReplicas", 0)

            # Determine rollout status
            if ready == desired and updated == desired:
                rollout = "complete"
            elif updated < desired:
                rollout = "progressing"
            elif ready < desired:
                rollout = "degraded"
            else:
                rollout = "unknown"

            # Get image
            containers = spec.get("template", {}).get("spec", {}).get("containers", [])
            image = containers[0].get("image", "unknown") if containers else "unknown"

            deployments.append({
                "name": name,
                "image": image,
                "replicas": {"desired": desired, "ready": ready, "updated": updated, "available": available},
                "rollout": rollout,
            })

        return deployments

    def _get_pods(self) -> List[Dict[str, Any]]:
        """Get all SLATE pods with status details."""
        data = self._kubectl_json("get", "pods", "-n", "slate")
        if not data or "items" not in data:
            return []

        pods = []
        for pod in data["items"]:
            name = pod.get("metadata", {}).get("name", "unknown")
            status = pod.get("status", {})
            phase = status.get("phase", "Unknown")

            # Container statuses
            container_statuses = status.get("containerStatuses", [])
            restarts = sum(cs.get("restartCount", 0) for cs in container_statuses)
            ready_containers = sum(1 for cs in container_statuses if cs.get("ready", False))
            total_containers = len(container_statuses)

            # Check for crash loops
            crash_loop = any(
                cs.get("state", {}).get("waiting", {}).get("reason") == "CrashLoopBackOff"
                for cs in container_statuses
            )

            pods.append({
                "name": name,
                "phase": phase,
                "ready": f"{ready_containers}/{total_containers}",
                "restarts": restarts,
                "crash_loop": crash_loop,
                "node": pod.get("spec", {}).get("nodeName", "unknown"),
            })

        return pods

    def _get_cronjobs(self) -> List[Dict[str, Any]]:
        """Get CronJob status — schedules, last run, active jobs."""
        data = self._kubectl_json("get", "cronjobs", "-n", "slate")
        if not data or "items" not in data:
            return []

        cronjobs = []
        for cj in data["items"]:
            name = cj.get("metadata", {}).get("name", "unknown")
            spec = cj.get("spec", {})
            status = cj.get("status", {})

            last_schedule = status.get("lastScheduleTime")
            active = len(status.get("active", []))

            cronjobs.append({
                "name": name,
                "schedule": spec.get("schedule", "unknown"),
                "suspend": spec.get("suspend", False),
                "last_schedule": last_schedule,
                "active_jobs": active,
            })

        return cronjobs

    def _get_pvcs(self) -> List[Dict[str, Any]]:
        """Get PersistentVolumeClaim status."""
        data = self._kubectl_json("get", "pvc", "-n", "slate")
        if not data or "items" not in data:
            return []

        pvcs = []
        for pvc in data["items"]:
            name = pvc.get("metadata", {}).get("name", "unknown")
            status = pvc.get("status", {})
            spec = pvc.get("spec", {})

            capacity = status.get("capacity", {}).get("storage", "unknown")
            access = spec.get("accessModes", [])

            pvcs.append({
                "name": name,
                "status": status.get("phase", "Unknown"),
                "capacity": capacity,
                "access_modes": access,
                "storage_class": spec.get("storageClassName", "default"),
            })

        return pvcs

    def _get_configmaps(self) -> List[Dict[str, Any]]:
        """Get ConfigMap names and key counts in slate namespace."""
        data = self._kubectl_json("get", "configmaps", "-n", "slate")
        if not data or "items" not in data:
            return []

        cms = []
        for cm in data["items"]:
            name = cm.get("metadata", {}).get("name", "unknown")
            # Skip kube-root-ca.crt
            if name == "kube-root-ca.crt":
                continue
            data_keys = list(cm.get("data", {}).keys())
            cms.append({
                "name": name,
                "keys": data_keys,
                "key_count": len(data_keys),
            })

        return cms

    def _detect_gpu_plugin(self) -> Dict[str, Any]:
        """Detect NVIDIA GPU device plugin and GPU availability."""
        # Check for NVIDIA device plugin DaemonSet
        ds = self._kubectl_json("get", "daemonset", "-n", "kube-system", "-l", "app=nvidia-device-plugin")

        gpu_plugin_present = False
        if ds and ds.get("items"):
            gpu_plugin_present = True

        # Check nodes for GPU capacity
        nodes = self._kubectl_json("get", "nodes")
        gpu_nodes = []
        if nodes and "items" in nodes:
            for node in nodes["items"]:
                capacity = node.get("status", {}).get("capacity", {})
                gpu_count = capacity.get("nvidia.com/gpu", "0")
                if int(gpu_count) > 0:
                    gpu_nodes.append({
                        "name": node.get("metadata", {}).get("name", "unknown"),
                        "gpu_count": int(gpu_count),
                    })

        return {
            "device_plugin_installed": gpu_plugin_present,
            "gpu_nodes": gpu_nodes,
            "total_gpus": sum(n["gpu_count"] for n in gpu_nodes),
        }

    def _get_recent_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent warning events in the slate namespace."""
        data = self._kubectl_json(
            "get", "events", "-n", "slate",
            "--field-selector", "type=Warning",
            "--sort-by", ".lastTimestamp"
        )
        if not data or "items" not in data:
            return []

        events = []
        for event in data["items"][-limit:]:
            events.append({
                "reason": event.get("reason", "unknown"),
                "message": event.get("message", "")[:200],
                "count": event.get("count", 1),
                "object": event.get("involvedObject", {}).get("name", "unknown"),
                "last_seen": event.get("lastTimestamp"),
            })

        return events

    def get_instruction_state(self) -> Optional[Dict[str, Any]]:
        """
        Read adaptive instruction state from ConfigMap.

        Returns:
            Dict with active-state, copilot-rules, mode — from K8s ConfigMap
        """
        data = self._kubectl_json(
            "get", "configmap", "slate-instructions", "-n", "slate"
        )
        if not data or "data" not in data:
            return None

        cm_data = data["data"]
        return {
            "active_state": cm_data.get("active-state.yaml"),
            "instruction_block": cm_data.get("instruction-block.md"),
            "copilot_rules": cm_data.get("copilot-rules.yaml"),
            "agent_prompts": cm_data.get("agent-prompts.yaml") is not None,
            "mcp_tools": cm_data.get("mcp-tools.yaml") is not None,
            "key_count": len(cm_data),
        }

    def rollout_status(self, deployment: str) -> Optional[str]:
        """Get rollout status for a deployment."""
        return self._kubectl("rollout", "status", f"deployment/{deployment}", "-n", "slate", "--timeout=10s")

    def restart_deployment(self, deployment: str) -> bool:
        """Restart a deployment via rollout restart."""
        result = self._kubectl("rollout", "restart", f"deployment/{deployment}", "-n", "slate")
        return result is not None

    def scale_deployment(self, deployment: str, replicas: int) -> bool:
        """Scale a deployment to the specified number of replicas."""
        result = self._kubectl("scale", f"deployment/{deployment}", f"--replicas={replicas}", "-n", "slate")
        return result is not None

    def get_pod_logs(self, pod_name: str, tail: int = 50) -> Optional[str]:
        """Get recent logs from a pod."""
        return self._kubectl("logs", pod_name, "-n", "slate", f"--tail={tail}")

    def apply_manifest(self, path: str) -> bool:
        """Apply a K8s manifest file."""
        result = self._kubectl("apply", "-f", path)
        return result is not None

    def apply_kustomize(self, path: str = "k8s/overlays/local/") -> bool:
        """Apply Kustomize overlay."""
        result = self._kubectl("apply", "-k", path)
        return result is not None

    # Modified: 2026-02-08T18:00:00Z | Author: Claude Opus 4.5 | Change: Add ConfigMap reading capability
    def read_configmap(
        self,
        name: str,
        mount_path: Optional[Path] = None,
    ) -> Optional[Dict[str, str]]:
        """
        Read a ConfigMap's data from mounted volume.

        In Kubernetes, ConfigMaps are mounted as directories where each key
        becomes a file. This method reads all files from the mount path.

        Args:
            name: ConfigMap name (used for logging/identification)
            mount_path: Path where ConfigMap is mounted (default: /config/{name})

        Returns:
            Dict mapping filenames to content, or None if not found/readable
        """
        if mount_path is None:
            mount_path = Path(f"/config/{name}")

        if not mount_path.exists():
            logger.debug(f"ConfigMap mount not found: {mount_path}")
            return None

        if not mount_path.is_dir():
            logger.warning(f"ConfigMap path is not a directory: {mount_path}")
            return None

        try:
            data: Dict[str, str] = {}
            for file_path in mount_path.iterdir():
                if file_path.is_file():
                    try:
                        data[file_path.name] = file_path.read_text(encoding="utf-8")
                    except Exception as e:
                        logger.warning(f"Could not read ConfigMap file {file_path}: {e}")

            logger.debug(f"Read ConfigMap '{name}' with {len(data)} entries")
            return data if data else None

        except Exception as e:
            logger.error(f"Error reading ConfigMap '{name}': {e}")
            return None

    def read_configmap_key(
        self,
        name: str,
        key: str,
        mount_path: Optional[Path] = None,
    ) -> Optional[str]:
        """
        Read a single key from a ConfigMap.

        Args:
            name: ConfigMap name
            key: Key (filename) to read
            mount_path: Path where ConfigMap is mounted

        Returns:
            Content of the key, or None if not found
        """
        data = self.read_configmap(name, mount_path)
        if data:
            return data.get(key)
        return None


# Singleton instance
_integration: Optional[SlateK8sIntegration] = None


def get_k8s_integration() -> SlateK8sIntegration:
    """Get the singleton K8s integration instance."""
    global _integration
    if _integration is None:
        _integration = SlateK8sIntegration()
    return _integration


# ─────────────────────────────────────────────────────────────────────────────
# CLI Interface
# ─────────────────────────────────────────────────────────────────────────────

async def main():
    """CLI entry point for testing K8s integration."""
    import argparse

    parser = argparse.ArgumentParser(description="SLATE K8s Integration")
    parser.add_argument("--status", action="store_true", help="Show integration status")
    parser.add_argument("--health", action="store_true", help="Check all service health")
    parser.add_argument("--cluster", action="store_true", help="Show cluster status via kubectl")
    parser.add_argument("--deployments", action="store_true", help="Show deployment rollout status")
    parser.add_argument("--pods", action="store_true", help="Show pod status")
    parser.add_argument("--instructions", action="store_true", help="Show instruction ConfigMap state")
    parser.add_argument("--gpu", action="store_true", help="Show GPU device plugin status")
    parser.add_argument("--events", action="store_true", help="Show recent warning events")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    integration = get_k8s_integration()

    if args.cluster or args.deployments or args.pods or args.instructions or args.gpu or args.events:
        # kubectl-based introspection
        if args.json:
            if args.cluster:
                data = integration.get_cluster_status()
            elif args.instructions:
                data = integration.get_instruction_state()
            elif args.gpu:
                data = integration._detect_gpu_plugin()
            elif args.deployments:
                data = integration._get_deployments()
            elif args.pods:
                data = integration._get_pods()
            elif args.events:
                data = integration._get_recent_events()
            else:
                data = integration.get_cluster_status()
            print(json.dumps(data, indent=2, default=str))
        else:
            cluster = integration.get_cluster_status()
            if cluster is None:
                print("[-] kubectl not available or not configured")
                return

            print("\n╔══════════════════════════════════════════════════════════════╗")
            print("║            SLATE Kubernetes Cluster Status                   ║")
            print("╚══════════════════════════════════════════════════════════════╝\n")

            print(f"kubectl: {cluster.get('kubectl_version', 'unknown')}\n")

            # Deployments
            if not args.pods and not args.instructions and not args.gpu and not args.events:
                deployments = cluster.get("deployments", [])
                print(f"Deployments ({len(deployments)}):")
                for dep in deployments:
                    r = dep["replicas"]
                    icon = "✓" if dep["rollout"] == "complete" else "↻" if dep["rollout"] == "progressing" else "✗"
                    print(f"  {icon} {dep['name']}: {r['ready']}/{r['desired']} ready ({dep['image']})")

            # Pods
            if args.pods or (not args.deployments and not args.instructions and not args.gpu and not args.events):
                pods = cluster.get("pods", [])
                print(f"\nPods ({len(pods)}):")
                for pod in pods:
                    icon = "✓" if pod["phase"] == "Running" else "✓" if pod["phase"] == "Succeeded" else "✗"
                    crash = " [CRASH LOOP]" if pod.get("crash_loop") else ""
                    restart_info = f" (restarts: {pod['restarts']})" if pod["restarts"] > 0 else ""
                    print(f"  {icon} {pod['name']}: {pod['phase']} {pod['ready']}{restart_info}{crash}")

            # CronJobs
            if not args.pods and not args.instructions and not args.gpu and not args.events:
                cronjobs = cluster.get("cronjobs", [])
                print(f"\nCronJobs ({len(cronjobs)}):")
                for cj in cronjobs:
                    icon = "⏸" if cj["suspend"] else "▶"
                    last = cj.get("last_schedule", "never")
                    print(f"  {icon} {cj['name']}: {cj['schedule']} (last: {last})")

            # PVCs
            if not args.pods and not args.instructions and not args.gpu and not args.events:
                pvcs = cluster.get("pvcs", [])
                print(f"\nPVCs ({len(pvcs)}):")
                for pvc in pvcs:
                    icon = "✓" if pvc["status"] == "Bound" else "?"
                    print(f"  {icon} {pvc['name']}: {pvc['status']} ({pvc['capacity']})")

            # GPU
            if args.gpu or (not args.pods and not args.deployments and not args.instructions and not args.events):
                gpu = cluster.get("gpu", {})
                print(f"\nGPU Device Plugin:")
                print(f"  Installed: {'✓' if gpu.get('device_plugin_installed') else '✗ Not found'}")
                print(f"  Total GPUs: {gpu.get('total_gpus', 0)}")
                for node in gpu.get("gpu_nodes", []):
                    print(f"  Node {node['name']}: {node['gpu_count']} GPU(s)")

            # ConfigMaps
            if not args.pods and not args.gpu and not args.events:
                cms = cluster.get("configmaps", [])
                print(f"\nConfigMaps ({len(cms)}):")
                for cm in cms:
                    print(f"  • {cm['name']} ({cm['key_count']} keys)")

            # Instructions
            if args.instructions:
                inst = integration.get_instruction_state()
                if inst:
                    print(f"\nInstruction ConfigMap:")
                    print(f"  Keys: {inst.get('key_count', 0)}")
                    print(f"  Active state: {'✓' if inst.get('active_state') else '✗ Not set'}")
                    print(f"  Instruction block: {'✓' if inst.get('instruction_block') else '✗ Not set'}")
                    print(f"  Copilot rules: {'✓' if inst.get('copilot_rules') else '✗ Not set'}")
                    print(f"  Agent prompts: {'✓' if inst.get('agent_prompts') else '✗ Missing'}")
                    print(f"  MCP tools: {'✓' if inst.get('mcp_tools') else '✗ Missing'}")

            # Events
            if args.events or (not args.pods and not args.deployments and not args.instructions and not args.gpu):
                events = cluster.get("events", [])
                if events:
                    print(f"\nRecent Warning Events ({len(events)}):")
                    for ev in events:
                        print(f"  ⚠ {ev['reason']} on {ev['object']}: {ev['message'][:80]}")
                else:
                    print("\nNo warning events")

    elif args.health:
        status = await integration.get_full_status()
        if args.json:
            print(json.dumps(status, indent=2, default=str))
        else:
            _print_health_status(status)
    else:
        status = integration.get_integration_status()
        if args.json:
            print(json.dumps(status, indent=2, default=str))
        else:
            _print_basic_status(status)


def _print_health_status(status: Dict[str, Any]):
    """Print health status in human-readable format."""
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║           SLATE Kubernetes Integration Status                ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")

    print(f"Environment: {status.get('environment', 'unknown')}")

    if pod := status.get("pod"):
        print(f"Pod: {pod.get('name')} in {pod.get('namespace')}")
        print(f"Pod IP: {pod.get('ip')}")

    print("\nServices:")
    services = status.get("services", {})
    for name, info in services.items():
        if isinstance(info, dict):
            url = info.get("url", "unknown")
            svc_status = info.get("status", "unknown")
            latency = info.get("latency_ms", 0)
            icon = "✓" if svc_status == "healthy" else "✗" if svc_status == "unhealthy" else "?"
            print(f"  {icon} {name}: {svc_status} ({latency:.1f}ms) - {url}")

    if summary := status.get("summary"):
        print(f"\nSummary: {summary.get('healthy')}/{summary.get('total_services')} healthy")
        if summary.get("all_required_healthy"):
            print("✓ All required services healthy")
        else:
            print("✗ Some required services unhealthy")

    if cluster := status.get("cluster"):
        deploys = cluster.get("deployments", [])
        gpu = cluster.get("gpu", {})
        print(f"\nCluster: {len(deploys)} deployments, {gpu.get('total_gpus', 0)} GPUs")


def _print_basic_status(status: Dict[str, Any]):
    """Print basic status in human-readable format."""
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║           SLATE Kubernetes Integration Status                ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")

    print(f"Environment: {status.get('environment', 'unknown')}")

    if pod := status.get("pod"):
        print(f"Pod: {pod.get('name')} in {pod.get('namespace')}")

    print("\nServices:")
    services = status.get("services", {})
    for name, info in services.items():
        if isinstance(info, dict):
            url = info.get("url", "unknown")
            req = "required" if info.get("required") else "optional"
            print(f"  • {name}: {url} ({req})")


if __name__ == "__main__":
    asyncio.run(main())
