// Modified: 2026-02-12T04:00:00Z | Author: COPILOT | Change: Create ATHENA bottom panel webview for live dashboard iframe
/**
 * ATHENA Bottom Panel — Live Dashboard
 * =====================================
 * Embeds the FastAPI dashboard (http://127.0.0.1:8080) in the VS Code bottom panel.
 * This provides real-time system topology, GPU status, Ollama models, and task queue
 * visualization directly within VS Code.
 *
 * Design System: ATHENA Greek — Olympus Gold, Aegean Blue, Midnight Deep
 * Port: 8080 (slate_athena_server.py)
 */

import * as vscode from 'vscode';

const DASHBOARD_URL = 'http://127.0.0.1:8080';

export class AthenaBottomPanelProvider implements vscode.WebviewViewProvider {
	public static readonly viewType = 'athena.dashboardPanel';

	private _view?: vscode.WebviewView;

	constructor(
		private readonly _extensionUri: vscode.Uri,
		private readonly _context: vscode.ExtensionContext,
	) {}

	public resolveWebviewView(
		webviewView: vscode.WebviewView,
		_context: vscode.WebviewViewResolveContext,
		_token: vscode.CancellationToken,
	): void {
		this._view = webviewView;

		webviewView.webview.options = {
			enableScripts: true,
			localResourceRoots: [this._extensionUri],
		};

		webviewView.webview.html = this._getHtml(webviewView.webview);

		// Handle messages from the webview
		webviewView.webview.onDidReceiveMessage(async (message) => {
			switch (message.type) {
				case 'openExternal':
					await vscode.env.openExternal(vscode.Uri.parse(DASHBOARD_URL));
					break;
				case 'refresh':
					this.refresh();
					break;
				case 'showMessage':
					vscode.window.showInformationMessage(message.text);
					break;
			}
		});
	}

	public refresh(): void {
		if (this._view) {
			this._view.webview.html = this._getHtml(this._view.webview);
		}
	}

	private _getHtml(webview: vscode.Webview): string {
		const nonce = this._getNonce();

		return `<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<meta http-equiv="Content-Security-Policy" content="
		default-src 'none';
		frame-src ${DASHBOARD_URL};
		style-src 'unsafe-inline';
		script-src 'nonce-${nonce}';
	">
	<title>ATHENA Dashboard</title>
	<style>
		/* Athena Gold/Blue Design Tokens — Modified: 2026-02-11T10:00:00Z | Author: COPILOT | Restore Athena theme */
		:root {
			--athena-root: #080B10;
			--athena-surface: #0E1420;
			--athena-gold: #C9A227;
			--athena-gold-bright: #E8C547;
			--athena-blue: #3498DB;
			--athena-text: #F8F9FA;
			--athena-text-secondary: #9CA3AF;
			--athena-border: rgba(201, 162, 39, 0.15);
			--athena-success: #27AE60;
			--athena-error: #DC3545;
		}

		* {
			margin: 0;
			padding: 0;
			box-sizing: border-box;
		}

		html, body {
			height: 100%;
			width: 100%;
			overflow: hidden;
			background: var(--athena-root);
			font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
		}

		.panel-container {
			display: flex;
			flex-direction: column;
			height: 100%;
			width: 100%;
		}

		.panel-header {
			display: flex;
			align-items: center;
			justify-content: space-between;
			padding: 8px 12px;
			background: var(--athena-surface);
			border-bottom: 1px solid var(--athena-border);
			flex-shrink: 0;
		}

		.header-left {
			display: flex;
			align-items: center;
			gap: 8px;
		}

		.athena-logo {
			width: 20px;
			height: 20px;
			fill: var(--athena-gold);
		}

		.panel-title {
			font-size: 12px;
			font-weight: 600;
			color: var(--athena-gold);
			text-transform: uppercase;
			letter-spacing: 0.5px;
		}

		.header-actions {
			display: flex;
			gap: 6px;
		}

		.action-btn {
			background: transparent;
			border: 1px solid var(--athena-border);
			border-radius: 4px;
			padding: 4px 8px;
			color: var(--athena-text);
			font-size: 11px;
			cursor: pointer;
			transition: all 0.2s ease;
		}

		.action-btn:hover {
			background: rgba(201, 162, 39, 0.1);
			border-color: var(--athena-gold);
			color: var(--athena-gold);
		}

		.action-btn.primary {
			background: linear-gradient(135deg, var(--athena-gold), #9B7D1E);
			border-color: var(--athena-gold);
			color: var(--athena-root);
			font-weight: 500;
		}

		.action-btn.primary:hover {
			background: linear-gradient(135deg, var(--athena-gold-bright), var(--athena-gold));
			transform: translateY(-1px);
		}

		.iframe-container {
			flex: 1;
			width: 100%;
			position: relative;
			background: var(--athena-root);
		}

		.dashboard-frame {
			width: 100%;
			height: 100%;
			border: none;
			background: var(--athena-root);
		}

		.loading-overlay {
			position: absolute;
			top: 0;
			left: 0;
			right: 0;
			bottom: 0;
			display: flex;
			flex-direction: column;
			align-items: center;
			justify-content: center;
			background: var(--athena-root);
			z-index: 10;
			transition: opacity 0.3s ease;
		}

		.loading-overlay.hidden {
			opacity: 0;
			pointer-events: none;
		}

		.loading-spinner {
			width: 40px;
			height: 40px;
			border: 3px solid var(--athena-border);
			border-top-color: var(--athena-gold);
			border-radius: 50%;
			animation: spin 1s linear infinite;
		}

		.loading-text {
			margin-top: 12px;
			color: var(--athena-text);
			font-size: 12px;
			opacity: 0.7;
		}

		@keyframes spin {
			to { transform: rotate(360deg); }
		}

		.error-state {
			display: none;
			flex-direction: column;
			align-items: center;
			justify-content: center;
			height: 100%;
			padding: 24px;
			text-align: center;
		}

		.error-state.visible {
			display: flex;
		}

		.error-icon {
			font-size: 48px;
			margin-bottom: 16px;
		}

		.error-title {
			color: var(--athena-gold);
			font-size: 16px;
			font-weight: 600;
			margin-bottom: 8px;
		}

		.error-message {
			color: var(--athena-text);
			font-size: 12px;
			opacity: 0.7;
			margin-bottom: 16px;
		}

		/* Status indicator */
		.status-dot {
			width: 8px;
			height: 8px;
			border-radius: 50%;
			background: #666;
			transition: background 0.3s ease;
		}

		.status-dot.connected {
			background: var(--athena-success);
			box-shadow: 0 0 8px rgba(39, 174, 96, 0.5);
		}

		.status-dot.error {
			background: var(--athena-error);
			box-shadow: 0 0 8px rgba(220, 53, 69, 0.5);
		}
	</style>
</head>
<body>
	<div class="panel-container">
		<div class="panel-header">
			<div class="header-left">
				<svg class="athena-logo" viewBox="0 0 24 24">
					<path d="M12 2C8.5 2 6 4.5 6 8c0 2 1 4 2 5l-1 8h10l-1-8c1-1 2-3 2-5 0-3.5-2.5-6-6-6z"/>
					<circle cx="9" cy="8" r="1.5" fill="#080B10"/>
					<circle cx="15" cy="8" r="1.5" fill="#080B10"/>
					<path d="M8 12c0 0 2 2 4 2s4-2 4-2" stroke="#080B10" stroke-width="1.5" fill="none"/>
				</svg>
				<span class="panel-title">ATHENA Dashboard</span>
				<div class="status-dot" id="statusDot"></div>
			</div>
			<div class="header-actions">
				<button class="action-btn" id="refreshBtn" title="Refresh Dashboard">↻ Refresh</button>
				<button class="action-btn primary" id="popoutBtn" title="Open in Browser">⬀ Pop Out</button>
			</div>
		</div>

		<div class="iframe-container">
			<div class="loading-overlay" id="loadingOverlay">
				<div class="loading-spinner"></div>
				<div class="loading-text">Connecting to ATHENA Dashboard...</div>
			</div>

			<div class="error-state" id="errorState">
				<div class="error-icon">🦉</div>
				<div class="error-title">Dashboard Offline</div>
				<div class="error-message">The ATHENA dashboard server is not running on port 8080.</div>
				<button class="action-btn primary" id="retryBtn">Retry Connection</button>
			</div>

			<iframe
				id="dashboardFrame"
				class="dashboard-frame"
				src="${DASHBOARD_URL}"
				title="ATHENA Dashboard"
				sandbox="allow-scripts allow-same-origin allow-forms"
			></iframe>
		</div>
	</div>

	<script nonce="${nonce}">
		const vscode = acquireVsCodeApi();
		const frame = document.getElementById('dashboardFrame');
		const loadingOverlay = document.getElementById('loadingOverlay');
		const errorState = document.getElementById('errorState');
		const statusDot = document.getElementById('statusDot');
		const refreshBtn = document.getElementById('refreshBtn');
		const popoutBtn = document.getElementById('popoutBtn');
		const retryBtn = document.getElementById('retryBtn');

		let checkTimeout;

		function showLoading() {
			loadingOverlay.classList.remove('hidden');
			errorState.classList.remove('visible');
			frame.style.display = 'block';
		}

		function showError() {
			loadingOverlay.classList.add('hidden');
			errorState.classList.add('visible');
			frame.style.display = 'none';
			statusDot.classList.remove('connected');
			statusDot.classList.add('error');
		}

		function showDashboard() {
			loadingOverlay.classList.add('hidden');
			errorState.classList.remove('visible');
			frame.style.display = 'block';
			statusDot.classList.remove('error');
			statusDot.classList.add('connected');
		}

		function checkConnection() {
			clearTimeout(checkTimeout);
			showLoading();

			// Set a timeout for connection check
			checkTimeout = setTimeout(() => {
				showError();
			}, 5000);
		}

		// Handle iframe load events
		frame.addEventListener('load', () => {
			clearTimeout(checkTimeout);
			try {
				// If we can access the content, it's loaded
				showDashboard();
			} catch (e) {
				// Cross-origin, but iframe loaded successfully
				showDashboard();
			}
		});

		frame.addEventListener('error', () => {
			clearTimeout(checkTimeout);
			showError();
		});

		// Button handlers
		refreshBtn.addEventListener('click', () => {
			checkConnection();
			frame.src = '${DASHBOARD_URL}?' + Date.now();
		});

		popoutBtn.addEventListener('click', () => {
			vscode.postMessage({ type: 'openExternal' });
		});

		retryBtn.addEventListener('click', () => {
			checkConnection();
			frame.src = '${DASHBOARD_URL}?' + Date.now();
		});

		// Initial connection check
		checkConnection();
	</script>
</body>
</html>`;
	}

	private _getNonce(): string {
		let text = '';
		const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
		for (let i = 0; i < 32; i++) {
			text += possible.charAt(Math.floor(Math.random() * possible.length));
		}
		return text;
	}
}
