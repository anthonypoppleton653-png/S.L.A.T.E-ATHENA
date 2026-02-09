# Modified: 2026-02-09T05:00:00Z | Author: COPILOT | Change: Create test coverage for slate_k8s_deploy.py
"""
Tests for slate/slate_k8s_deploy.py — K8s deployment manager.
Tests focus on logic paths without requiring a live cluster.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import subprocess
import sys

# Add workspace root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestK8sDeployImport:
    """Test that the module can be imported."""

    def test_import_module(self):
        import slate.slate_k8s_deploy
        assert hasattr(slate.slate_k8s_deploy, 'check_prerequisites')
        assert hasattr(slate.slate_k8s_deploy, 'cmd_status')
        assert hasattr(slate.slate_k8s_deploy, 'cmd_health')

    def test_check_prerequisites_exists(self):
        from slate.slate_k8s_deploy import check_prerequisites
        assert callable(check_prerequisites)

    def test_cmd_functions_exist(self):
        from slate.slate_k8s_deploy import cmd_status, cmd_deploy, cmd_health, cmd_teardown
        assert callable(cmd_status)
        assert callable(cmd_deploy)
        assert callable(cmd_health)
        assert callable(cmd_teardown)


class TestK8sManifestPaths:
    """Test that manifest paths are correctly resolved."""

    def test_k8s_dir_exists(self):
        k8s_dir = Path(__file__).parent.parent / "k8s"
        assert k8s_dir.exists(), "k8s/ directory must exist"

    def test_namespace_yaml_exists(self):
        ns = Path(__file__).parent.parent / "k8s" / "namespace.yaml"
        assert ns.exists(), "k8s/namespace.yaml must exist"

    def test_deployments_yaml_exists(self):
        dep = Path(__file__).parent.parent / "k8s" / "deployments.yaml"
        assert dep.exists(), "k8s/deployments.yaml must exist"

    def test_agentic_system_exists(self):
        agent = Path(__file__).parent.parent / "k8s" / "agentic-system.yaml"
        assert agent.exists(), "k8s/agentic-system.yaml must exist"

    def test_ml_pipeline_exists(self):
        ml = Path(__file__).parent.parent / "k8s" / "ml-pipeline.yaml"
        assert ml.exists(), "k8s/ml-pipeline.yaml must exist"

    def test_kustomization_exists(self):
        kustom = Path(__file__).parent.parent / "k8s" / "kustomization.yaml"
        assert kustom.exists(), "k8s/kustomization.yaml must exist"


class TestK8sManifestValidity:
    """Test that YAML manifests are valid."""

    def test_all_manifests_valid_yaml(self):
        import yaml
        k8s_dir = Path(__file__).parent.parent / "k8s"
        errors = []
        for f in k8s_dir.rglob("*.yaml"):
            try:
                list(yaml.safe_load_all(f.read_text(encoding="utf-8")))
            except Exception as e:
                errors.append(f"{f.name}: {e}")
        assert len(errors) == 0, f"Invalid YAML files: {errors}"

    def test_namespace_has_slate(self):
        import yaml
        ns_file = Path(__file__).parent.parent / "k8s" / "namespace.yaml"
        docs = list(yaml.safe_load_all(ns_file.read_text(encoding="utf-8")))
        namespaces = [d for d in docs if d and d.get("kind") == "Namespace"]
        assert any(n["metadata"]["name"] == "slate" for n in namespaces)

    def test_deployments_have_images(self):
        import yaml
        dep_file = Path(__file__).parent.parent / "k8s" / "deployments.yaml"
        docs = list(yaml.safe_load_all(dep_file.read_text(encoding="utf-8")))
        deployments = [d for d in docs if d and d.get("kind") == "Deployment"]
        assert len(deployments) > 0, "Must have at least one deployment"
        for dep in deployments:
            containers = dep["spec"]["template"]["spec"]["containers"]
            for c in containers:
                assert "image" in c, f"Container {c.get('name')} missing image"

    def test_no_zero_bind(self):
        """Security: No manifest should bind to 0.0.0.0 outside of env vars / comments."""
        k8s_dir = Path(__file__).parent.parent / "k8s"
        for f in k8s_dir.rglob("*.yaml"):
            content = f.read_text(encoding="utf-8")
            lines = content.splitlines()
            for i, line in enumerate(lines):
                stripped = line.strip()
                if "0.0.0.0" in stripped:
                    # Allow in: env var values, container commands/args, comments, CIDR blocks
                    if any(kw in stripped for kw in [
                        "value:", "OLLAMA_HOST", "CHROMA_SERVER",
                        "HOST", "LISTEN", "#", "HTTPServer", "command:",
                        "args:", "http.server", "serve_forever", "lambda",
                        "cidr:", "0.0.0.0/0",  # CIDR for ingress rules is allowed
                    ]):
                        continue
                    assert False, f"{f.name}:{i+1} contains 0.0.0.0 binding: {stripped}"


class TestHelmChart:
    """Test Helm chart structure."""

    def test_chart_yaml_exists(self):
        chart = Path(__file__).parent.parent / "helm" / "Chart.yaml"
        assert chart.exists()

    def test_values_yaml_exists(self):
        vals = Path(__file__).parent.parent / "helm" / "values.yaml"
        assert vals.exists()

    def test_values_valid_yaml(self):
        import yaml
        vals = Path(__file__).parent.parent / "helm" / "values.yaml"
        data = yaml.safe_load(vals.read_text(encoding="utf-8"))
        assert isinstance(data, dict)
        # namespace may be at top level or under global
        has_ns = "namespace" in data or "namespace" in data.get("global", {})
        assert has_ns, "values.yaml must define namespace (top-level or global)"

    def test_templates_exist(self):
        templates = Path(__file__).parent.parent / "helm" / "templates"
        assert templates.exists()
        yamls = list(templates.glob("*.yaml"))
        assert len(yamls) > 0, "Helm templates directory must have YAML files"


class TestKustomizeOverlays:
    """Test Kustomize overlay structure."""

    @pytest.mark.parametrize("overlay", ["local", "dev", "staging", "prod"])
    def test_overlay_exists(self, overlay):
        overlay_dir = Path(__file__).parent.parent / "k8s" / "overlays" / overlay
        assert overlay_dir.exists(), f"Overlay {overlay} must exist"

    @pytest.mark.parametrize("overlay", ["local", "dev", "staging", "prod"])
    def test_overlay_has_kustomization(self, overlay):
        kustom = Path(__file__).parent.parent / "k8s" / "overlays" / overlay / "kustomization.yaml"
        assert kustom.exists(), f"Overlay {overlay} must have kustomization.yaml"


class TestK8sDeployMethods:
    """Test K8s deploy functions with mocked subprocess."""

    @patch("slate.slate_k8s_deploy.subprocess.run")
    def test_check_prerequisites_kubectl_found(self, mock_run):
        from slate.slate_k8s_deploy import check_prerequisites
        mock_run.return_value = MagicMock(returncode=0, stdout="Client Version: v1.31.0")
        prereqs = check_prerequisites()
        assert prereqs["kubectl"] is True

    @patch("slate.slate_k8s_deploy.subprocess.run")
    def test_check_prerequisites_kubectl_missing(self, mock_run):
        from slate.slate_k8s_deploy import check_prerequisites
        mock_run.side_effect = FileNotFoundError
        prereqs = check_prerequisites()
        assert prereqs["kubectl"] is False
