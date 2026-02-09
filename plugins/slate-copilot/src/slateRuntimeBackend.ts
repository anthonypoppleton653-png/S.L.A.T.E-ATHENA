// Modified: 2026-02-08T23:00:00Z | Author: COPILOT | Change: Rebuild runtime backend — K8s/Docker only, local fallback removed per SLATE container-first architecture
// SLATE command execution routes through containerized infrastructure:
//   1. K8s Backend (primary) — HTTP to slate-copilot-bridge-svc in the cluster
//   2. Docker Backend (secondary) — docker exec into SLATE container
//   No local fallback — K8s or Docker is REQUIRED per SLATE architecture.

import * as vscode from 'vscode';
import * as http from 'http';
import * as cp from 'child_process';

// ─── Runtime Backend Types ─────────────────────────────────────────────
// Modified: 2026-02-10T04:00:00Z | Author: COPILOT | Change: Remove 'local' from RuntimeBackend, K8s/Docker only
export type RuntimeBackend = 'kubernetes' | 'docker' | 'none';

export interface RuntimeStatus {
	backend: RuntimeBackend;
	healthy: boolean;
	endpoint?: string;
	version?: string;
	lastCheck: number;
	details?: string;
}

export interface RuntimeConfig {
	/** Preferred backend — auto-detected if not set */
	preferredBackend?: RuntimeBackend;
	/** K8s copilot bridge service URL */
	k8sEndpoint: string;
	/** Docker SLATE container name */
	dockerContainer: string;
	/** Health check interval (ms) */
	healthCheckInterval: number;
	/** Command timeout (ms) */
	commandTimeout: number;
}

// ─── Constants ───────────────────────────────────────────────────────────────
const DEFAULT_K8S_ENDPOINT = 'http://127.0.0.1:8083';
const DEFAULT_DOCKER_CONTAINER = 'slate';
const HEALTH_CHECK_INTERVAL = 30_000;
const COMMAND_TIMEOUT = 90_000;
const COMMAND_TIMEOUT_LONG = 300_000;

// ─── Runtime Backend Manager ─────────────────────────────────────────────────
export class SlateRuntimeBackend {
	private _status: RuntimeStatus = {
		backend: 'none',
		healthy: false,
		lastCheck: 0,
	};
	private _config: RuntimeConfig;
	private _healthTimer: NodeJS.Timeout | undefined;
	private _statusBarItem: vscode.StatusBarItem | undefined;
	private _onStatusChange = new vscode.EventEmitter<RuntimeStatus>();
	public readonly onStatusChange = this._onStatusChange.event;

	constructor() {
		this._config = {
			k8sEndpoint: DEFAULT_K8S_ENDPOINT,
			dockerContainer: DEFAULT_DOCKER_CONTAINER,
			healthCheckInterval: HEALTH_CHECK_INTERVAL,
			commandTimeout: COMMAND_TIMEOUT,
		};
	}

	/** Initialize the runtime backend — detect best available backend */
	async activate(context: vscode.ExtensionContext): Promise<void> {
		// Read user preference from settings
		const config = vscode.workspace.getConfiguration('slate');
		const preferred = config.get<string>('runtime.backend', 'auto');
		const k8sEndpoint = config.get<string>('runtime.k8sEndpoint', DEFAULT_K8S_ENDPOINT);
		const dockerContainer = config.get<string>('runtime.dockerContainer', DEFAULT_DOCKER_CONTAINER);

		this._config.k8sEndpoint = k8sEndpoint;
		this._config.dockerContainer = dockerContainer;

		if (preferred !== 'auto') {
			this._config.preferredBackend = preferred as RuntimeBackend;
		}

		// Create status bar item
		this._statusBarItem = vscode.window.createStatusBarItem(
			vscode.StatusBarAlignment.Left,
			99
		);
		this._statusBarItem.command = 'slate.switchRuntime';
		context.subscriptions.push(this._statusBarItem);

		// Register switch command
		context.subscriptions.push(
			vscode.commands.registerCommand('slate.switchRuntime', () => this._showRuntimePicker())
		);

		// Initial detection
		await this.detectBackend();

		// Start health check loop
		this._healthTimer = setInterval(() => this.detectBackend(), this._config.healthCheckInterval);
		context.subscriptions.push({ dispose: () => clearInterval(this._healthTimer) });
	}

	/** Get current runtime status */
	get status(): RuntimeStatus {
		return { ...this._status };
	}

	/** Get current backend type */
	get backend(): RuntimeBackend {
		return this._status.backend;
	}

	/** Auto-detect the best available backend */
	async detectBackend(): Promise<RuntimeBackend> {
		// If user has a preferred backend, try it first
		if (this._config.preferredBackend) {
			const healthy = await this._checkHealth(this._config.preferredBackend);
			if (healthy) {
				this._updateStatus(this._config.preferredBackend, true);
				return this._config.preferredBackend;
			}
		}

		// Auto-detection order: K8s → Docker → Local
		// 1. Try K8s copilot bridge
		if (await this._checkHealth('kubernetes')) {
			this._updateStatus('kubernetes', true);
			return 'kubernetes';
		}

		// 2. Try Docker container
		if (await this._checkHealth('docker')) {
			this._updateStatus('docker', true);
			return 'docker';
		}

		// No runtime available — K8s or Docker deployment required
		this._updateStatus('none', false, 'No K8s or Docker runtime detected. Run "SLATE: K8s Deploy" or "SLATE: Docker Up".');
		vscode.window.showWarningMessage(
			'SLATE: No K8s or Docker runtime detected. Deploy SLATE to continue.',
			'K8s Deploy', 'Docker Up'
		).then(action => {
			if (action === 'K8s Deploy') {
				void vscode.commands.executeCommand('workbench.action.tasks.runTask', 'SLATE: K8s Deploy');
			} else if (action === 'Docker Up') {
				void vscode.commands.executeCommand('workbench.action.tasks.runTask', 'SLATE: Docker Up (Dev)');
			}
		});
		return 'none';
	}

	/** Execute a SLATE command via the active backend */
	async exec(command: string, token: vscode.CancellationToken, long = false): Promise<string> {
		const timeout = long ? COMMAND_TIMEOUT_LONG : this._config.commandTimeout;

		// Re-detect if stale (>60s since last check)
		if (Date.now() - this._status.lastCheck > 60_000) {
			await this.detectBackend();
		}

		switch (this._status.backend) {
			case 'kubernetes':
				return this._execK8s(command, token, timeout);
			case 'docker':
				return this._execDocker(command, token, timeout);
			default:
				throw new Error(
					'SLATE runtime unavailable — no K8s or Docker backend detected.\n' +
					'Deploy SLATE: run task "SLATE: K8s Deploy" or "SLATE: Docker Up (Dev)".'
				);
		}
	}

	// ─── K8s Backend ─────────────────────────────────────────────────────────

	private async _execK8s(command: string, token: vscode.CancellationToken, timeoutMs: number): Promise<string> {
		return new Promise<string>((resolve, reject) => {
			if (token.isCancellationRequested) {
				reject(new Error('Cancelled'));
				return;
			}

			const payload = JSON.stringify({ command, timeout: timeoutMs });
			const url = new URL(`${this._config.k8sEndpoint}/api/exec`);

			const req = http.request(
				{
					hostname: url.hostname,
					port: url.port,
					path: url.pathname,
					method: 'POST',
					headers: {
						'Content-Type': 'application/json',
						'Content-Length': Buffer.byteLength(payload),
					},
					timeout: timeoutMs + 5000,
				},
				(res) => {
					let body = '';
					res.on('data', (chunk: Buffer) => { body += chunk.toString('utf-8'); });
					res.on('end', () => {
						try {
							const result = JSON.parse(body);
							if (result.error) {
								resolve(`[K8s error]: ${result.error}\n${result.output ?? ''}`);
							} else {
								resolve(result.output ?? body);
							}
						} catch {
							resolve(body);
						}
					});
				}
			);

			req.on('error', (err) => {
				// Fallback to Docker on K8s failure
				console.warn(`K8s backend failed, falling back to Docker: ${err.message}`);
				this._checkHealth('docker').then((dockerOk) => {
					if (dockerOk) {
						this._updateStatus('docker', true, 'K8s unreachable — fell back to Docker');
						this._execDocker(command, token, timeoutMs).then(resolve, reject);
					} else {
						reject(new Error(`K8s backend failed: ${err.message}. No Docker fallback available. Deploy SLATE to K8s or Docker.`));
					}
				});
			});

			req.on('timeout', () => {
				req.destroy();
				reject(new Error(`K8s command timed out after ${timeoutMs / 1000}s`));
			});

			const disposable = token.onCancellationRequested(() => {
				req.destroy();
				reject(new Error('Cancelled'));
			});

			req.write(payload);
			req.end();

			// Cleanup
			req.on('close', () => disposable.dispose());
		});
	}

	// ─── Docker Backend ──────────────────────────────────────────────────────

	private async _execDocker(command: string, token: vscode.CancellationToken, timeoutMs: number): Promise<string> {
		return new Promise<string>((resolve, reject) => {
			if (token.isCancellationRequested) {
				reject(new Error('Cancelled'));
				return;
			}

			const container = this._config.dockerContainer;
			const args = ['exec', '-i', container, 'python', ...this._parseArgs(command)];

			let proc: cp.ChildProcess;
			try {
				proc = cp.spawn('docker', args, {
					stdio: ['ignore', 'pipe', 'pipe'],
					windowsHide: true,
				});
			} catch (err) {
				reject(new Error(`Docker backend unavailable: ${err}. Ensure SLATE container is running.`));
				return;
			}

			let stdout = '';
			let stderr = '';
			let settled = false;

			const settle = (val: string) => { if (!settled) { settled = true; clearTimeout(timer); disposable.dispose(); resolve(val); } };
			const fail = (err: Error) => { if (!settled) { settled = true; clearTimeout(timer); disposable.dispose(); reject(err); } };

			proc.stdout!.on('data', (d: Buffer) => { stdout += d.toString('utf-8'); });
			proc.stderr!.on('data', (d: Buffer) => { stderr += d.toString('utf-8'); });

			const disposable = token.onCancellationRequested(() => {
				if (!proc.killed) { proc.kill('SIGTERM'); }
				fail(new Error('Cancelled'));
			});

			proc.on('close', (code) => {
				if (code === 0) {
					settle(stdout.trim() || '[completed — no output]');
				} else {
					const parts: string[] = [];
					if (stdout.trim()) { parts.push(stdout.trim()); }
					if (stderr.trim()) { parts.push(`[stderr]: ${stderr.trim()}`); }
					settle(parts.join('\n') || `[docker exec exited with code ${code}]`);
				}
			});

			proc.on('error', (err) => {
				fail(new Error(`Docker exec error: ${err.message}. Ensure SLATE container '${container}' is running.`));
			});

			const timer = setTimeout(() => {
				if (!proc.killed) { proc.kill('SIGTERM'); }
				settle((stdout.trim() ? stdout.trim() + '\n' : '') + `[timeout after ${timeoutMs / 1000}s]`);
			}, timeoutMs);
		});
	}

	// ─── Health Checks ───────────────────────────────────────────────────────

	private async _checkHealth(backend: RuntimeBackend): Promise<boolean> {
		switch (backend) {
			case 'kubernetes':
				return this._checkK8sHealth();
			case 'docker':
				return this._checkDockerHealth();
			default:
				return false;
		}
	}

	private async _checkK8sHealth(): Promise<boolean> {
		return new Promise<boolean>((resolve) => {
			const url = new URL(`${this._config.k8sEndpoint}/api/health`);
			const req = http.get(
				{ hostname: url.hostname, port: url.port, path: url.pathname, timeout: 5000 },
				(res) => {
					let body = '';
					res.on('data', (chunk: Buffer) => { body += chunk.toString(); });
					res.on('end', () => {
						try {
							const data = JSON.parse(body);
							this._status.version = data.version;
							resolve(res.statusCode === 200);
						} catch {
							resolve(res.statusCode === 200);
						}
					});
				}
			);
			req.on('error', () => resolve(false));
			req.on('timeout', () => { req.destroy(); resolve(false); });
		});
	}

	private async _checkDockerHealth(): Promise<boolean> {
		return new Promise<boolean>((resolve) => {
			const proc = cp.spawn('docker', ['inspect', '--format', '{{.State.Running}}', this._config.dockerContainer], {
				stdio: ['ignore', 'pipe', 'pipe'],
				windowsHide: true,
			});
			let out = '';
			proc.stdout!.on('data', (d: Buffer) => { out += d.toString(); });
			proc.on('close', (code) => {
				resolve(code === 0 && out.trim() === 'true');
			});
			proc.on('error', () => resolve(false));
			setTimeout(() => { if (!proc.killed) { proc.kill(); } resolve(false); }, 5000);
		});
	}

	// ─── Status Management ───────────────────────────────────────────────────

	private _updateStatus(backend: RuntimeBackend, healthy: boolean, details?: string): void {
		const changed = this._status.backend !== backend || this._status.healthy !== healthy;
		this._status = {
			backend,
			healthy,
			endpoint: backend === 'kubernetes' ? this._config.k8sEndpoint
				: backend === 'docker' ? `docker://${this._config.dockerContainer}`
				: 'none',
			version: this._status.version,
			lastCheck: Date.now(),
			details,
		};

		this._updateStatusBar();

		if (changed) {
			this._onStatusChange.fire(this._status);
		}
	}

	private _updateStatusBar(): void {
		if (!this._statusBarItem) { return; }

		const icons: Record<RuntimeBackend, string> = {
			kubernetes: '$(cloud)',
			docker: '$(package)',
			none: '$(circle-slash)',
		};

		const labels: Record<RuntimeBackend, string> = {
			kubernetes: 'K8s',
			docker: 'Docker',
			none: 'Offline',
		};

		const healthIcon = this._status.healthy ? '' : ' $(warning)';
		this._statusBarItem.text = `${icons[this._status.backend]} SLATE: ${labels[this._status.backend]}${healthIcon}`;
		this._statusBarItem.tooltip = [
			`SLATE Runtime: ${labels[this._status.backend]}`,
			`Healthy: ${this._status.healthy ? 'Yes' : 'No'}`,
			`Endpoint: ${this._status.endpoint ?? 'N/A'}`,
			this._status.details ? `Details: ${this._status.details}` : '',
			'',
			'Click to switch runtime backend',
		].filter(Boolean).join('\n');
		this._statusBarItem.backgroundColor = this._status.healthy
			? undefined
			: new vscode.ThemeColor('statusBarItem.warningBackground');
		this._statusBarItem.show();
	}

	private async _showRuntimePicker(): Promise<void> {
		const items: vscode.QuickPickItem[] = [
			{
				label: '$(cloud) Kubernetes',
				description: this._status.backend === 'kubernetes' ? '(active)' : '',
				detail: `Route commands to K8s copilot-bridge-svc at ${this._config.k8sEndpoint}`,
			},
			{
				label: '$(package) Docker',
				description: this._status.backend === 'docker' ? '(active)' : '',
				detail: `Execute inside Docker container '${this._config.dockerContainer}'`,
			},
			{
				label: '$(sync) Auto-detect',
				description: '',
				detail: 'Auto-detect best available backend (K8s > Docker)',
			},
			{
				label: '$(rocket) Deploy to K8s',
				description: '',
				detail: 'Deploy SLATE to Kubernetes cluster',
			},
			{
				label: '$(server) Docker Up',
				description: '',
				detail: 'Start SLATE Docker Compose services',
			},
		];

		const pick = await vscode.window.showQuickPick(items, {
			placeHolder: 'Select SLATE runtime backend',
			title: 'SLATE Runtime Backend',
		});

		if (!pick) { return; }

		if (pick.label.includes('Auto-detect')) {
			this._config.preferredBackend = undefined;
			await vscode.workspace.getConfiguration('slate').update('runtime.backend', 'auto', vscode.ConfigurationTarget.Global);
			await this.detectBackend();
			vscode.window.showInformationMessage(`SLATE runtime auto-detected: ${this._status.backend}`);
		} else if (pick.label.includes('Kubernetes') && !pick.label.includes('Deploy')) {
			this._config.preferredBackend = 'kubernetes';
			await vscode.workspace.getConfiguration('slate').update('runtime.backend', 'kubernetes', vscode.ConfigurationTarget.Global);
			await this.detectBackend();
		} else if (pick.label.includes('Docker') && !pick.label.includes('Up')) {
			this._config.preferredBackend = 'docker';
			await vscode.workspace.getConfiguration('slate').update('runtime.backend', 'docker', vscode.ConfigurationTarget.Global);
			await this.detectBackend();
		} else if (pick.label.includes('Deploy to K8s')) {
			void vscode.commands.executeCommand('workbench.action.tasks.runTask', 'SLATE: K8s Deploy');
		} else if (pick.label.includes('Docker Up')) {
			void vscode.commands.executeCommand('workbench.action.tasks.runTask', 'SLATE: Docker Up (Dev)');
		}
	}

	// ─── Utilities ───────────────────────────────────────────────────────────

	private _parseArgs(command: string): string[] {
		const args: string[] = [];
		let current = '';
		let inQuote: string | null = null;

		for (let i = 0; i < command.length; i++) {
			const ch = command[i];
			if (inQuote) {
				if (ch === inQuote) { inQuote = null; } else { current += ch; }
			} else if (ch === '"' || ch === "'") {
				inQuote = ch;
			} else if (ch === ' ' || ch === '\t') {
				if (current.length > 0) { args.push(current); current = ''; }
			} else {
				current += ch;
			}
		}
		if (current.length > 0) { args.push(current); }
		return args;
	}

	/** Dispose resources */
	dispose(): void {
		if (this._healthTimer) { clearInterval(this._healthTimer); }
		this._onStatusChange.dispose();
	}
}

/** Singleton instance */
let _runtimeBackend: SlateRuntimeBackend | undefined;

/** Get the global runtime backend instance */
export function getSlateRuntime(): SlateRuntimeBackend {
	if (!_runtimeBackend) {
		_runtimeBackend = new SlateRuntimeBackend();
	}
	return _runtimeBackend;
}

/** Initialize and activate the runtime backend */
export async function activateSlateRuntime(context: vscode.ExtensionContext): Promise<SlateRuntimeBackend> {
	const runtime = getSlateRuntime();
	await runtime.activate(context);
	return runtime;
}
