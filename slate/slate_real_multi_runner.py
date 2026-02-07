#!/usr/bin/env python3
"""
SLATE Real Multi-Runner Manager - Manages actual GitHub Actions runner instances.

Unlike the benchmark-based slate_multi_runner.py which only wrote to a JSON file,
this module manages REAL runner processes — each with its own directory, registration,
and listener process.

Modified: 2026-02-07T01:41:00Z | Author: COPILOT | Change: Initial implementation of real multi-runner system
"""

import json
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

WORKSPACE_ROOT = Path(__file__).parent.parent
PYTHON = WORKSPACE_ROOT / ".venv" / "Scripts" / "python.exe"


@dataclass
class RealRunner:
    """A real GitHub Actions runner instance."""
    name: str
    directory: Path
    agent_id: int | None = None
    labels: list[str] | None = None
    status: str = "unknown"  # online, offline, unknown
    busy: bool = False
    pid: int | None = None
    gpu_id: int | None = None


class RealMultiRunnerManager:
    """Manages actual GitHub Actions runner processes and registrations."""

    REPO = "SynchronizedLivingArchitecture/S.L.A.T.E"
    API_BASE = f"https://api.github.com/repos/{REPO}"

    def __init__(self, workspace: Path | None = None):
        self.workspace = workspace or WORKSPACE_ROOT
        self.runners: list[RealRunner] = []
        self._token: str | None = None

    # ─── GitHub Auth ─────────────────────────────────────────────────

    def _get_token(self) -> str:
        """Get GitHub token from git credential manager."""
        if self._token:
            return self._token
        result = subprocess.run(
            ["git", "credential", "fill"],
            input="protocol=https\nhost=github.com\n",
            capture_output=True, text=True, cwd=str(self.workspace),
        )
        for line in result.stdout.splitlines():
            if line.startswith("password="):
                self._token = line.split("=", 1)[1]
                return self._token
        raise RuntimeError("Failed to get GitHub token from git credential manager")

    def _api_get(self, endpoint: str) -> dict:
        """Make authenticated GET to GitHub API."""
        import urllib.request
        token = self._get_token()
        req = urllib.request.Request(
            f"{self.API_BASE}/{endpoint}",
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
            },
        )
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _api_post(self, endpoint: str, data: dict | None = None) -> dict:
        """Make authenticated POST to GitHub API."""
        import urllib.request
        token = self._get_token()
        body = json.dumps(data or {}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.API_BASE}/{endpoint}",
            data=body,
            method="POST",
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))

    # ─── Runner Discovery ────────────────────────────────────────────

    def discover_local_runners(self) -> list[RealRunner]:
        """Find all runner directories in the workspace."""
        self.runners = []
        for d in sorted(self.workspace.iterdir()):
            if d.is_dir() and d.name.startswith("actions-runner"):
                runner_file = d / ".runner"
                if runner_file.exists():
                    with open(runner_file, encoding="utf-8-sig") as f:
                        cfg = json.load(f)
                    runner = RealRunner(
                        name=cfg.get("agentName", d.name),
                        directory=d,
                        agent_id=cfg.get("agentId"),
                    )
                    self.runners.append(runner)
                else:
                    self.runners.append(RealRunner(name=d.name, directory=d))
        return self.runners

    def discover_github_runners(self) -> list[dict]:
        """Get all runners registered with GitHub."""
        data = self._api_get("actions/runners")
        return data.get("runners", [])

    def get_full_status(self) -> dict[str, Any]:
        """Get combined local + GitHub runner status."""
        local = self.discover_local_runners()
        github_runners = self.discover_github_runners()

        # Build a map of github runner data by name
        gh_map = {r["name"]: r for r in github_runners}

        # Merge process info
        running_pids = self._get_listener_pids()

        results = []
        for runner in local:
            gh_info = gh_map.get(runner.name, {})
            runner.status = gh_info.get("status", "not_registered")
            runner.busy = gh_info.get("busy", False)
            runner.labels = [
                label["name"] for label in gh_info.get("labels", [])
                if label.get("type") == "custom"
            ]
            runner.agent_id = gh_info.get("id", runner.agent_id)

            # Check if process is alive
            runner_dir_str = str(runner.directory)
            for pid, cwd in running_pids.items():
                if runner_dir_str.lower() in cwd.lower():
                    runner.pid = pid
                    break

            # Determine GPU assignment from labels
            if runner.labels:
                for label in runner.labels:
                    if label.startswith("gpu-") and label != "gpu-2":
                        try:
                            runner.gpu_id = int(label.split("-")[1])
                        except (ValueError, IndexError):
                            pass

            results.append({
                "name": runner.name,
                "directory": str(runner.directory),
                "agent_id": runner.agent_id,
                "status": runner.status,
                "busy": runner.busy,
                "pid": runner.pid,
                "labels": runner.labels or [],
                "gpu_id": runner.gpu_id,
                "process_alive": runner.pid is not None,
            })

        return {
            "total_registered_github": len(github_runners),
            "total_local_directories": len(local),
            "runners": results,
            "all_online": all(r["status"] == "online" for r in results),
            "processes_running": sum(1 for r in results if r["process_alive"]),
            "timestamp": datetime.now().isoformat(),
        }

    def _get_listener_pids(self) -> dict[int, str]:
        """Get PIDs and working directories of runner listener processes."""
        pids = {}
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 "Get-Process -Name 'Runner.Listener' -ErrorAction SilentlyContinue | "
                 "Select-Object Id, @{n='Dir';e={$_.Path}} | "
                 "ForEach-Object { \"$($_.Id)|$($_.Dir)\" }"],
                capture_output=True, text=True, timeout=10,
            )
            for line in result.stdout.strip().splitlines():
                if "|" in line:
                    parts = line.split("|", 1)
                    try:
                        pids[int(parts[0])] = parts[1]
                    except ValueError:
                        pass
        except Exception:
            pass
        return pids

    # ─── Runner Lifecycle ────────────────────────────────────────────

    def start_all(self) -> dict[str, str]:
        """Start all registered runners."""
        self.discover_local_runners()
        results = {}
        for runner in self.runners:
            if not (runner.directory / ".runner").exists():
                results[runner.name] = "not_registered"
                continue
            # Check if already running
            run_cmd = runner.directory / "run.cmd"
            if not run_cmd.exists():
                results[runner.name] = "no_run_cmd"
                continue

            # Start as background process
            proc = subprocess.Popen(
                ["cmd.exe", "/c", str(run_cmd)],
                cwd=str(runner.directory),
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            results[runner.name] = f"started (PID {proc.pid})"
            time.sleep(2)  # Brief pause between starts

        return results

    def stop_all(self) -> dict[str, str]:
        """Stop all runner listener processes."""
        results = {}
        try:
            procs = subprocess.run(
                ["powershell", "-Command",
                 "Get-Process -Name 'Runner.Listener','Runner.Worker' -ErrorAction SilentlyContinue | "
                 "ForEach-Object { Stop-Process -Id $_.Id -Force; \"Stopped $($_.ProcessName) PID $($_.Id)\" }"],
                capture_output=True, text=True, timeout=15,
            )
            for line in procs.stdout.strip().splitlines():
                results[line] = "stopped"
        except Exception as e:
            results["error"] = str(e)
        return results

    def get_registration_token(self) -> str:
        """Get a registration token for new runners."""
        data = self._api_post("actions/runners/registration-token")
        return data["token"]

    # ─── Workflow Dispatch ───────────────────────────────────────────

    def dispatch_workflow(self, workflow: str, ref: str = "main", inputs: dict | None = None) -> bool:
        """Dispatch a workflow via GitHub API."""
        data: dict[str, Any] = {"ref": ref}
        if inputs:
            data["inputs"] = inputs
        try:
            self._api_post(f"actions/workflows/{workflow}/dispatches", data)
            return True
        except Exception as e:
            print(f"  Dispatch failed: {e}")
            return False

    def get_active_runs(self) -> list[dict]:
        """Get currently active workflow runs."""
        runs = []
        for status in ("queued", "in_progress", "waiting"):
            data = self._api_get(f"actions/runs?status={status}&per_page=20")
            for run in data.get("workflow_runs", []):
                runs.append({
                    "id": run["id"],
                    "name": run["name"],
                    "status": run["status"],
                    "conclusion": run.get("conclusion"),
                    "run_number": run["run_number"],
                    "created_at": run["created_at"],
                })
        return runs

    def get_run_jobs(self, run_id: int) -> list[dict]:
        """Get jobs for a specific workflow run."""
        data = self._api_get(f"actions/runs/{run_id}/jobs")
        jobs = []
        for job in data.get("jobs", []):
            jobs.append({
                "id": job["id"],
                "name": job["name"],
                "status": job["status"],
                "conclusion": job.get("conclusion"),
                "runner_name": job.get("runner_name"),
                "started_at": job.get("started_at"),
                "completed_at": job.get("completed_at"),
            })
        return jobs

    # ─── Display ─────────────────────────────────────────────────────

    def print_status(self) -> None:
        """Print human-readable status of all runners."""
        status = self.get_full_status()

        print("=" * 70)
        print("  S.L.A.T.E. Real Multi-Runner Status")
        print("=" * 70)
        print()
        print(f"  GitHub Registered:  {status['total_registered_github']}")
        print(f"  Local Directories:  {status['total_local_directories']}")
        print(f"  Processes Running:  {status['processes_running']}")
        print(f"  All Online:         {'YES' if status['all_online'] else 'NO'}")
        print(f"  Timestamp:          {status['timestamp']}")
        print()
        print("-" * 70)
        print(f"  {'Name':<18} {'AgentID':<10} {'Status':<10} {'Busy':<6} {'PID':<8} {'GPU':<5} {'Labels'}")
        print(f"  {'-'*18} {'-'*10} {'-'*10} {'-'*6} {'-'*8} {'-'*5} {'-'*20}")

        for r in status["runners"]:
            gpu = str(r["gpu_id"]) if r["gpu_id"] is not None else "-"
            pid = str(r["pid"]) if r["pid"] else "-"
            labels = ",".join(r["labels"])
            busy = "YES" if r["busy"] else "no"
            print(f"  {r['name']:<18} {str(r['agent_id'] or '-'):<10} {r['status']:<10} {busy:<6} {pid:<8} {gpu:<5} {labels}")

        print()
        print("=" * 70)


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="SLATE Real Multi-Runner Manager")
    parser.add_argument("--status", action="store_true", help="Show all runner status")
    parser.add_argument("--json", action="store_true", help="Output status as JSON")
    parser.add_argument("--start-all", action="store_true", help="Start all runners")
    parser.add_argument("--stop-all", action="store_true", help="Stop all runners")
    parser.add_argument("--dispatch", type=str, help="Dispatch a workflow (e.g., 'multi-runner.yml')")
    parser.add_argument("--active-runs", action="store_true", help="Show active workflow runs")
    parser.add_argument("--run-jobs", type=int, help="Show jobs for a specific run ID")
    args = parser.parse_args()

    mgr = RealMultiRunnerManager()

    if args.json:
        status = mgr.get_full_status()
        print(json.dumps(status, indent=2, default=str))
    elif args.start_all:
        results = mgr.start_all()
        for name, result in results.items():
            print(f"  {name}: {result}")
    elif args.stop_all:
        results = mgr.stop_all()
        for name, result in results.items():
            print(f"  {name}: {result}")
    elif args.dispatch:
        print(f"Dispatching {args.dispatch}...")
        ok = mgr.dispatch_workflow(args.dispatch)
        print(f"  {'Success' if ok else 'FAILED'}")
    elif args.active_runs:
        runs = mgr.get_active_runs()
        if runs:
            for run in runs:
                print(f"  #{run['run_number']} {run['name']} - {run['status']} ({run['id']})")
        else:
            print("  No active runs.")
    elif args.run_jobs:
        jobs = mgr.get_run_jobs(args.run_jobs)
        for job in jobs:
            runner = job["runner_name"] or "pending"
            print(f"  {job['name']}: {job['status']} -> {runner}")
    else:
        mgr.print_status()


if __name__ == "__main__":
    main()
