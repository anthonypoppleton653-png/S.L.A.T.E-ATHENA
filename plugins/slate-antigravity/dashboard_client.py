# Modified: 2026-02-09T03:24:00-05:00 | Author: ANTIGRAVITY (Gemini) | Change: Dashboard API client for Antigravity
# AI Note: When modifying, add a comment with the current date, time, and a 'Gemini' marker.
"""
SLATE Dashboard Client for Antigravity
=======================================
Provides programmatic access to the SLATE dashboard API at 127.0.0.1:8080.
This is how Antigravity reads system state, task queues, agent registry,
GPU info, and all SLATE services without going through VS Code.

Usage:
    from plugins.slate_antigravity.dashboard_client import SlateDashboard

    dashboard = SlateDashboard()
    status = dashboard.status()
    tasks = dashboard.tasks()
    agents = dashboard.agents()
"""

import json
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone


class SlateDashboard:
    """Client for the SLATE dashboard API.
    
    Auto-detects the best available endpoint:
    1. K8s Antigravity Bridge at localhost:30085 (NodePort)
    2. Direct dashboard at localhost:8080
    """

    def __init__(self, host: str = None, timeout: int = 10):
        self.timeout = timeout
        self.agent_name = "ANTIGRAVITY"
        
        if host:
            self.host = host
        else:
            # Auto-detect: try K8s bridge first, then direct dashboard
            self.host = self._detect_endpoint()

    def _detect_endpoint(self) -> str:
        """Detect the best available dashboard endpoint."""
        candidates = [
            os.environ.get("ANTIGRAVITY_BRIDGE_URL", ""),
            "http://127.0.0.1:30085",  # K8s NodePort (antigravity-bridge)
            os.environ.get("SLATE_DASHBOARD_URL", ""),
            "http://127.0.0.1:8080",   # Direct dashboard
        ]
        for url in candidates:
            if not url:
                continue
            try:
                req = urllib.request.Request(f"{url}/health", headers={"User-Agent": "SLATE-ANTIGRAVITY/1.2.0"})
                with urllib.request.urlopen(req, timeout=3) as resp:
                    if resp.status == 200:
                        return url
            except Exception:
                continue
        return "http://127.0.0.1:8080"  # fallback

    def _get(self, path: str) -> dict:
        """GET a JSON endpoint."""
        url = f"{self.host}{path}"
        req = urllib.request.Request(url, headers={"User-Agent": f"SLATE-{self.agent_name}/1.1.0"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as e:
            return {"error": str(e), "endpoint": path}
        except Exception as e:
            return {"error": str(e), "endpoint": path}

    def _post(self, path: str, data: dict = None) -> dict:
        """POST to a JSON endpoint."""
        url = f"{self.host}{path}"
        payload = json.dumps(data or {}).encode("utf-8")
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json", "User-Agent": f"SLATE-{self.agent_name}/1.1.0"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as e:
            return {"error": str(e), "endpoint": path}
        except Exception as e:
            return {"error": str(e), "endpoint": path}

    # ─── Core Status ─────────────────────────────────────────────────────

    def health(self) -> dict:
        """Dashboard health check."""
        return self._get("/health")

    def status(self) -> dict:
        """Full system status (Python, GPU, Ollama, K8s, Antigravity)."""
        return self._get("/api/status")

    # ─── Task Management ─────────────────────────────────────────────────

    def tasks(self) -> dict:
        """Get current task queue."""
        return self._get("/api/tasks")

    # ─── Agent Registry ──────────────────────────────────────────────────

    def agents(self) -> dict:
        """Get all registered agents."""
        return self._get("/api/agents")

    # ─── Infrastructure ──────────────────────────────────────────────────

    def runner(self) -> dict:
        """GitHub Actions runner status."""
        return self._get("/api/runner")

    def runner_status(self) -> dict:
        """Runner detailed status."""
        return self._get("/api/runner/status")

    def gpu(self) -> dict:
        """GPU hardware info."""
        return self._get("/api/gpu")

    def gpu_system(self) -> dict:
        """System GPU metrics."""
        return self._get("/api/system/gpu")

    def services(self) -> dict:
        """SLATE service status."""
        return self._get("/api/services")

    def orchestrator(self) -> dict:
        """Orchestrator status."""
        return self._get("/api/orchestrator")

    # ─── CI/CD & GitHub ──────────────────────────────────────────────────

    def github(self) -> dict:
        """GitHub integration status."""
        return self._get("/api/github")

    def workflows(self) -> dict:
        """GitHub Actions workflows."""
        return self._get("/api/workflows")

    def workflow_runs(self) -> dict:
        """Recent workflow runs."""
        return self._get("/api/workflows/runs")

    def forks(self) -> dict:
        """Contributor fork status."""
        return self._get("/api/forks")

    # ─── Kubernetes ──────────────────────────────────────────────────────

    def kubernetes(self) -> dict:
        """K8s cluster status."""
        return self._get("/api/kubernetes/status")

    # ─── Docker ──────────────────────────────────────────────────────────

    def docker(self) -> dict:
        """Docker environment status."""
        return self._get("/api/docker")

    # ─── AI & Models ─────────────────────────────────────────────────────

    def ai_recommend(self) -> dict:
        """AI model recommendations."""
        return self._get("/api/slate/ai/recommend")

    def benchmark(self) -> dict:
        """Run benchmarks."""
        return self._get("/api/slate/benchmark")

    # ─── Monitoring ──────────────────────────────────────────────────────

    def activity(self) -> dict:
        """Recent activity feed."""
        return self._get("/api/activity")

    def heatmap(self) -> dict:
        """Activity heatmap data."""
        return self._get("/api/heatmap")

    def multirunner(self) -> dict:
        """Multi-runner status (GPU allocation)."""
        return self._get("/api/multirunner")

    # ─── Specs & Tech Tree ───────────────────────────────────────────────

    def specs(self) -> dict:
        """Specification documents."""
        return self._get("/api/specs")

    def tech_tree(self) -> dict:
        """Tech tree / roadmap."""
        return self._get("/api/tech")

    # ─── Schematics ──────────────────────────────────────────────────────

    def schematic_system(self) -> dict:
        """System architecture schematic."""
        return self._get("/api/schematic/system")

    def schematic_widget(self) -> dict:
        """Compact schematic widget."""
        return self._get("/api/schematic/widget/compact")

    # ─── Actions ─────────────────────────────────────────────────────────

    def slate_action(self, action: str) -> dict:
        """Execute a SLATE control action."""
        return self._post(f"/api/slate/{action}")

    def dispatch_workflow(self, workflow: str) -> dict:
        """Dispatch a CI/CD workflow."""
        return self._post(f"/api/dispatch/{workflow}")

    def deploy(self, target: str) -> dict:
        """Deploy to a target."""
        return self._post(f"/api/slate/deploy/{target}")

    # ─── Convenience ─────────────────────────────────────────────────────

    def full_report(self) -> dict:
        """Get a comprehensive system report for Antigravity context."""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": self.agent_name,
            "dashboard": self.host,
            "health": self.health(),
            "status": self.status(),
            "tasks": self.tasks(),
            "agents": self.agents(),
            "services": self.services(),
        }


# ─── CLI ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="SLATE Dashboard Client")
    parser.add_argument("command", nargs="?", default="status",
                        help="API to call: status, tasks, agents, gpu, runner, services, report")
    args = parser.parse_args()

    d = SlateDashboard()
    commands = {
        "status": d.status, "health": d.health, "tasks": d.tasks,
        "agents": d.agents, "gpu": d.gpu, "runner": d.runner,
        "services": d.services, "k8s": d.kubernetes, "docker": d.docker,
        "github": d.github, "workflows": d.workflows, "forks": d.forks,
        "activity": d.activity, "specs": d.specs, "tech": d.tech_tree,
        "report": d.full_report, "orchestrator": d.orchestrator,
        "multirunner": d.multirunner, "schematic": d.schematic_system,
    }

    fn = commands.get(args.command, d.status)
    result = fn()
    print(json.dumps(result, indent=2, default=str))
