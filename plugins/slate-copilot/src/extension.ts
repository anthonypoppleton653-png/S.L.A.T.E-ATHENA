// Modified: 2026-02-10T08:00:00Z | Author: COPILOT | Change: v5.3.0 — Add auto-start SLATE systems on VS Code open, Copilot SDK dashboard integration
// Modified: 2026-02-10T02:00:00Z | Author: COPILOT | Change: Replace static DASHBOARD_URL with K8s/Docker runtime adapter — dashboard served by K8s or Docker, not hardcoded local
// Modified: 2026-02-08T22:00:00Z | Author: COPILOT | Change: Add K8s/Docker runtime backend — hybrid execution engine, deprecate local-only execution
import * as vscode from 'vscode';
import * as http from 'http';
import { exec as cpExec, spawn } from 'child_process';
import { registerSlateParticipant } from './slateParticipant';
import { registerSlateTools } from './tools';
import { SlateUnifiedDashboardViewProvider } from './slateUnifiedDashboardView';
import { registerServiceMonitor } from './slateServiceMonitor';
import { registerAgentSdkHooks } from './slateAgentSdkHooks';
import {
	applySchematicBackground,
	registerBackgroundCommands,
	watchForStateChanges
} from './slateSchematicBackground';
import { SlateDiagnosticsProvider } from './slateDiagnostics';
import { SlateTestController } from './slateTestController';
import { SlateTaskProvider } from './slateTaskProvider';
import { SlateCodeLensProvider } from './slateCodeLens';
import { registerGitHubTools } from './slateGitHubIntegration';
import { activateSlateRuntime, getSlateRuntime } from './slateRuntimeBackend';
import { SlateRuntimeAdapter } from './slateRuntimeAdapter';

// DEPRECATED: 2026-02-10 | Reason: Static DASHBOARD_URL replaced by runtime adapter dynamic URL
// const DASHBOARD_URL = 'http://127.0.0.1:8080';
const SLATE_THEME_ID = 'SLATE Dark';

/** Global runtime adapter — provides dynamic URLs for K8s/Docker/local backends */
let slateRuntimeAdapter: SlateRuntimeAdapter | undefined;

/** Get the active runtime adapter */
export function getRuntimeAdapter(): SlateRuntimeAdapter | undefined {
	return slateRuntimeAdapter;
}

/** Get the current dashboard URL from the runtime adapter (falls back to default) */
export function getDashboardUrl(): string {
	return slateRuntimeAdapter?.dashboardUrl ?? 'http://127.0.0.1:8080';
}

/** Get the current Ollama URL from the runtime adapter (falls back to default) */
export function getOllamaUrl(): string {
	return slateRuntimeAdapter?.ollamaUrl ?? 'http://127.0.0.1:11434';
}

/** Status bar item showing SLATE is installed */
let slateStatusBarItem: vscode.StatusBarItem;

export function activate(context: vscode.ExtensionContext) {
	registerSlateTools(context);
	registerSlateParticipant(context);
	registerAgentSdkHooks(context);

	// ─── K8s/Docker Runtime Backend (v5.1.0) ────────────────────────────────
	// Modified: 2026-02-10T08:00:00Z | Author: COPILOT | Change: Add auto-start SLATE systems after runtime detection
	// Container-first execution: auto-detects K8s → Docker backends (no local)
	activateSlateRuntime(context).then(async (runtime) => {
		const status = runtime.status;
		console.log(`SLATE Runtime: ${status.backend} (healthy: ${status.healthy})`);

		// Auto-start SLATE systems if not running
		await autoStartSlateSystems(context, runtime);

		// Log runtime changes
		runtime.onStatusChange((newStatus) => {
			console.log(`SLATE Runtime changed: ${newStatus.backend} (healthy: ${newStatus.healthy})`);
			if (newStatus.backend === 'kubernetes') {
				vscode.window.setStatusBarMessage('$(cloud) SLATE: Connected to K8s cluster', 5000);
			} else if (newStatus.backend === 'docker') {
				vscode.window.setStatusBarMessage('$(package) SLATE: Connected to Docker runtime', 5000);
			}
		});
	});

	// ─── VS Code Deep Integrations ─────────────────────────────────────────
	// These hook SLATE into native VS Code systems for seamless DX

	// Diagnostics: Security scan findings → Problems panel
	const diagnostics = new SlateDiagnosticsProvider();
	diagnostics.activate(context);

	// Test Explorer: SLATE tests → VS Code Test Explorer sidebar
	const testController = new SlateTestController();
	testController.activate(context);

	// Task Provider: Dynamic SLATE tasks → Terminal > Run Task
	const taskProvider = new SlateTaskProvider();
	taskProvider.activate(context);

	// CodeLens: Inline actions on Python/YAML files
	const codeLens = new SlateCodeLensProvider();
	codeLens.activate(context);

	// GitHub Integration: CI monitor, PR manager, issue tracker, git ops
	registerGitHubTools(context);

	// ─── SLATE Theme & Background Initialization ───────────────────────────
	// Embodies the SLATE ethos: systems evolve with progress
	initializeSlateEnvironment(context);

	// Create SLATE status bar indicator
	slateStatusBarItem = vscode.window.createStatusBarItem(
		vscode.StatusBarAlignment.Left,
		100
	);
	slateStatusBarItem.text = '$(circuit-board) SLATE';
	slateStatusBarItem.tooltip = 'S.L.A.T.E. — Synchronized Living Architecture for Transformation and Evolution\n\nClick to show system status';
	slateStatusBarItem.command = 'slate.showStatus';
	slateStatusBarItem.backgroundColor = undefined;
	slateStatusBarItem.show();
	context.subscriptions.push(slateStatusBarItem);

	// Register service monitor for auto-restart — now K8s/Docker runtime aware
	const serviceMonitor = registerServiceMonitor(context);
	slateRuntimeAdapter = serviceMonitor.runtimeAdapter;

	// Register the unified dashboard (combines guided setup, control board, and dashboard)
	// Dashboard URL is now dynamic — provided by the runtime adapter
	const unifiedDashboardProvider = new SlateUnifiedDashboardViewProvider(context.extensionUri, context);
	context.subscriptions.push(
		vscode.window.registerWebviewViewProvider(
			SlateUnifiedDashboardViewProvider.viewType,
			unifiedDashboardProvider,
			{ webviewOptions: { retainContextWhenHidden: true } }
		)
	);

	// Refresh command
	context.subscriptions.push(
		vscode.commands.registerCommand('slate.refreshDashboard', () => {
			unifiedDashboardProvider.refresh();
		})
	);

	// Skip onboarding command (escape hatch for stuck state)
	context.subscriptions.push(
		vscode.commands.registerCommand('slate.skipOnboarding', async () => {
			await context.globalState.update('slateOnboardingComplete', true);
			await context.globalState.update('slateLastVersion', '4.0.0');
			unifiedDashboardProvider.refresh();
			vscode.window.showInformationMessage('SLATE onboarding skipped. Dashboard view refreshed.');
		})
	);

	// Reset onboarding command
	context.subscriptions.push(
		vscode.commands.registerCommand('slate.resetOnboarding', async () => {
			await context.globalState.update('slateOnboardingComplete', false);
			await context.globalState.update('slateLastVersion', '0.0.0');
			unifiedDashboardProvider.refresh();
			vscode.window.showInformationMessage('SLATE onboarding reset. Refresh the SLATE panel to restart.');
		})
	);

	// Register the status command
	context.subscriptions.push(
		vscode.commands.registerCommand('slate.showStatus', async () => {
			const terminal = vscode.window.createTerminal('SLATE Status');
			terminal.show();
			terminal.sendText(`"${getSlateConfig().pythonPath}" slate/slate_status.py --quick`);
		})
	);

	context.subscriptions.push(
		vscode.commands.registerCommand('slate.openDashboard', async () => {
			const dashboardUrl = getDashboardUrl();
			const panel = vscode.window.createWebviewPanel(
				'slateDashboard',
				'SLATE Dashboard',
				vscode.ViewColumn.One,
				{
					enableScripts: true,
					retainContextWhenHidden: true,
				}
			);

			panel.webview.onDidReceiveMessage((message) => {
				if (message?.type === 'openExternal') {
					void vscode.env.openExternal(vscode.Uri.parse(dashboardUrl));
				}
			});

			panel.webview.html = getDashboardHtml(panel.webview, dashboardUrl);
		})
	);
}

export function deactivate() { }

// ─── Auto-Start SLATE Systems ──────────────────────────────────────────────
// Modified: 2026-02-10T08:00:00Z | Author: COPILOT | Change: Auto-start Ollama + SLATE services on VS Code open
// Modified: 2026-02-11T06:00:00Z | Author: COPILOT | Change: Enforce container-first in auto-start — no local Python fallback, skip host Ollama when K8s backend detected

/** Check if Ollama is running by hitting its health endpoint */
async function checkOllamaRunning(): Promise<boolean> {
	return new Promise<boolean>((resolve) => {
		const req = http.get(
			{ hostname: '127.0.0.1', port: 11434, path: '/api/version', timeout: 3000 },
			(res) => {
				let body = '';
				res.on('data', (chunk: Buffer) => { body += chunk.toString(); });
				res.on('end', () => resolve(res.statusCode === 200));
			}
		);
		req.on('error', () => resolve(false));
		req.on('timeout', () => { req.destroy(); resolve(false); });
	});
}

/** Check if a local service is reachable */
async function checkServiceRunning(port: number, path: string = '/'): Promise<boolean> {
	return new Promise<boolean>((resolve) => {
		const req = http.get(
			{ hostname: '127.0.0.1', port, path, timeout: 3000 },
			(res) => { resolve(res.statusCode !== undefined && res.statusCode < 500); }
		);
		req.on('error', () => resolve(false));
		req.on('timeout', () => { req.destroy(); resolve(false); });
	});
}

/** Auto-start SLATE systems when VS Code opens */
async function autoStartSlateSystems(
	context: vscode.ExtensionContext,
	runtime: Awaited<ReturnType<typeof activateSlateRuntime>>
): Promise<void> {
	const autoStartEnabled = vscode.workspace.getConfiguration('slate').get<boolean>('autoStart', true);
	if (!autoStartEnabled) {
		console.log('[SLATE] Auto-start disabled by setting');
		return;
	}

	const status = runtime.status;
	const startedServices: string[] = [];
	const failedServices: string[] = [];

	vscode.window.setStatusBarMessage('$(sync~spin) SLATE: Checking systems...', 10000);
	console.log('[SLATE] Auto-start: checking SLATE systems...');

	// 1. Check and start Ollama (host-level only — skip if K8s detected, Ollama runs as pod)
	if (status.backend === 'kubernetes') {
		console.log('[SLATE] Auto-start: K8s backend detected — skipping host Ollama (runs as K8s pod)');
	} else {
		const ollamaOk = await checkOllamaRunning();
		if (!ollamaOk) {
			console.log('[SLATE] Auto-start: Ollama not running, attempting to start...');
			try {
				const ollamaProc = spawn('ollama', ['serve'], {
					detached: true,
					stdio: 'ignore',
					windowsHide: true,
				});
				ollamaProc.unref();
				// Wait a moment for Ollama to start
				await new Promise(r => setTimeout(r, 2000));
				const ollamaCheck = await checkOllamaRunning();
				if (ollamaCheck) {
					startedServices.push('Ollama');
					console.log('[SLATE] Auto-start: Ollama started successfully');
				} else {
					failedServices.push('Ollama');
					console.warn('[SLATE] Auto-start: Ollama failed to start');
				}
			} catch (err) {
				failedServices.push('Ollama');
				console.warn('[SLATE] Auto-start: Ollama spawn error:', err);
			}
		} else {
			console.log('[SLATE] Auto-start: Ollama already running');
		}
	}

	// 2. If runtime backend is not healthy, try to start services
	if (!status.healthy || status.backend === 'none') {
		console.log('[SLATE] Auto-start: Runtime not healthy, attempting to start services...');

		// Check if Dashboard is running
		const dashboardOk = await checkServiceRunning(8080, '/docs');
		if (!dashboardOk) {
			// Try to start services via the SLATE Auto-Start task (which uses container runtime)
			try {
				await vscode.commands.executeCommand('workbench.action.tasks.runTask', 'SLATE: Auto-Start');
				startedServices.push('SLATE Services');
				console.log('[SLATE] Auto-start: Dispatched SLATE: Auto-Start task');
			} catch (err) {
				// Container-first: prompt user to deploy via K8s or Docker instead of local Python fallback
				console.warn('[SLATE] Auto-start: Auto-Start task failed, prompting container deploy');
				void vscode.window.showWarningMessage(
					'SLATE: Could not auto-start services. Deploy via K8s or Docker to enable the full runtime.',
					'K8s Deploy', 'Docker Up (Dev)'
				).then(action => {
					if (action === 'K8s Deploy') {
						void vscode.commands.executeCommand('workbench.action.tasks.runTask', 'SLATE: K8s Deploy');
					} else if (action === 'Docker Up (Dev)') {
						void vscode.commands.executeCommand('workbench.action.tasks.runTask', 'SLATE: Docker Up (Dev)');
					}
				});
				failedServices.push('SLATE Services');
			}
		} else {
			console.log('[SLATE] Auto-start: Dashboard already running on :8080');
		}

		// Re-detect backend after starting services
		await new Promise(r => setTimeout(r, 3000));
		await runtime.detectBackend();
	}

	// 3. Report results
	if (startedServices.length > 0) {
		vscode.window.setStatusBarMessage(
			`$(check) SLATE: Started ${startedServices.join(', ')}`,
			8000
		);
		vscode.window.showInformationMessage(
			`SLATE auto-started: ${startedServices.join(', ')}. ` +
			`Runtime: ${runtime.status.backend}`
		);
	} else if (failedServices.length > 0) {
		vscode.window.setStatusBarMessage(
			`$(warning) SLATE: Failed to start ${failedServices.join(', ')}`,
			8000
		);
	} else {
		vscode.window.setStatusBarMessage(
			`$(check) SLATE: All systems online (${runtime.status.backend})`,
			5000
		);
	}

	console.log(`[SLATE] Auto-start complete: started=[${startedServices}], failed=[${failedServices}], backend=${runtime.status.backend}`);
}

// ─── SLATE Environment Initialization ──────────────────────────────────────
// This implements the SLATE ethos: the system evolves with progress

/**
 * Initialize the SLATE visual environment:
 * 1. Apply SLATE Dark theme (on first install or if requested)
 * 2. Generate and apply the evolving schematic background
 * 3. Set up watchers for automatic background evolution
 */
async function initializeSlateEnvironment(context: vscode.ExtensionContext): Promise<void> {
	const isFirstActivation = !context.globalState.get<boolean>('slateInitialized');

	// Register background commands
	registerBackgroundCommands(context);

	// On first activation, offer to apply SLATE theme
	if (isFirstActivation) {
		await context.globalState.update('slateInitialized', true);

		const applyTheme = await vscode.window.showInformationMessage(
			'Welcome to SLATE! Apply the SLATE Dark theme and schematic background?',
			'Yes, Transform VS Code',
			'Just Theme',
			'Skip'
		);

		if (applyTheme === 'Yes, Transform VS Code') {
			// Apply theme
			await vscode.workspace.getConfiguration('workbench').update(
				'colorTheme',
				SLATE_THEME_ID,
				vscode.ConfigurationTarget.Global
			);

			// Enable and generate background
			await vscode.workspace.getConfiguration('slate').update(
				'background.enabled',
				true,
				vscode.ConfigurationTarget.Global
			);
			await applySchematicBackground(context);

			// Set up watchers for evolution
			watchForStateChanges(context);

			vscode.window.showInformationMessage(
				'SLATE environment activated! Your VS Code will evolve as your system progresses.'
			);
		} else if (applyTheme === 'Just Theme') {
			await vscode.workspace.getConfiguration('workbench').update(
				'colorTheme',
				SLATE_THEME_ID,
				vscode.ConfigurationTarget.Global
			);
		}
	} else {
		// On subsequent activations, refresh background if enabled
		const config = vscode.workspace.getConfiguration('slate');
		if (config.get<boolean>('background.enabled', false)) {
			// Generate background silently
			await applySchematicBackground(context);
			watchForStateChanges(context);
		}
	}

	// Register apply theme command
	context.subscriptions.push(
		vscode.commands.registerCommand('slate.applyTheme', async () => {
			await vscode.workspace.getConfiguration('workbench').update(
				'colorTheme',
				SLATE_THEME_ID,
				vscode.ConfigurationTarget.Global
			);

			const enableBg = await vscode.window.showInformationMessage(
				'SLATE Dark theme applied! Enable evolving schematic background?',
				'Yes',
				'No'
			);

			if (enableBg === 'Yes') {
				await vscode.workspace.getConfiguration('slate').update(
					'background.enabled',
					true,
					vscode.ConfigurationTarget.Global
				);
				await applySchematicBackground(context);
				watchForStateChanges(context);
			}
		})
	);
}

/** SLATE workspace configuration */
export interface SlateConfig {
	pythonPath: string;
	workspacePath: string;
}

/** Get SLATE configuration from workspace */
export function getSlateConfig(): SlateConfig {
	const workspaceFolders = vscode.workspace.workspaceFolders;
	const workspacePath = workspaceFolders?.[0]?.uri.fsPath ?? process.cwd();

	return {
		pythonPath: `${workspacePath}\\.venv\\Scripts\\python.exe`,
		workspacePath,
	};
}

function getDashboardHtml(webview: vscode.Webview, dashboardUrl: string): string {
	const nonce = getNonce();
	const runtimeLabel = slateRuntimeAdapter?.state.backend ?? 'unknown';
	const csp = [
		"default-src 'none'",
		`frame-src ${dashboardUrl}`,
		`img-src ${dashboardUrl} data:`,
		"style-src 'unsafe-inline'",
		`script-src 'nonce-${nonce}'`,
	].join('; ');

	return `<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8" />
	<meta name="viewport" content="width=device-width, initial-scale=1.0" />
	<meta http-equiv="Content-Security-Policy" content="${csp}" />
	<title>SLATE Dashboard</title>
	<style>
		html, body {
			height: 100%;
			width: 100%;
			margin: 0;
			padding: 0;
			background: #0a0a0a;
			color: #F5F0EB;
			font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
		}
		.toolbar {
			display: flex;
			align-items: center;
			justify-content: space-between;
			padding: 10px 14px;
			border-bottom: 1px solid rgba(255,255,255,0.08);
			background: #050505;
		}
		.title {
			font-size: 14px;
			letter-spacing: 0.08em;
			text-transform: uppercase;
			color: #B87333;
			font-weight: 600;
		}
		.runtime-badge {
			font-size: 10px;
			letter-spacing: 0.06em;
			text-transform: uppercase;
			color: #7EC8E3;
			background: rgba(126, 200, 227, 0.1);
			border: 1px solid rgba(126, 200, 227, 0.2);
			border-radius: 4px;
			padding: 2px 8px;
			margin-left: 8px;
		}
		.actions {
			display: flex;
			gap: 8px;
		}
		button {
			background: #111111;
			color: #F5F0EB;
			border: 1px solid rgba(255,255,255,0.12);
			border-radius: 8px;
			padding: 6px 14px;
			cursor: pointer;
			font-size: 12px;
			font-family: inherit;
			transition: all 0.2s;
		}
		button:hover {
			background: #1a1a1a;
			border-color: #B87333;
			color: #C9956B;
		}
		.frame {
			height: calc(100% - 44px);
			width: 100%;
			border: none;
			background: #0a0a0a;
		}
	</style>
</head>
<body>
	<div class="toolbar">
		<div style="display:flex;align-items:center">
			<div class="title">SLATE Dashboard</div>
			<span class="runtime-badge">${runtimeLabel}</span>
		</div>
		<div class="actions">
			<button id="openExternal">Open in Browser</button>
		</div>
	</div>
	<iframe class="frame" src="${dashboardUrl}" title="SLATE Dashboard"></iframe>
	<script nonce="${nonce}">
		const vscode = acquireVsCodeApi();
		document.getElementById('openExternal').addEventListener('click', () => {
			vscode.postMessage({ type: 'openExternal' });
		});
	</script>
</body>
</html>`;
}

function getNonce(): string {
	const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
	let text = '';
	for (let i = 0; i < 32; i += 1) {
		text += possible.charAt(Math.floor(Math.random() * possible.length));
	}
	return text;
}
