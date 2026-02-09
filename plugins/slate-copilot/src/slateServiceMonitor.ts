// Modified: 2026-02-10T03:00:00Z | Author: Claude Opus 4.5 | Change: Add runtime state change notifications and event emitter
// DEPRECATED: 2026-02-10 | Reason: SlateServiceMonitor standalone server spawning removed. Replaced by SlateRuntimeAdapter (slateRuntimeAdapter.ts)
import * as vscode from 'vscode';
import { SlateRuntimeAdapter, RuntimeState } from './slateRuntimeAdapter';

/**
 * Service Monitor for SLATE — K8s/Docker Runtime Bridge
 * =====================================================
 * DEPRECATED: The old standalone server spawning has been removed.
 * This module now delegates to SlateRuntimeAdapter which manages
 * K8s port-forwarding and Docker runtime detection.
 *
 * The dashboard is NO LONGER served by a local Python process.
 * It is served by the Kubernetes cluster (kubectl port-forward)
 * or Docker Compose (WSL relay) runtime.
 */
export class SlateServiceMonitor implements vscode.Disposable {
	private _runtimeAdapter: SlateRuntimeAdapter;
	private _disposables: vscode.Disposable[] = [];
	private _onStateChange = new vscode.EventEmitter<RuntimeState>();
	public readonly onStateChange = this._onStateChange.event;
	private _lastBackend: string = 'none';

	constructor() {
		this._runtimeAdapter = new SlateRuntimeAdapter();

		// Forward state changes from runtime adapter
		this._disposables.push(
			this._runtimeAdapter.onStateChange((state) => {
				this._onStateChange.fire(state);
				this._handleStateChange(state);
			})
		);
	}

	/**
	 * Handle runtime state changes with user notifications
	 */
	private _handleStateChange(state: RuntimeState): void {
		// Notify on backend change
		if (state.backend !== this._lastBackend) {
			if (state.backend === 'kubernetes') {
				vscode.window.setStatusBarMessage('$(cloud) SLATE: Connected to K8s cluster', 5000);
			} else if (state.backend === 'docker') {
				vscode.window.setStatusBarMessage('$(package) SLATE: Connected to Docker runtime', 5000);
			} else if (state.backend === 'none' && this._lastBackend !== 'none') {
				vscode.window.setStatusBarMessage('$(circle-slash) SLATE: Runtime disconnected', 5000);
			}
			this._lastBackend = state.backend;
		}

		// Notify on health degradation
		if (!state.healthy && this._lastBackend !== 'none') {
			const unhealthy = state.services.filter(s => !s.healthy).map(s => s.name);
			if (unhealthy.length > 0) {
				vscode.window.setStatusBarMessage(`$(warning) SLATE: ${unhealthy.join(', ')} offline`, 5000);
			}
		}
	}

	/** Get the runtime adapter instance */
	public get runtimeAdapter(): SlateRuntimeAdapter {
		return this._runtimeAdapter;
	}

	/**
	 * Start the service monitor — delegates to runtime adapter
	 */
	public async start(): Promise<void> {
		await this._runtimeAdapter.initialize();
	}

	/**
	 * Stop the service monitor
	 */
	public async stop(): Promise<void> {
		await this._runtimeAdapter.shutdown();
	}

	/**
	 * Toggle service — show runtime info
	 */
	public async toggleService(): Promise<void> {
		const state = this._runtimeAdapter.state;
		const summary = this._runtimeAdapter.getSummary();

		if (state.healthy) {
			const action = await vscode.window.showInformationMessage(
				`SLATE Runtime: ${summary}`,
				'Open Dashboard',
				'Re-detect Runtime',
				'Runtime Details'
			);

			if (action === 'Open Dashboard') {
				void vscode.env.openExternal(vscode.Uri.parse(state.dashboardUrl));
			} else if (action === 'Re-detect Runtime') {
				await this._runtimeAdapter.redetect();
				void vscode.window.showInformationMessage(`SLATE Runtime: ${this._runtimeAdapter.getSummary()}`);
			} else if (action === 'Runtime Details') {
				const detail = [
					`Backend: ${state.backend}`,
					`Dashboard: ${state.dashboardUrl}`,
					`Ollama: ${state.ollamaUrl}`,
					`ChromaDB: ${state.chromaDbUrl}`,
					`Pods: ${state.podCount}`,
					`Healthy: ${state.healthy}`,
					`Port Forward PID: ${state.portForwardPid ?? 'N/A'}`,
					'',
					'Services:',
					...state.services.map(s => `  ${s.healthy ? '●' : '○'} ${s.name} — ${s.url}`),
				].join('\n');
				void vscode.window.showInformationMessage(detail, { modal: true });
			}
		} else {
			const action = await vscode.window.showWarningMessage(
				`SLATE Runtime offline: ${summary}`,
				'Re-detect Runtime',
				'K8s Deploy',
				'Docker Up'
			);

			if (action === 'Re-detect Runtime') {
				await this._runtimeAdapter.redetect();
			} else if (action === 'K8s Deploy') {
				void vscode.commands.executeCommand('workbench.action.tasks.runTask', 'SLATE: K8s Deploy');
			} else if (action === 'Docker Up') {
				void vscode.commands.executeCommand('workbench.action.tasks.runTask', 'SLATE: Docker Up (Dev)');
			}
		}
	}

	/**
	 * Force re-detect runtime
	 */
	public async forceRestart(): Promise<void> {
		await this._runtimeAdapter.redetect();
	}

	public dispose(): void {
		this._disposables.forEach(d => d.dispose());
		this._onStateChange.dispose();
		this._runtimeAdapter.dispose();
	}
}

/**
 * Create and register the service monitor (with runtime adapter)
 */
export function registerServiceMonitor(context: vscode.ExtensionContext): SlateServiceMonitor {
	const monitor = new SlateServiceMonitor();

	context.subscriptions.push(monitor);

	// Register commands
	context.subscriptions.push(
		vscode.commands.registerCommand('slate.toggleService', () => {
			void monitor.toggleService();
		})
	);

	context.subscriptions.push(
		vscode.commands.registerCommand('slate.restartDashboard', () => {
			void monitor.forceRestart();
		})
	);

	context.subscriptions.push(
		vscode.commands.registerCommand('slate.runtimeInfo', () => {
			void monitor.toggleService();
		})
	);

	// Auto-start the monitor (async — detects runtime and sets up port-forwarding)
	void monitor.start();

	return monitor;
}
