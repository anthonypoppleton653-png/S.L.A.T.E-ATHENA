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

PORT_FORWARDS = {
    'dashboard': ('slate-dashboard-svc', 8080, 8080),
    'agent-router': ('slate-agent-router-svc', 8081, 8081),
    'autonomous': ('slate-autonomous-svc', 8082, 8082),
    'bridge': ('slate-copilot-bridge-svc', 8083, 8083),
    'workflow': ('slate-workflow-svc', 8084, 8084),
    'ollama': ('ollama-svc', 11434, 11434),
    'chromadb': ('chromadb-svc', 8000, 8000),
    'metrics': ('slate-metrics-svc', 9090, 9090),
}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def run_cmd(cmd: list[str], check: bool = True, capture: bool = True, timeout: int = 120) -> subprocess.CompletedProcess:
    """Run a command and return result."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture,
            text=True,
            timeout=timeout,
            encoding='utf-8',
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
    
    print("Applying Kustomize manifests...")
    r = run_cmd(['kubectl', 'apply', '-k', str(K8S_DIR)], check=False, timeout=120)
    if r.returncode == 0:
        print("  ✓ Base manifests applied")
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


def cmd_port_forward():
    """Set up port forwarding for all SLATE services."""
    print_banner("Setting Up Port Forwarding")
    
    print("Available services:")
    for name, (svc, local_port, remote_port) in PORT_FORWARDS.items():
        print(f"  {name}: 127.0.0.1:{local_port} → {svc}:{remote_port}")
    
    print("\nStarting port forwards (press Ctrl+C to stop)...")
    processes = []
    try:
        for name, (svc, local_port, remote_port) in PORT_FORWARDS.items():
            proc = subprocess.Popen(
                ['kubectl', '-n', NAMESPACE, 'port-forward', f'svc/{svc}', f'127.0.0.1:{local_port}:{remote_port}'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            processes.append((name, proc))
            print(f"  ✓ {name}: 127.0.0.1:{local_port}")
        
        print("\nAll port forwards active. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping port forwards...")
        for name, proc in processes:
            proc.terminate()
        print("  Done.")


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
        cmd_port_forward()
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
