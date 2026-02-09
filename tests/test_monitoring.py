# Modified: 2026-02-09T12:00:00Z | Author: COPILOT | Change: Add test coverage for monitoring module
"""
Tests for slate/monitoring.py — Prometheus-compatible monitoring system
"""

import pytest
import threading
from unittest.mock import MagicMock, patch
from pathlib import Path

try:
    from slate.monitoring import (
        MetricType,
        Metric,
        MetricsRegistry,
        MetricsExporter,
    )
    MODULE_AVAILABLE = True
except ImportError as e:
    MODULE_AVAILABLE = False
    pytest.skip(f"monitoring not importable: {e}", allow_module_level=True)


class TestMetricType:
    """Test MetricType constants."""

    def test_counter_type(self):
        assert MetricType.COUNTER == "counter"

    def test_gauge_type(self):
        assert MetricType.GAUGE == "gauge"

    def test_histogram_type(self):
        assert MetricType.HISTOGRAM == "histogram"

    def test_summary_type(self):
        assert MetricType.SUMMARY == "summary"


class TestMetric:
    """Test Metric dataclass."""

    def test_create_metric(self):
        m = Metric(
            name="slate_test_total",
            help_text="Test metric",
            metric_type=MetricType.COUNTER,
            value=42.0
        )
        assert m.name == "slate_test_total"
        assert m.value == 42.0

    def test_to_prometheus(self):
        m = Metric(
            name="slate_test_gauge",
            help_text="A test gauge",
            metric_type=MetricType.GAUGE,
            value=3.14
        )
        output = m.to_prometheus()
        assert "# HELP slate_test_gauge A test gauge" in output
        assert "# TYPE slate_test_gauge gauge" in output
        assert "slate_test_gauge 3.14" in output

    def test_to_prometheus_with_labels(self):
        m = Metric(
            name="slate_inference_count",
            help_text="Inference count",
            metric_type=MetricType.COUNTER,
            value=100.0,
            labels={"model": "slate-coder", "gpu": "0"}
        )
        output = m.to_prometheus()
        assert 'model="slate-coder"' in output
        assert 'gpu="0"' in output

    def test_default_value_is_zero(self):
        m = Metric(
            name="test",
            help_text="test",
            metric_type=MetricType.GAUGE
        )
        assert m.value == 0.0


class TestMetricsRegistry:
    """Test MetricsRegistry class."""

    def test_create_registry(self):
        reg = MetricsRegistry()
        assert reg is not None

    def test_register_metric(self):
        reg = MetricsRegistry()
        reg.register("test_metric", "A test metric", MetricType.GAUGE)

    def test_set_gauge(self):
        reg = MetricsRegistry()
        reg.register("test_gauge", "Test gauge", MetricType.GAUGE)
        reg.set_gauge("test_gauge", 42.0)

    def test_inc_counter(self):
        reg = MetricsRegistry()
        reg.register("test_counter", "Test counter", MetricType.COUNTER)
        reg.inc_counter("test_counter", 1.0)
        reg.inc_counter("test_counter", 1.0)

    def test_to_prometheus(self):
        reg = MetricsRegistry()
        reg.register("test_metric", "Test", MetricType.GAUGE)
        reg.set_gauge("test_metric", 5.0)
        output = reg.to_prometheus()
        assert isinstance(output, str)

    def test_to_dict(self):
        reg = MetricsRegistry()
        reg.register("test_metric", "Test", MetricType.GAUGE)
        reg.set_gauge("test_metric", 5.0)
        d = reg.to_dict()
        assert isinstance(d, dict)


class TestMetricsExporter:
    """Test MetricsExporter class."""

    def test_create_exporter(self):
        exporter = MetricsExporter()
        assert exporter is not None
        assert exporter.registry is not None

    @patch("slate.monitoring.subprocess.run")
    def test_collect_system_metrics(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr=""
        )
        exporter = MetricsExporter()
        exporter.collect_system_metrics()

    def test_record_inference(self):
        exporter = MetricsExporter()
        exporter.record_inference("slate-coder", latency=1.5, tokens=128)

    def test_record_agent_task(self):
        exporter = MetricsExporter()
        exporter.record_agent_task("ALPHA", success=True, latency=0.5)

    def test_record_availability(self):
        exporter = MetricsExporter()
        exporter.record_availability(0.998, target=0.999)
