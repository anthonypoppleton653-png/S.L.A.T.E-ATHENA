// Modified: 2026-02-08T23:00:00Z | Author: COPILOT | Change: Rebuild on K8s/Docker runtime — remove all local execution code
// All SLATE command execution routes through the K8s/Docker runtime backend.
// Local Python spawning removed per SLATE container-first architecture.
// DEPRECATED: 2026-02-08 | Reason: Local child_process.spawn execution removed entirely
import * as vscode from 'vscode';
import { getSlateRuntime } from './slateRuntimeBackend';

/**
 * Execute a SLATE Python command via the K8s/Docker runtime backend.
 * Routes to: K8s copilot-bridge (primary) → Docker exec (secondary).
 * No local fallback — container runtime is REQUIRED.
 */
export function execSlateCommand(command: string, token: vscode.CancellationToken): Promise<string> {
	return getSlateRuntime().exec(command, token, false);
}

/**
 * Execute a long-running SLATE command via the K8s/Docker runtime backend.
 * Extended timeout (5 min) for installs, builds, benchmarks, model training.
 */
export function execSlateCommandLong(command: string, token: vscode.CancellationToken): Promise<string> {
	return getSlateRuntime().exec(command, token, true);
}

/**
 * Execute a SLATE command with a specific timeout override.
 * Routes through the K8s/Docker runtime backend.
 */
export function execSlateCommandWithTimeout(command: string, token: vscode.CancellationToken, timeoutMs: number): Promise<string> {
	return getSlateRuntime().exec(command, token, timeoutMs > 90_000);
}
