#!/usr/bin/env python3
# Modified: 2026-02-08T15:00:00Z | Author: COPILOT | Change: Create Prometheus-compatible metrics exporter for SLATE observability
"""
SLATE Monitoring Module
========================
Prometheus-compatible metrics exporter for local AI orchestration observability.

Exposes metrics at http://127.0.0.1:9090/metrics in Prometheus text format.
Compatible with Kube-Prometheus-Stack, Grafana, and standalone Prometheus.

Features:
    - System metrics (CPU, memory, disk, GPU)
    - Service health (Ollama, ChromaDB, dashboard)
    - Inference metrics (latency, throughput, token rates)
    - Agent metrics (task counts, success rates, selection frequency)
    - Circuit breaker states
    - Availability SLO tracking

Usage:
    from slate.monitoring import MetricsExporter, start_metrics_server

    exporter = MetricsExporter()
    exporter.record_inference("slate-coder", latency=1.5, tokens=128)
    start_metrics_server(port=9090)  # Starts HTTP server on 127.0.0.1

    # Or use as CLI:
    python slate/monitoring.py --serve          # Start metrics server
    python slate/monitoring.py --status         # Show current metrics
    python slate/monitoring.py --json           # JSON metrics dump
"""

import json
import logging
import os
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Any, Optional

WORKSPACE = Path(__file__).parent.parent

log = logging.getLogger("slate.monitoring")
if not log.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
    log.addHandler(handler)
    log.setLevel(logging.INFO)


# ═══════════════════════════════════════════════════════════════════════════════
# Prometheus Metric Types
# ═══════════════════════════════════════════════════════════════════════════════

class MetricType:
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class Metric:
    """A single Prometheus-compatible metric."""
    name: str
    help_text: str
    metric_type: str
    value: float = 0.0
    labels: dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_prometheus(self) -> str:
        """Render metric in Prometheus text exposition format."""
        lines = []
        lines.append(f"# HELP {self.name} {self.help_text}")
        lines.append(f"# TYPE {self.name} {self.metric_type}")

        label_str = ""
        if self.labels:
            pairs = [f'{k}="{v}"' for k, v in sorted(self.labels.items())]
            label_str = "{" + ",".join(pairs) + "}"

        lines.append(f"{self.name}{label_str} {self.value}")
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# Metrics Registry
# ═══════════════════════════════════════════════════════════════════════════════

class MetricsRegistry:
    """Thread-safe registry of all SLATE metrics."""

    def __init__(self):
        self._metrics: dict[str, list[Metric]] = {}
        self._lock = threading.Lock()

    def register(self, name: str, help_text: str, metric_type: str) -> None:
        """Register a metric name."""
        with self._lock:
            if name not in self._metrics:
                self._metrics[name] = []

    def set_gauge(self, name: str, value: float, labels: Optional[dict] = None,
                  help_text: str = "") -> None:
        """Set a gauge metric value."""
        with self._lock:
            key = self._label_key(name, labels or {})
            self._metrics[key] = [Metric(
                name=name, help_text=help_text or name,
                metric_type=MetricType.GAUGE, value=value,
                labels=labels or {}, timestamp=time.time(),
            )]

    def inc_counter(self, name: str, value: float = 1.0, labels: Optional[dict] = None,
                    help_text: str = "") -> None:
        """Increment a counter metric."""
        with self._lock:
            key = self._label_key(name, labels or {})
            existing = self._metrics.get(key, [])
            if existing:
                existing[0].value += value
                existing[0].timestamp = time.time()
            else:
                self._metrics[key] = [Metric(
                    name=name, help_text=help_text or name,
                    metric_type=MetricType.COUNTER, value=value,
                    labels=labels or {}, timestamp=time.time(),
                )]

    def to_prometheus(self) -> str:
        """Render all metrics in Prometheus text format."""
        with self._lock:
            lines = []
            seen_headers = set()
            for metrics_list in self._metrics.values():
                for m in metrics_list:
                    header_key = m.name
                    if header_key not in seen_headers:
                        lines.append(f"# HELP {m.name} {m.help_text}")
                        lines.append(f"# TYPE {m.name} {m.metric_type}")
                        seen_headers.add(header_key)

                    label_str = ""
                    if m.labels:
                        pairs = [f'{k}="{v}"' for k, v in sorted(m.labels.items())]
                        label_str = "{" + ",".join(pairs) + "}"
                    lines.append(f"{m.name}{label_str} {m.value}")
            return "\n".join(lines) + "\n"

    def to_dict(self) -> dict:
        """Export all metrics as a dict."""
        with self._lock:
            result = {}
            for key, metrics_list in self._metrics.items():
                for m in metrics_list:
                    result[key] = {
                        "name": m.name,
                        "type": m.metric_type,
                        "value": m.value,
                        "labels": m.labels,
                    }
            return result

    @staticmethod
    def _label_key(name: str, labels: dict) -> str:
        if not labels:
            return name
        parts = sorted(f"{k}={v}" for k, v in labels.items())
        return f"{name}{{{'|'.join(parts)}}}"


# ═══════════════════════════════════════════════════════════════════════════════
# Metrics Exporter
# ═══════════════════════════════════════════════════════════════════════════════

class MetricsExporter:
    """Collects and exports SLATE system metrics.

    Usage:
        exporter = MetricsExporter()
        exporter.collect_system_metrics()  # Refresh CPU/GPU/memory
        prometheus_text = exporter.render()
    """

    def __init__(self):
        self.registry = MetricsRegistry()
        self._inference_latencies: list[float] = []
        self._lock = threading.Lock()

    # ── System Metrics ──────────────────────────────────────────────────────

    def collect_system_metrics(self) -> None:
        """Collect CPU, memory, disk, GPU metrics."""
        try:
            import psutil

            # CPU
            cpu_pct = psutil.cpu_percent(interval=0.5)
            self.registry.set_gauge(
                "slate_cpu_usage_percent", cpu_pct,
                help_text="Current CPU usage percentage"
            )
            self.registry.set_gauge(
                "slate_cpu_count", psutil.cpu_count(),
                help_text="Number of CPU cores"
            )

            # Memory
            mem = psutil.virtual_memory()
            self.registry.set_gauge(
                "slate_memory_usage_percent", mem.percent,
                help_text="Memory usage percentage"
            )
            self.registry.set_gauge(
                "slate_memory_available_bytes", mem.available,
                help_text="Available memory in bytes"
            )
            self.registry.set_gauge(
                "slate_memory_total_bytes", mem.total,
                help_text="Total memory in bytes"
            )

            # Disk
            disk = psutil.disk_usage(str(WORKSPACE))
            self.registry.set_gauge(
                "slate_disk_usage_percent", disk.percent,
                help_text="Disk usage percentage"
            )
            self.registry.set_gauge(
                "slate_disk_free_bytes", disk.free,
                help_text="Free disk space in bytes"
            )

        except ImportError:
            log.warning("psutil not available — system metrics skipped")

        # GPU metrics via nvidia-smi
        self._collect_gpu_metrics()

    def _collect_gpu_metrics(self) -> None:
        """Collect GPU metrics from nvidia-smi."""
        try:
            result = subprocess.run(
                ["nvidia-smi",
                 "--query-gpu=index,name,memory.used,memory.total,temperature.gpu,utilization.gpu,power.draw",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode != 0:
                return

            for line in result.stdout.strip().split("\n"):
                parts = [p.strip() for p in line.split(",")]
                if len(parts) < 7:
                    continue
                idx, name, mem_used, mem_total, temp, util, power = parts
                labels = {"gpu": idx, "name": name}

                self.registry.set_gauge(
                    "slate_gpu_memory_used_mb", float(mem_used), labels=labels,
                    help_text="GPU memory used in MB"
                )
                self.registry.set_gauge(
                    "slate_gpu_memory_total_mb", float(mem_total), labels=labels,
                    help_text="GPU memory total in MB"
                )
                self.registry.set_gauge(
                    "slate_gpu_temperature_celsius", float(temp), labels=labels,
                    help_text="GPU temperature in Celsius"
                )
                self.registry.set_gauge(
                    "slate_gpu_utilization_percent", float(util), labels=labels,
                    help_text="GPU utilization percentage"
                )
                try:
                    self.registry.set_gauge(
                        "slate_gpu_power_watts", float(power), labels=labels,
                        help_text="GPU power draw in watts"
                    )
                except (ValueError, IndexError):
                    pass

            self.registry.set_gauge(
                "slate_gpu_count", len(result.stdout.strip().split("\n")),
                help_text="Number of GPUs detected"
            )

        except Exception as e:
            log.debug(f"GPU metrics collection failed: {e}")

    # ── Service Health ──────────────────────────────────────────────────────

    def collect_service_metrics(self) -> None:
        """Check health of SLATE services."""
        import urllib.request

        # Ollama
        try:
            req = urllib.request.Request("http://127.0.0.1:11434/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = len(data.get("models", []))
                self.registry.set_gauge(
                    "slate_ollama_healthy", 1.0,
                    help_text="Ollama service health (1=healthy, 0=unhealthy)"
                )
                self.registry.set_gauge(
                    "slate_ollama_models_count", models,
                    help_text="Number of Ollama models available"
                )
        except Exception:
            self.registry.set_gauge("slate_ollama_healthy", 0.0,
                                    help_text="Ollama service health")

        # Dashboard
        try:
            req = urllib.request.Request("http://127.0.0.1:8080/health", method="GET")
            with urllib.request.urlopen(req, timeout=5):
                self.registry.set_gauge("slate_dashboard_healthy", 1.0,
                                        help_text="Dashboard service health")
        except Exception:
            self.registry.set_gauge("slate_dashboard_healthy", 0.0,
                                    help_text="Dashboard service health")

    # ── Inference Metrics ───────────────────────────────────────────────────

    def record_inference(self, model: str, latency: float, tokens: int = 0,
                         success: bool = True) -> None:
        """Record an inference execution."""
        labels = {"model": model}
        self.registry.inc_counter(
            "slate_inference_total", 1.0, labels=labels,
            help_text="Total inference requests"
        )

        if success:
            self.registry.inc_counter(
                "slate_inference_success_total", 1.0, labels=labels,
                help_text="Successful inference requests"
            )
        else:
            self.registry.inc_counter(
                "slate_inference_errors_total", 1.0, labels=labels,
                help_text="Failed inference requests"
            )

        self.registry.set_gauge(
            "slate_inference_latency_seconds", latency, labels=labels,
            help_text="Last inference latency in seconds"
        )

        if tokens > 0:
            tok_per_sec = tokens / max(latency, 0.001)
            self.registry.set_gauge(
                "slate_inference_tokens_per_second", tok_per_sec, labels=labels,
                help_text="Inference throughput in tokens per second"
            )
            self.registry.inc_counter(
                "slate_inference_tokens_total", float(tokens), labels=labels,
                help_text="Total tokens generated"
            )

    # ── Agent Metrics ───────────────────────────────────────────────────────

    def record_agent_task(self, agent: str, success: bool, latency: float = 0.0) -> None:
        """Record an agent task execution."""
        labels = {"agent": agent}
        self.registry.inc_counter(
            "slate_agent_tasks_total", 1.0, labels=labels,
            help_text="Total tasks processed by agent"
        )
        if success:
            self.registry.inc_counter(
                "slate_agent_tasks_success_total", 1.0, labels=labels,
                help_text="Successful tasks by agent"
            )
        self.registry.set_gauge(
            "slate_agent_last_latency_seconds", latency, labels=labels,
            help_text="Last task latency for agent"
        )

    # ── Availability ────────────────────────────────────────────────────────

    def record_availability(self, availability: float, target: float = 0.999) -> None:
        """Record availability metrics."""
        self.registry.set_gauge(
            "slate_availability_ratio", availability,
            help_text="Current system availability ratio"
        )
        self.registry.set_gauge(
            "slate_availability_target", target,
            help_text="Availability SLO target"
        )
        meets = 1.0 if availability >= target else 0.0
        self.registry.set_gauge(
            "slate_availability_slo_met", meets,
            help_text="Whether availability SLO is met (1=yes, 0=no)"
        )

    # ── Circuit Breaker ─────────────────────────────────────────────────────

    def record_circuit_breaker(self, name: str, state: str, failure_count: int) -> None:
        """Record circuit breaker state."""
        labels = {"service": name}
        state_value = {"closed": 0, "half_open": 1, "open": 2}.get(state, -1)
        self.registry.set_gauge(
            "slate_circuit_breaker_state", state_value, labels=labels,
            help_text="Circuit breaker state (0=closed, 1=half_open, 2=open)"
        )
        self.registry.set_gauge(
            "slate_circuit_breaker_failures", failure_count, labels=labels,
            help_text="Circuit breaker failure count"
        )

    # ── Render ──────────────────────────────────────────────────────────────

    def collect_all(self) -> None:
        """Collect all available metrics."""
        self.collect_system_metrics()
        try:
            self.collect_service_metrics()
        except Exception as e:
            log.debug(f"Service metrics collection failed: {e}")

    def render(self) -> str:
        """Render all metrics in Prometheus text format."""
        return self.registry.to_prometheus()

    def render_json(self) -> str:
        """Render all metrics as JSON."""
        return json.dumps(self.registry.to_dict(), indent=2, default=str)


# ═══════════════════════════════════════════════════════════════════════════════
# HTTP Metrics Server
# ═══════════════════════════════════════════════════════════════════════════════

_global_exporter: Optional[MetricsExporter] = None


class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP handler for Prometheus metrics endpoint."""

    def do_GET(self) -> None:
        if self.path == "/metrics":
            if _global_exporter:
                _global_exporter.collect_all()
                body = _global_exporter.render().encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_error(503, "Exporter not initialized")
        elif self.path == "/health":
            self.send_response(200)
            body = b'{"status": "ok"}'
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(200)
            body = b'<html><body><h1>SLATE Metrics</h1><a href="/metrics">/metrics</a></body></html>'
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(body)

    def log_message(self, fmt: str, *args: Any) -> None:
        """Suppress request logging."""
        pass


def start_metrics_server(port: int = 9090, host: str = "127.0.0.1") -> threading.Thread:
    """Start a background HTTP server for Prometheus metrics scraping.

    Args:
        port: Port to listen on (default 9090).
        host: Host to bind to (default 127.0.0.1 — local only per SLATE security).

    Returns:
        Background thread running the server.
    """
    global _global_exporter
    _global_exporter = MetricsExporter()

    server = HTTPServer((host, port), MetricsHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True, name="slate-metrics")
    thread.start()
    log.info(f"Metrics server started at http://{host}:{port}/metrics")
    return thread


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="SLATE Prometheus Metrics Exporter")
    parser.add_argument("--serve", action="store_true", help="Start metrics HTTP server")
    parser.add_argument("--port", type=int, default=9090, help="Metrics server port (default 9090)")
    parser.add_argument("--status", action="store_true", help="Print current metrics")
    parser.add_argument("--json", action="store_true", help="JSON metrics output")
    args = parser.parse_args()

    if args.serve:
        print(f"Starting SLATE metrics server on http://127.0.0.1:{args.port}/metrics")
        print("Press Ctrl+C to stop")
        start_metrics_server(port=args.port)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopped.")
    elif args.json:
        exporter = MetricsExporter()
        exporter.collect_all()
        print(exporter.render_json())
    else:
        exporter = MetricsExporter()
        exporter.collect_all()
        print(exporter.render())


if __name__ == "__main__":
    main()
