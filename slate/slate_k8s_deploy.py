#!/usr/bin/env python3
# Modified: 2026-02-08T22:00:00Z | Author: COPILOT | Change: Create K8s deployment automation script for SLATE
"""
SLATE Kubernetes Deployment Manager
Deploys, manages, and monitors the full SLATE agentic AI system on Kubernetes.

Usage:
    python slate/slate_k8s_deploy.py --status          # Check deployment status
    python slate/slate_k8s_deploy.py --deploy           # Deploy full SLATE stack
    python slate/slate_k8s_deploy.py --deploy-kustomize # Deploy via Kustomize
    python slate/slate_k8s_deploy.py --deploy-helm      # Deploy via Helm
    python slate/slate_k8s_deploy.py --teardown         # Remove all SLATE K8s resources
    python slate/slate_k8s_deploy.py --port-forward      # Set up port forwarding
    python slate/slate_k8s_deploy.py --preload-models    # Trigger model preload job
    python slate/slate_k8s_deploy.py --logs [component]  # View component logs
    python slate/slate_k8s_deploy.py --health            # Run K8s health check
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime


# ─── Constants ────────────────────────────────────────────────────────────────

WORKSPACE = Path(os.environ.get('SLATE_WORKSPACE', Path(__file__).resolve().parent.parent))
K8S_DIR = WORKSPACE / 'k8s'
HELM_DIR = WORKSPACE / 'helm'
NAMESPACE = 'slate'
RELEASE_NAME = 'slate'

COMPONENTS = [
    'slate-core',
    'ollama',
    'chromadb',
    'slate-agent-router',
    'slate-autonomous-loop',
    'slate-copilot-bridge',
    'slate-workflow-manager',
]

# Modified: 2026-02-09T03:30:00Z | Author: COPILOT | Change: Add instruction-controller to PORT_FORWARDS
# Modified: 2026-02-10T12:00:00Z | Author: COPILOT | Change: Add LM Studio note — host-level service, not K8s pod
PORT_FORWARDS = {
    'dashboard': ('slate-dashboard-svc', 8080, 8080),
    'agent-router': ('slate-agent-router-svc', 8081, 8081),
    'autonomous': ('slate-autonomous-svc', 8082, 8082),
    'bridge': ('slate-copilot-bridge-svc', 8083, 8083),
    'workflow': ('slate-workflow-svc', 8084, 8084),
    'instructions': ('slate-instruction-controller-svc', 8085, 8085),
    'ollama': ('ollama-svc', 11434, 11434),
    'chromadb': ('chromadb-svc', 8000, 8000),
    'metrics': ('slate-metrics-svc', 9090, 9090),
    # LM Studio (port 1234) runs on the host — K8s pods reach it via host.docker.internal:1234
    # No port-forward needed; env var LMSTUDIO_HOST is set in deployments.yaml
}


# ─── Helpers ──────────────────────────────────────────────────────────────────

# Modified: 2026-02-08T23:20:00Z | Author: COPILOT | Change: Add input_data param for piping kustomize output to kubectl apply
def run_cmd(cmd: list[str], check: bool = True, capture: bool = True, timeout: int = 120, input_data: str = None) -> subprocess.CompletedProcess:
    """Run a command and return result."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture,
            text=True,
            timeout=timeout,
            encoding='utf-8',
            input=input_data,
        )
        if check and result.returncode != 0:
            print(f"  ERROR: {' '.join(cmd)}")
            if result.stderr:
                print(f"  {result.stderr[:500]}")
        return result
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT: {' '.join(cmd)}")
        return subprocess.CompletedProcess(cmd, 1, '', 'timeout')
    except FileNotFoundError:
        print(f"  NOT FOUND: {cmd[0]}")
        return subprocess.CompletedProcess(cmd, 1, '', f'{cmd[0]} not found')


def kubectl(*args, **kwargs) -> subprocess.CompletedProcess:
    """Run kubectl command."""
    return run_cmd(['kubectl', '-n', NAMESPACE, *args], **kwargs)


def helm(*args, **kwargs) -> subprocess.CompletedProcess:
    """Run helm command."""
    return run_cmd(['helm', *args], **kwargs)


def check_prerequisites() -> dict:
    """Check that required tools are installed."""
    tools = {}
    for tool in ['kubectl', 'helm', 'docker']:
        r = run_cmd([tool, 'version', '--client'] if tool == 'kubectl' else [tool, 'version'], check=False)
        tools[tool] = r.returncode == 0
    
    # Check kubectl cluster connection
    r = run_cmd(['kubectl', 'cluster-info'], check=False)
    tools['cluster'] = r.returncode == 0
    
    # Check for GPU operator / device plugin
    r = run_cmd(['kubectl', 'get', 'daemonset', '-n', 'kube-system', '-l', 'app.kubernetes.io/name=nvidia-device-plugin', '-o', 'name'], check=False)
    tools['gpu-plugin'] = r.returncode == 0 and r.stdout.strip() != ''
    
    return tools


def print_banner(text: str):
    """Print a formatted banner."""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


# ─── Commands ─────────────────────────────────────────────────────────────────

def cmd_status():
    """Show SLATE K8s deployment status."""
    print_banner("SLATE Kubernetes Status")
    
    # Prerequisites
    prereqs = check_prerequisites()
    print("Prerequisites:")
    for tool, ok in prereqs.items():
        print(f"  {'✓' if ok else '✗'} {tool}")
    
    if not prereqs.get('cluster'):
        print("\n  No Kubernetes cluster connected. Run:")
        print("    minikube start --gpus all --memory 32768 --cpus 12")
        print("  Or connect to an existing cluster.")
        return
    
    # Namespace
    r = kubectl('get', 'namespace', NAMESPACE, '-o', 'name', check=False)
    ns_exists = r.returncode == 0
    print(f"\n  Namespace: {'✓ exists' if ns_exists else '✗ not found'}")
    
    if not ns_exists:
        print("  Deploy with: python slate/slate_k8s_deploy.py --deploy")
        return
    
    # Deployments
    print("\nDeployments:")
    r = kubectl('get', 'deployments', '-o', 'wide', '--no-headers', check=False)
    if r.stdout.strip():
        for line in r.stdout.strip().split('\n'):
            parts = line.split()
            name = parts[0] if parts else '?'
            ready = parts[1] if len(parts) > 1 else '?'
            print(f"  {'✓' if '/' in ready and ready.split('/')[0] == ready.split('/')[1] else '✗'} {name}: {ready}")
    else:
        print("  No deployments found")
    
    # Pods
    print("\nPods:")
    r = kubectl('get', 'pods', '-o', 'wide', '--no-headers', check=False)
    if r.stdout.strip():
        for line in r.stdout.strip().split('\n'):
            parts = line.split()
            name = parts[0] if parts else '?'
            status = parts[2] if len(parts) > 2 else '?'
            ready = parts[1] if len(parts) > 1 else '?'
            node = parts[6] if len(parts) > 6 else '?'
            icon = '✓' if status == 'Running' else '⚠' if status in ('Pending', 'ContainerCreating') else '✗'
            print(f"  {icon} {name}: {status} ({ready}) on {node}")
    else:
        print("  No pods found")
    
    # Services
    print("\nServices:")
    r = kubectl('get', 'services', '-o', 'wide', '--no-headers', check=False)
    if r.stdout.strip():
        for line in r.stdout.strip().split('\n'):
            parts = line.split()
            name = parts[0] if parts else '?'
            svc_type = parts[1] if len(parts) > 1 else '?'
            cluster_ip = parts[2] if len(parts) > 2 else '?'
            ports = parts[4] if len(parts) > 4 else '?'
            print(f"  {name}: {svc_type} {cluster_ip} ({ports})")
    
    # CronJobs
    print("\nCronJobs:")
    r = kubectl('get', 'cronjobs', '--no-headers', check=False)
    if r.stdout.strip():
        for line in r.stdout.strip().split('\n'):
            parts = line.split()
            name = parts[0] if parts else '?'
            schedule = parts[1] if len(parts) > 1 else '?'
            active = parts[3] if len(parts) > 3 else '?'
            last = parts[4] if len(parts) > 4 else 'never'
            print(f"  {name}: {schedule} (active: {active}, last: {last})")
    else:
        print("  No CronJobs found")
    
    # PVCs
    print("\nPersistent Volume Claims:")
    r = kubectl('get', 'pvc', '--no-headers', check=False)
    if r.stdout.strip():
        for line in r.stdout.strip().split('\n'):
            parts = line.split()
            name = parts[0] if parts else '?'
            status = parts[1] if len(parts) > 1 else '?'
            size = parts[3] if len(parts) > 3 else '?'
            icon = '✓' if status == 'Bound' else '✗'
            print(f"  {icon} {name}: {status} ({size})")
    
    # GPU resources
    print("\nGPU Resources:")
    r = kubectl('get', 'resourcequota', 'slate-gpu-quota', '-o', 'json', check=False)
    if r.returncode == 0 and r.stdout:
        try:
            quota = json.loads(r.stdout)
            used = quota.get('status', {}).get('used', {})
            hard = quota.get('status', {}).get('hard', {})
            gpu_used = used.get('requests.nvidia.com/gpu', '0')
            gpu_limit = hard.get('requests.nvidia.com/gpu', '2')
            print(f"  GPUs: {gpu_used}/{gpu_limit} allocated")
        except json.JSONDecodeError:
            print("  Could not parse GPU quota")
    else:
        print("  No GPU quota configured")
    
    print()


# Modified: 2026-02-08T23:20:00Z | Author: COPILOT | Change: Use kustomize pipe for overlays to handle cross-directory references
def cmd_deploy_kustomize():
    """Deploy SLATE via Kustomize."""
    print_banner("Deploying SLATE via Kustomize")
    
    prereqs = check_prerequisites()
    if not prereqs.get('kubectl'):
        print("ERROR: kubectl not found. Install kubectl first.")
        return
    if not prereqs.get('cluster'):
        print("ERROR: No Kubernetes cluster connected.")
        print("  Start a local cluster: minikube start --gpus all --memory 32768 --cpus 12")
        return
    
    # Check for local overlay first
    local_overlay = K8S_DIR / 'overlays' / 'local'
    if local_overlay.exists():
        print("Applying Kustomize manifests (local overlay)...")
        # Use kustomize render + pipe to handle cross-directory references
        render = run_cmd(
            ['kubectl', 'kustomize', str(local_overlay), '--load-restrictor', 'LoadRestrictionsNone'],
            check=False, timeout=120
        )
        if render.returncode != 0:
            print(f"  ✗ Kustomize render failed: {render.stderr[:300]}")
            print("  Falling back to base manifests...")
            r = run_cmd(['kubectl', 'apply', '-k', str(K8S_DIR)], check=False, timeout=120)
        else:
            # Pipe rendered YAML to kubectl apply
            r = run_cmd(
                ['kubectl', 'apply', '-f', '-'],
                check=False, timeout=120,
                input_data=render.stdout
            )
    else:
        print("Applying Kustomize manifests (base)...")
        r = run_cmd(['kubectl', 'apply', '-k', str(K8S_DIR)], check=False, timeout=120)
    
    if r.returncode == 0:
        print("  ✓ Manifests applied")
    else:
        print(f"  ✗ Failed: {r.stderr[:300]}")
        return
    
    # Apply additional manifests
    for manifest in ['agentic-system.yaml', 'ml-pipeline.yaml', 'ingress-gpu.yaml']:
        path = K8S_DIR / manifest
        if path.exists():
            r = run_cmd(['kubectl', 'apply', '-f', str(path)], check=False, timeout=60)
            if r.returncode == 0:
                print(f"  ✓ {manifest} applied")
            else:
                print(f"  ⚠ {manifest}: {r.stderr[:200]}")
    
    print("\nWaiting for pods to start...")
    time.sleep(5)
    r = kubectl('get', 'pods', '--no-headers', check=False)
    if r.stdout:
        print(r.stdout)
    
    print("Deploy complete. Check status with: python slate/slate_k8s_deploy.py --status")


def cmd_deploy_helm():
    """Deploy SLATE via Helm chart."""
    print_banner("Deploying SLATE via Helm")
    
    prereqs = check_prerequisites()
    if not prereqs.get('helm'):
        print("ERROR: helm not found. Install helm first.")
        return
    if not prereqs.get('cluster'):
        print("ERROR: No Kubernetes cluster connected.")
        return
    
    # Check if release exists
    r = helm('list', '-n', NAMESPACE, '-q', check=False)
    release_exists = RELEASE_NAME in (r.stdout or '')
    
    action = 'upgrade' if release_exists else 'install'
    print(f"{'Upgrading' if release_exists else 'Installing'} SLATE Helm release...")
    
    r = helm(
        action, RELEASE_NAME, str(HELM_DIR),
        '-n', NAMESPACE,
        '--create-namespace',
        '--wait',
        '--timeout', '10m',
        check=False,
        timeout=660,
    )
    
    if r.returncode == 0:
        print(f"  ✓ SLATE {action}d successfully")
    else:
        print(f"  ✗ Helm {action} failed: {r.stderr[:500]}")
        return
    
    # Show release info
    r = helm('status', RELEASE_NAME, '-n', NAMESPACE, check=False)
    if r.stdout:
        # Print just the summary lines
        for line in r.stdout.split('\n')[:15]:
            print(f"  {line}")
    
    print("\nDeploy complete. Check status with: python slate/slate_k8s_deploy.py --status")


def cmd_deploy():
    """Deploy SLATE (auto-detect Helm or Kustomize)."""
    prereqs = check_prerequisites()
    if prereqs.get('helm'):
        cmd_deploy_helm()
    else:
        cmd_deploy_kustomize()


def cmd_teardown():
    """Remove all SLATE K8s resources."""
    print_banner("Tearing Down SLATE K8s")
    
    # Try Helm uninstall first
    r = helm('list', '-n', NAMESPACE, '-q', check=False)
    if RELEASE_NAME in (r.stdout or ''):
        print("Removing Helm release...")
        helm('uninstall', RELEASE_NAME, '-n', NAMESPACE, check=False, timeout=120)
        print("  ✓ Helm release removed")
    
    # Delete namespace
    print("Removing namespace...")
    r = run_cmd(['kubectl', 'delete', 'namespace', NAMESPACE, '--timeout=60s'], check=False, timeout=90)
    if r.returncode == 0:
        print(f"  ✓ Namespace '{NAMESPACE}' deleted")
    else:
        print(f"  ⚠ {r.stderr[:200]}")
    
    print("\nTeardown complete.")


# Modified: 2026-02-09T03:30:00Z | Author: COPILOT | Change: Improve port-forward with conflict detection, stale cleanup, background mode, health verification
def _check_port_available(port: int) -> tuple[bool, int | None]:
    """Check if a port is available. Returns (available, pid_if_occupied)."""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            s.bind(('127.0.0.1', port))
            return True, None
    except OSError:
        # Port in use — try to find the PID (Windows)
        try:
            r = subprocess.run(
                ['netstat', '-ano'], capture_output=True, text=True, timeout=10
            )
            for line in r.stdout.splitlines():
                if f':{port}' in line and 'LISTENING' in line:
                    parts = line.split()
                    pid = int(parts[-1])
                    return False, pid
        except Exception:
            pass
        return False, None


def _kill_stale_kubectl_forwards():
    """Kill any existing kubectl port-forward processes."""
    try:
        r = subprocess.run(
            ['tasklist', '/FI', 'IMAGENAME eq kubectl.exe', '/FO', 'CSV', '/NH'],
            capture_output=True, text=True, timeout=10
        )
        for line in r.stdout.strip().splitlines():
            if 'kubectl' in line.lower():
                # Check if it's a port-forward process via command line
                parts = line.strip('"').split('","')
                if len(parts) >= 2:
                    pid = parts[1].strip('"')
                    try:
                        cr = subprocess.run(
                            ['wmic', 'process', 'where', f'ProcessId={pid}', 'get', 'CommandLine', '/VALUE'],
                            capture_output=True, text=True, timeout=10
                        )
                        if 'port-forward' in cr.stdout:
                            subprocess.run(['taskkill', '/PID', pid, '/F'],
                                           capture_output=True, timeout=5)
                    except Exception:
                        pass
    except Exception:
        pass


def cmd_port_forward(background: bool = False):
    """Set up port forwarding for all SLATE services.

    Args:
        background: If True, start forwards in background and return immediately.
                    If False (default), block until Ctrl+C.
    """
    print_banner("Setting Up Port Forwarding")

    # Kill stale kubectl port-forwards
    _kill_stale_kubectl_forwards()
    time.sleep(1)

    # Check for port conflicts
    conflicts = []
    for name, (svc, local_port, remote_port) in PORT_FORWARDS.items():
        available, pid = _check_port_available(local_port)
        if not available:
            conflicts.append((name, local_port, pid))

    if conflicts:
        print("Port conflicts detected:")
        for name, port, pid in conflicts:
            pid_info = f" (PID {pid})" if pid else ""
            print(f"  ⚠ {name}: 127.0.0.1:{port} already in use{pid_info}")
        print("  Skipping conflicting ports.\n")
    conflict_ports = {c[1] for c in conflicts}

    print("Starting port forwards...")
    processes = []
    for name, (svc, local_port, remote_port) in PORT_FORWARDS.items():
        if local_port in conflict_ports:
            print(f"  ⊘ {name}: 127.0.0.1:{local_port} (skipped — conflict)")
            continue
        proc = subprocess.Popen(
            ['kubectl', '-n', NAMESPACE, 'port-forward', '--address', '127.0.0.1',
             f'svc/{svc}', f'{local_port}:{remote_port}'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        processes.append((name, proc, local_port))
        print(f"  ✓ {name}: 127.0.0.1:{local_port} → {svc}:{remote_port}")

    if background:
        print(f"\n{len(processes)} port forwards started in background.")
        # Verify health after short delay
        time.sleep(3)
        _verify_port_forward_health(processes)
        return

    try:
        print(f"\n{len(processes)} port forwards active. Press Ctrl+C to stop.")
        while True:
            time.sleep(5)
            # Check for dead processes and restart
            for i, (name, proc, lport) in enumerate(processes):
                if proc.poll() is not None:
                    svc_info = PORT_FORWARDS[name]
                    new_proc = subprocess.Popen(
                        ['kubectl', '-n', NAMESPACE, 'port-forward', '--address', '127.0.0.1',
                         f'svc/{svc_info[0]}', f'{lport}:{svc_info[2]}'],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    processes[i] = (name, new_proc, lport)
                    print(f"  ↻ Restarted: {name}: 127.0.0.1:{lport}")
    except KeyboardInterrupt:
        print("\nStopping port forwards...")
        for name, proc, _ in processes:
            proc.terminate()
        print("  Done.")


def _verify_port_forward_health(processes: list):
    """Quick health check on port-forwarded services."""
    import urllib.request
    ok_count = 0
    for name, proc, lport in processes:
        if proc.poll() is not None:
            print(f"  ✗ {name}: process died")
            continue
        # Try health endpoint
        for path in ['/api/health', '/health', '/']:
            try:
                req = urllib.request.Request(f'http://127.0.0.1:{lport}{path}', method='GET')
                with urllib.request.urlopen(req, timeout=3) as resp:
                    if resp.status == 200:
                        ok_count += 1
                        print(f"  ✓ {name}: healthy")
                        break
            except Exception:
                continue
        else:
            print(f"  ? {name}: no health endpoint responded")
    print(f"\n  Health: {ok_count}/{len(processes)} services verified")


def cmd_preload_models():
    """Trigger the model preload job."""
    print_banner("Triggering Model Preload")
    
    # Delete old job if exists
    kubectl('delete', 'job', 'slate-model-preload', '--ignore-not-found=true', check=False)
    
    # Apply the ML pipeline manifest (contains the preload job)
    path = K8S_DIR / 'ml-pipeline.yaml'
    if path.exists():
        r = run_cmd(['kubectl', 'apply', '-f', str(path)], check=False)
        if r.returncode == 0:
            print("  ✓ Model preload job created")
            print("  Monitor with: kubectl -n slate logs -f job/slate-model-preload")
        else:
            print(f"  ✗ Failed: {r.stderr[:200]}")
    else:
        print(f"  ✗ {path} not found")


def cmd_logs(component: str = None):
    """View logs for a SLATE component."""
    if component:
        label = f"app.kubernetes.io/component={component}"
        r = kubectl('logs', '-l', label, '--tail=100', '--all-containers', check=False)
        if r.stdout:
            print(r.stdout)
        else:
            print(f"No logs found for component={component}")
    else:
        print("Available components:")
        for comp in ['core', 'ollama', 'vectorstore', 'agent-router', 'autonomous-loop',
                     'copilot-bridge', 'workflow-manager', 'model-trainer', 'codebase-indexer',
                     'benchmarks', 'health-check', 'workflow-cleanup', 'runner']:
            print(f"  {comp}")
        print("\nUsage: python slate/slate_k8s_deploy.py --logs <component>")


def cmd_health():
    """Run K8s-specific health checks."""
    print_banner("SLATE K8s Health Check")
    
    checks = []
    
    # 1. Namespace exists
    r = kubectl('get', 'namespace', NAMESPACE, '-o', 'name', check=False)
    checks.append(('Namespace', r.returncode == 0))
    
    # 2. All deployments ready
    r = kubectl('get', 'deployments', '-o', 'json', check=False)
    if r.returncode == 0 and r.stdout:
        try:
            deps = json.loads(r.stdout).get('items', [])
            for dep in deps:
                name = dep['metadata']['name']
                spec_replicas = dep['spec'].get('replicas', 1)
                ready = dep.get('status', {}).get('readyReplicas', 0) or 0
                checks.append((f'Deploy: {name}', ready >= spec_replicas))
        except json.JSONDecodeError:
            checks.append(('Deployments', False))
    
    # 3. All PVCs bound
    r = kubectl('get', 'pvc', '-o', 'json', check=False)
    if r.returncode == 0 and r.stdout:
        try:
            pvcs = json.loads(r.stdout).get('items', [])
            for pvc in pvcs:
                name = pvc['metadata']['name']
                phase = pvc.get('status', {}).get('phase', 'Unknown')
                checks.append((f'PVC: {name}', phase == 'Bound'))
        except json.JSONDecodeError:
            checks.append(('PVCs', False))
    
    # 4. No crashed pods
    r = kubectl('get', 'pods', '-o', 'json', check=False)
    crash_count = 0
    if r.returncode == 0 and r.stdout:
        try:
            pods = json.loads(r.stdout).get('items', [])
            for pod in pods:
                name = pod['metadata']['name']
                phase = pod.get('status', {}).get('phase', 'Unknown')
                if phase in ('Failed', 'CrashLoopBackOff'):
                    crash_count += 1
        except json.JSONDecodeError:
            pass
    checks.append(('No crashed pods', crash_count == 0))
    
    # Print results
    all_pass = True
    for name, ok in checks:
        print(f"  {'✓' if ok else '✗'} {name}")
        if not ok:
            all_pass = False
    
    print(f"\n  Overall: {'PASS ✓' if all_pass else 'FAIL ✗'}")
    print(f"  Timestamp: {datetime.utcnow().isoformat()}Z")
    return all_pass


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='SLATE Kubernetes Deployment Manager')
    parser.add_argument('--status', action='store_true', help='Show deployment status')
    parser.add_argument('--deploy', action='store_true', help='Deploy full SLATE stack (auto-detect)')
    parser.add_argument('--deploy-kustomize', action='store_true', help='Deploy via Kustomize')
    parser.add_argument('--deploy-helm', action='store_true', help='Deploy via Helm')
    parser.add_argument('--teardown', action='store_true', help='Remove all SLATE K8s resources')
    parser.add_argument('--port-forward', action='store_true', help='Set up port forwarding')
    parser.add_argument('--background', action='store_true', help='Run port-forward in background (non-blocking)')
    parser.add_argument('--preload-models', action='store_true', help='Trigger model preload job')
    parser.add_argument('--logs', nargs='?', const=None, default=False, help='View component logs')
    parser.add_argument('--health', action='store_true', help='Run K8s health check')
    parser.add_argument('--json', action='store_true', help='Output as JSON where applicable')
    
    args = parser.parse_args()
    
    if args.status:
        cmd_status()
    elif args.deploy:
        cmd_deploy()
    elif args.deploy_kustomize:
        cmd_deploy_kustomize()
    elif args.deploy_helm:
        cmd_deploy_helm()
    elif args.teardown:
        cmd_teardown()
    elif args.port_forward:
        cmd_port_forward(background=args.background)
    elif args.preload_models:
        cmd_preload_models()
    elif args.logs is not False:
        cmd_logs(args.logs)
    elif args.health:
        success = cmd_health()
        sys.exit(0 if success else 1)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
