// Modified: 2026-02-10T04:00:00Z | Author: COPILOT | Change: Rebuild runtime adapter — K8s/Docker only, local fallback removed per SLATE container-first architecture
/**
 * SLATE Runtime Adapter
 * =====================
 * Detects and manages the SLATE runtime backend (K8s or Docker).
 * The extension connects to whichever runtime is serving the dashboard.
 *
 * Priority order:
 * 1. Kubernetes (kubectl port-forward from slate namespace)
 * 2. Docker Compose (services already exposed via Docker Desktop WSL relay)
 *
 * No local fallback — K8s or Docker is REQUIRED per SLATE architecture.
 */

import * as vscode from 'vscode';
import * as cp from 'child_process';
import * as http from 'http';

// ─── Types ──────────────────────────────────────────────────────────────────

export type RuntimeBackend = 'kubernetes' | 'docker' | 'none';

export interface RuntimeState {
	backend: RuntimeBackend;
	dashboardUrl: string;
	ollamaUrl: string;
	chromaDbUrl: string;
	healthy: boolean;
	podCount: number;
	portForwardPid: number | null;
	lastCheck: number;
	services: ServiceStatus[];
}

export interface ServiceStatus {
	name: string;
	url: string;
	port: number;
	healthy: boolean;
}

// ─── Constants ──────────────────────────────────────────────────────────────

const K8S_NAMESPACE = 'slate';

/** K8s service → local port mapping (with fallback ports for conflicts) */
const K8S_PORT_MAP: Record<string, { svc: string; localPort: number; altPort: number; remotePort: number }> = {
	dashboard:    { svc: 'slate-dashboard-svc',              localPort: 8080,  altPort: 18080, remotePort: 8080 },
	agentRouter:  { svc: 'slate-agent-router-svc',           localPort: 8081,  altPort: 18081, remotePort: 8081 },
	autonomous:   { svc: 'slate-autonomous-svc',             localPort: 8082,  altPort: 18082, remotePort: 8082 },
	bridge:       { svc: 'slate-copilot-bridge-svc',         localPort: 8083,  altPort: 18083, remotePort: 8083 },
	workflow:     { svc: 'slate-workflow-svc',                localPort: 8084,  altPort: 18084, remotePort: 8084 },
	instructions: { svc: 'slate-instruction-controller-svc', localPort: 8085,  altPort: 18085, remotePort: 8085 },
	ollama:       { svc: 'ollama-svc',                       localPort: 11434, altPort: 21434, remotePort: 11434 },
	chromadb:     { svc: 'chromadb-svc',                     localPort: 8000,  altPort: 18000, remotePort: 8000 },
	metrics:      { svc: 'slate-metrics-svc',                localPort: 9090,  altPort: 19090, remotePort: 9090 },
};

/** Track actual ports used (may differ from defaults due to conflicts) */
const ACTIVE_PORTS: Record<string, number> = {};

const HEALTH_CHECK_INTERVAL = 20_000; // 20 seconds
const DETECTION_TIMEOUT = 8_000;      // 8 seconds for runtime detection

// ─── Runtime Adapter ────────────────────────────────────────────────────────

export class SlateRuntimeAdapter implements vscode.Disposable {
	private _state: RuntimeState;
	private _portForwardProcesses: Map<string, cp.ChildProcess> = new Map();
	private _healthInterval: NodeJS.Timeout | undefined;
	private _outputChannel: vscode.OutputChannel;
	private _statusBarItem: vscode.StatusBarItem;
	private _onStateChange = new vscode.EventEmitter<RuntimeState>();
	public readonly onStateChange = this._onStateChange.event;

	constructor() {
		this._state = {
			backend: 'none',
			dashboardUrl: 'http://127.0.0.1:8080',
			ollamaUrl: 'http://127.0.0.1:11434',
			chromaDbUrl: 'http://127.0.0.1:8000',
			healthy: false,
			podCount: 0,
			portForwardPid: null,
			lastCheck: 0,
			services: [],
		};

		this._outputChannel = vscode.window.createOutputChannel('SLATE Runtime');
		this._statusBarItem = vscode.window.createStatusBarItem(
			vscode.StatusBarAlignment.Right,
			99
		);
		this._statusBarItem.command = 'slate.runtimeInfo';
	}

	/** Get current runtime state */
	public get state(): RuntimeState {
		return { ...this._state };
	}

	/** Get the dashboard URL for the current runtime */
	public get dashboardUrl(): string {
		return this._state.dashboardUrl;
	}

	/** Get the Ollama URL for the current runtime */
	public get ollamaUrl(): string {
		return this._state.ollamaUrl;
	}

	// ─── Lifecycle ────────────────────────────────────────────────────────

	/**
	 * Initialize: detect runtime, set up port-forwarding, start health monitor
	 */
	public async initialize(): Promise<void> {
		this._log('Initializing SLATE Runtime Adapter...');
		this._updateStatusBar('detecting');

		// Detect which runtime is available
		const backend = await this._detectRuntime();
		this._state.backend = backend;
		this._log(`Detected runtime: ${backend}`);

		// Set up connectivity for the detected runtime
		await this._setupRuntime(backend);

		// Start health monitoring
		this._startHealthMonitor();

		this._statusBarItem.show();
		this._onStateChange.fire(this._state);
	}

	/**
	 * Shut down: stop port-forwards, stop health monitor
	 */
	public async shutdown(): Promise<void> {
		this._log('Shutting down runtime adapter...');
		this._stopHealthMonitor();
		this._stopAllPortForwards();
		this._statusBarItem.hide();
	}

	// ─── Runtime Detection ──────────────────────────────────────────────

	/**
	 * Detect which runtime backend is available.
	 * Priority: K8s → Docker → Local → None
	 */
	private async _detectRuntime(): Promise<RuntimeBackend> {
		// 1. Check Kubernetes
		const k8sAvailable = await this._checkK8s();
		if (k8sAvailable) {
			this._log('Kubernetes runtime detected — SLATE namespace has running pods');
			return 'kubernetes';
		}

		// 2. Check Docker Compose
		const dockerAvailable = await this._checkDocker();
		if (dockerAvailable) {
			this._log('Docker runtime detected — SLATE containers running');
			return 'docker';
		}

		this._log('No K8s or Docker runtime detected');
		return 'none';
	}

	/**
	 * Check if K8s cluster has SLATE pods running
	 */
	private async _checkK8s(): Promise<boolean> {
		try {
			const result = await this._execTimeout(
				'kubectl get pods -n slate -o jsonpath="{.items[?(@.status.phase==\'Running\')].metadata.name}" 2>&1',
				DETECTION_TIMEOUT
			);
			if (result.exitCode === 0 && result.stdout.trim().length > 0) {
				const pods = result.stdout.trim().split(/\s+/).filter(Boolean);
				this._state.podCount = pods.length;
				return pods.length >= 3; // Need at least dashboard + ollama + chromadb
			}
		} catch {
			// kubectl not available or cluster unreachable
		}
		return false;
	}

	/**
	 * Check if Docker Compose SLATE services are running
	 */
	private async _checkDocker(): Promise<boolean> {
		try {
			const result = await this._execTimeout(
				'docker compose ps --format json 2>&1',
				DETECTION_TIMEOUT
			);
			if (result.exitCode === 0 && result.stdout.includes('slate')) {
				return true;
			}
			// Also check docker-compose (v1)
			const resultV1 = await this._execTimeout(
				'docker-compose ps 2>&1',
				DETECTION_TIMEOUT
			);
			if (resultV1.exitCode === 0 && resultV1.stdout.includes('slate')) {
				return true;
			}
		} catch {
			// Docker not available
		}
		return false;
	}

	// ─── Runtime Setup ──────────────────────────────────────────────────

	/**
	 * Set up connectivity for the detected runtime
	 */
	private async _setupRuntime(backend: RuntimeBackend): Promise<void> {
		switch (backend) {
			case 'kubernetes':
				await this._setupK8sPortForwards();
				this._state.dashboardUrl = `http://127.0.0.1:${ACTIVE_PORTS['dashboard'] ?? K8S_PORT_MAP.dashboard.localPort}`;
				this._state.ollamaUrl = `http://127.0.0.1:${ACTIVE_PORTS['ollama'] ?? K8S_PORT_MAP.ollama.localPort}`;
				this._state.chromaDbUrl = `http://127.0.0.1:${ACTIVE_PORTS['chromadb'] ?? K8S_PORT_MAP.chromadb.localPort}`;
				break;

			case 'docker':
				// Docker services are already exposed via Docker Desktop WSL relay
				this._state.dashboardUrl = 'http://127.0.0.1:8080';
				this._state.ollamaUrl = 'http://127.0.0.1:11434';
				this._state.chromaDbUrl = 'http://127.0.0.1:8000';
				break;

			case 'none':
				this._state.dashboardUrl = 'http://127.0.0.1:8080';
				this._state.ollamaUrl = 'http://127.0.0.1:11434';
				this._state.chromaDbUrl = 'http://127.0.0.1:8000';
				void vscode.window.showWarningMessage(
					'SLATE: No runtime detected. Deploy via K8s or Docker to enable dashboard.',
					'K8s Deploy', 'Docker Up'
				).then(action => {
					if (action === 'K8s Deploy') {
						void vscode.commands.executeCommand('workbench.action.tasks.runTask', 'SLATE: K8s Deploy');
					} else if (action === 'Docker Up') {
						void vscode.commands.executeCommand('workbench.action.tasks.runTask', 'SLATE: Docker Up (Dev)');
					}
				});
				break;
		}

		// Verify connectivity
		await this._verifyConnectivity();
	}

	// ─── K8s Port Forwarding ────────────────────────────────────────────

	/**
	 * Set up kubectl port-forward for all SLATE K8s services.
	 * Uses 127.0.0.1 binding (local-only, per SLATE security rules).
	 */
	private async _setupK8sPortForwards(): Promise<void> {
		this._log('Setting up K8s port-forwards...');

		// Check if ports are already in use (by Docker or other processes)
		const portConflicts = await this._checkPortConflicts();
		if (portConflicts.length > 0) {
			this._log(`Port conflicts detected: ${portConflicts.join(', ')}`);
			// Only forward ports that aren't already in use
			// The conflicting ports might already be served by Docker compose
		}

		for (const [name, config] of Object.entries(K8S_PORT_MAP)) {
			if (portConflicts.includes(config.localPort)) {
				this._log(`Skipping port-forward for ${name} — port ${config.localPort} already in use (may be served by Docker)`);

				// Verify the existing port is actually serving the right content
				const isSlate = await this._httpPing(
					`http://127.0.0.1:${config.localPort}/api/status`,
					2000
				);
				if (isSlate) {
					this._log(`Port ${config.localPort} is serving SLATE content — OK`);
				}
				continue;
			}

			await this._startPortForward(name, config.svc, config.localPort, config.remotePort);
		}
	}

	/**
	 * Start a single kubectl port-forward
	 */
	private async _startPortForward(
		name: string,
		svc: string,
		localPort: number,
		remotePort: number
	): Promise<void> {
		// Kill existing forward for this service
		this._stopPortForward(name);

		const cmd = `kubectl -n ${K8S_NAMESPACE} port-forward svc/${svc} 127.0.0.1:${localPort}:${remotePort}`;
		this._log(`Starting port-forward: ${name} → ${cmd}`);

		try {
			const proc = cp.spawn('kubectl', [
				'-n', K8S_NAMESPACE,
				'port-forward',
				`svc/${svc}`,
				`127.0.0.1:${localPort}:${remotePort}`,
			], {
				stdio: ['ignore', 'pipe', 'pipe'],
				windowsHide: true,
				detached: false,
			});

			proc.stdout?.on('data', (data: Buffer) => {
				this._log(`[${name}] ${data.toString().trim()}`);
			});

			proc.stderr?.on('data', (data: Buffer) => {
				const msg = data.toString().trim();
				if (msg && !msg.includes('Handling connection')) {
					this._log(`[${name}] ERROR: ${msg}`);
				}
			});

			proc.on('exit', (code) => {
				this._log(`[${name}] port-forward exited with code ${code}`);
				this._portForwardProcesses.delete(name);
			});

			this._portForwardProcesses.set(name, proc);

			if (name === 'dashboard') {
				this._state.portForwardPid = proc.pid ?? null;
			}

			// Give it a moment to establish
			await new Promise(resolve => setTimeout(resolve, 1500));

		} catch (err) {
			this._log(`Failed to start port-forward for ${name}: ${err}`);
		}
	}

	/**
	 * Stop a specific port-forward
	 */
	private _stopPortForward(name: string): void {
		const proc = this._portForwardProcesses.get(name);
		if (proc && !proc.killed) {
			proc.kill();
			this._portForwardProcesses.delete(name);
			this._log(`Stopped port-forward: ${name}`);
		}
	}

	/**
	 * Stop all port-forwards
	 */
	private _stopAllPortForwards(): void {
		for (const [name, proc] of this._portForwardProcesses.entries()) {
			if (!proc.killed) {
				proc.kill();
				this._log(`Stopped port-forward: ${name}`);
			}
		}
		this._portForwardProcesses.clear();
		this._state.portForwardPid = null;
	}

	/**
	 * Check which local ports are already in use
	 */
	private async _checkPortConflicts(): Promise<number[]> {
		const conflicts: number[] = [];
		const portsToCheck = Object.values(K8S_PORT_MAP).map(c => c.localPort);

		for (const port of portsToCheck) {
			const inUse = await this._isPortInUse(port);
			if (inUse) {
				conflicts.push(port);
			}
		}
		return conflicts;
	}

	/**
	 * Check if a port is already in use
	 */
	private _isPortInUse(port: number): Promise<boolean> {
		return new Promise((resolve) => {
			const req = http.get(`http://127.0.0.1:${port}/`, { timeout: 2000 }, (res) => {
				resolve(true);
				res.resume();
			});
			req.on('error', () => resolve(false));
			req.on('timeout', () => {
				req.destroy();
				resolve(false);
			});
		});
	}

	// ─── Health Monitoring ──────────────────────────────────────────────

	/**
	 * Start periodic health checks
	 */
	private _startHealthMonitor(): void {
		this._healthInterval = setInterval(() => {
			void this._healthCheck();
		}, HEALTH_CHECK_INTERVAL);

		// Run immediately
		void this._healthCheck();
	}

	/**
	 * Stop health monitoring
	 */
	private _stopHealthMonitor(): void {
		if (this._healthInterval) {
			clearInterval(this._healthInterval);
			this._healthInterval = undefined;
		}
	}

	/**
	 * Run a health check on all services
	 */
	private async _healthCheck(): Promise<void> {
		this._state.lastCheck = Date.now();

		const services: ServiceStatus[] = [];
		const checks = [
			{ name: 'Dashboard',    url: `${this._state.dashboardUrl}/api/status`, port: 8080 },
			{ name: 'Ollama',       url: `${this._state.ollamaUrl}/api/tags`,      port: 11434 },
			{ name: 'ChromaDB',     url: `${this._state.chromaDbUrl}/api/v1/heartbeat`, port: 8000 },
		];

		let allHealthy = true;

		for (const check of checks) {
			const healthy = await this._httpPing(check.url, 3000);
			services.push({
				name: check.name,
				url: check.url,
				port: check.port,
				healthy,
			});
			if (!healthy) { allHealthy = false; }
		}

		this._state.services = services;
		this._state.healthy = allHealthy;

		// Update status bar
		if (allHealthy) {
			this._updateStatusBar('healthy');
		} else if (services.some(s => s.healthy)) {
			this._updateStatusBar('degraded');
		} else {
			this._updateStatusBar('offline');
		}

		// If K8s port-forwards died, restart them
		if (this._state.backend === 'kubernetes' && !allHealthy) {
			await this._restartDeadPortForwards();
		}

		this._onStateChange.fire(this._state);
	}

	/**
	 * Restart any port-forwards that have died
	 */
	private async _restartDeadPortForwards(): Promise<void> {
		for (const [name, config] of Object.entries(K8S_PORT_MAP)) {
			const proc = this._portForwardProcesses.get(name);
			if (!proc || proc.killed) {
				const portInUse = await this._isPortInUse(config.localPort);
				if (!portInUse) {
					this._log(`Restarting dead port-forward: ${name}`);
					await this._startPortForward(name, config.svc, config.localPort, config.remotePort);
				}
			}
		}
	}

	/**
	 * Verify connectivity to the dashboard after setup
	 */
	private async _verifyConnectivity(): Promise<void> {
		const healthy = await this._httpPing(`${this._state.dashboardUrl}/api/status`, 5000);
		this._state.healthy = healthy;

		if (healthy) {
			this._log(`✓ Dashboard accessible at ${this._state.dashboardUrl}`);
		} else {
			this._log(`✗ Dashboard NOT accessible at ${this._state.dashboardUrl}`);
		}
	}

	// ─── Public API ─────────────────────────────────────────────────────

	/**
	 * Force re-detect runtime and reconnect
	 */
	public async redetect(): Promise<void> {
		this._log('Re-detecting runtime...');
		this._stopAllPortForwards();
		this._state.backend = 'none';
		this._state.healthy = false;
		this._updateStatusBar('detecting');

		const backend = await this._detectRuntime();
		this._state.backend = backend;
		await this._setupRuntime(backend);
		this._onStateChange.fire(this._state);
	}

	/**
	 * Get a summary string for display
	 */
	public getSummary(): string {
		const { backend, healthy, podCount, services } = this._state;
		const healthIcon = healthy ? '✓' : '✗';
		const svcSummary = services.map(s => `${s.healthy ? '●' : '○'} ${s.name}`).join(', ');

		switch (backend) {
			case 'kubernetes':
				return `${healthIcon} K8s Runtime — ${podCount} pods — ${svcSummary}`;
			case 'docker':
				return `${healthIcon} Docker Runtime — ${svcSummary}`;

			case 'none':
				return '✗ No Runtime — Deploy via K8s or Docker';
		}
	}

	// ─── Status Bar ─────────────────────────────────────────────────────

	private _updateStatusBar(status: 'detecting' | 'healthy' | 'degraded' | 'offline'): void {
		switch (status) {
			case 'detecting':
				this._statusBarItem.text = '$(sync~spin) SLATE Runtime';
				this._statusBarItem.tooltip = 'Detecting SLATE runtime...';
				this._statusBarItem.backgroundColor = undefined;
				break;
			case 'healthy':
				this._statusBarItem.text = `$(cloud) SLATE ${this._runtimeLabel()}`;
				this._statusBarItem.tooltip = `SLATE Runtime: ${this._state.backend}\n${this.getSummary()}\nClick for details`;
				this._statusBarItem.backgroundColor = undefined;
				break;
			case 'degraded':
				this._statusBarItem.text = `$(warning) SLATE ${this._runtimeLabel()}`;
				this._statusBarItem.tooltip = `SLATE Runtime: ${this._state.backend} (degraded)\n${this.getSummary()}\nClick for details`;
				this._statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
				break;
			case 'offline':
				this._statusBarItem.text = '$(circle-slash) SLATE Offline';
				this._statusBarItem.tooltip = 'SLATE Runtime offline\nClick to reconnect';
				this._statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
				break;
		}
	}

	private _runtimeLabel(): string {
		switch (this._state.backend) {
			case 'kubernetes': return 'K8s';
			case 'docker': return 'Docker';

			default: return '';
		}
	}

	// ─── Utilities ──────────────────────────────────────────────────────

	/**
	 * HTTP ping — returns true if endpoint responds with 2xx/3xx
	 */
	private _httpPing(url: string, timeout: number): Promise<boolean> {
		return new Promise((resolve) => {
			try {
				const req = http.get(url, { timeout }, (res) => {
					resolve((res.statusCode ?? 500) < 400);
					res.resume();
				});
				req.on('error', () => resolve(false));
				req.on('timeout', () => {
					req.destroy();
					resolve(false);
				});
			} catch {
				resolve(false);
			}
		});
	}

	/**
	 * Execute a command with timeout
	 */
	private _execTimeout(cmd: string, timeout: number): Promise<{ exitCode: number; stdout: string; stderr: string }> {
		return new Promise((resolve) => {
			cp.exec(cmd, { timeout, encoding: 'utf-8', windowsHide: true }, (err, stdout, stderr) => {
				resolve({
					exitCode: err ? (err as any).code ?? 1 : 0,
					stdout: stdout ?? '',
					stderr: stderr ?? '',
				});
			});
		});
	}

	private _log(message: string): void {
		const timestamp = new Date().toISOString();
		this._outputChannel.appendLine(`[${timestamp}] ${message}`);
	}

	public dispose(): void {
		this._stopHealthMonitor();
		this._stopAllPortForwards();
		this._statusBarItem.dispose();
		this._outputChannel.dispose();
		this._onStateChange.dispose();
	}
}
