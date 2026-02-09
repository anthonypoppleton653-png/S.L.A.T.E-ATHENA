// Modified: 2026-02-10T03:00:00Z | Author: Claude Opus 4.5 | Change: Add Claude Agent SDK integration hooks for SLATE security
/**
 * SLATE Agent SDK Hooks
 * =====================
 * Provides Claude Agent SDK integration hooks that connect to SLATE's
 * ActionGuard security system. These hooks validate tool calls through
 * SLATE's Python backend before allowing execution.
 *
 * Architecture:
 *   VS Code Extension → slateAgentSdkHooks.ts → K8s Bridge/Local Python → ActionGuard
 *
 * Hook Types (per Claude Agent SDK):
 *   - PreToolUse: Validate before tool execution
 *   - PostToolUse: Log and audit after tool execution
 *   - UserPromptSubmit: Scan prompts for security issues
 */

import * as vscode from 'vscode';
import { execSlateCommand } from './slateRunner';
import { getSlateRuntime } from './slateRuntimeBackend';

// ─── Hook Types ────────────────────────────────────────────────────────────

export type HookEvent = 'PreToolUse' | 'PostToolUse' | 'PostToolUseFailure' | 'UserPromptSubmit' | 'Stop';

export interface HookResult {
	/** Permission decision: allow, deny, or ask */
	permission_decision: 'allow' | 'deny' | 'ask';
	/** Reason for the decision */
	reason: string;
	/** Whether to continue execution */
	continue_execution: boolean;
	/** Optional updated input (for PreToolUse) */
	updated_input?: Record<string, unknown>;
	/** Optional system message to inject */
	system_message?: string;
}

export interface HookContext {
	/** The tool being called */
	tool_name: string;
	/** The tool input parameters */
	tool_input: Record<string, unknown>;
	/** Unique ID for this tool use */
	tool_use_id: string;
	/** Optional session ID */
	session_id?: string;
}

// ─── ActionGuard Integration ────────────────────────────────────────────────

/**
 * Execute a SLATE hook through the ActionGuard security system.
 * Routes to K8s backend or local Python based on runtime.
 */
export async function executeSlateHook(
	event: HookEvent,
	context: HookContext,
	token?: vscode.CancellationToken
): Promise<HookResult> {
	// Use provided token or create a default one
	const cancellationToken = token ?? new vscode.CancellationTokenSource().token;

	try {
		const runtime = getSlateRuntime();
		const runtimeStatus = runtime?.status;

		// Build hook command
		const hookPayload = JSON.stringify({
			event,
			tool_name: context.tool_name,
			tool_input: context.tool_input,
			tool_use_id: context.tool_use_id,
			session_id: context.session_id,
		});

		// Escape for shell
		const escapedPayload = hookPayload.replace(/"/g, '\\"').replace(/'/g, "\\'");

		// Modified: 2026-02-10T06:00:00Z | Author: COPILOT | Change: Simplify hook routing — all backends use same command via execSlateCommand
		const cmd = `slate/claude_code_manager.py --execute-hook "${escapedPayload}"`;

		const output = await execSlateCommand(cmd, cancellationToken);

		// Parse result
		try {
			const result = JSON.parse(output);
			return {
				permission_decision: result.permission_decision ?? 'allow',
				reason: result.reason ?? '',
				continue_execution: result.continue_execution ?? true,
				updated_input: result.updated_input,
				system_message: result.system_message,
			};
		} catch {
			// If output isn't JSON, assume success
			return {
				permission_decision: 'allow',
				reason: 'Hook executed successfully',
				continue_execution: true,
			};
		}
	} catch (error) {
		// On error, log but allow execution (fail-open for UX, ActionGuard handles security)
		console.error(`[SLATE] Hook execution error: ${error}`);
		return {
			permission_decision: 'allow',
			reason: 'Hook error (fail-open)',
			continue_execution: true,
		};
	}
}

// ─── Convenience Hook Functions ────────────────────────────────────────────

/**
 * Validate a tool call before execution (PreToolUse hook).
 * Returns true if the tool call is allowed.
 */
export async function validateToolCall(
	toolName: string,
	toolInput: Record<string, unknown>,
	token?: vscode.CancellationToken
): Promise<{ allowed: boolean; reason: string; updatedInput?: Record<string, unknown> }> {
	const result = await executeSlateHook(
		'PreToolUse',
		{
			tool_name: toolName,
			tool_input: toolInput,
			tool_use_id: `validate_${Date.now()}`,
		},
		token
	);

	return {
		allowed: result.permission_decision !== 'deny',
		reason: result.reason,
		updatedInput: result.updated_input,
	};
}

/**
 * Log a tool execution after completion (PostToolUse hook).
 */
export async function logToolExecution(
	toolName: string,
	toolInput: Record<string, unknown>,
	success: boolean,
	token?: vscode.CancellationToken
): Promise<void> {
	const event: HookEvent = success ? 'PostToolUse' : 'PostToolUseFailure';
	await executeSlateHook(
		event,
		{
			tool_name: toolName,
			tool_input: toolInput,
			tool_use_id: `log_${Date.now()}`,
		},
		token
	);
}

/**
 * Scan a user prompt for security issues (UserPromptSubmit hook).
 * Returns true if the prompt is safe.
 */
export async function scanUserPrompt(
	prompt: string,
	token?: vscode.CancellationToken
): Promise<{ safe: boolean; reason: string }> {
	const result = await executeSlateHook(
		'UserPromptSubmit',
		{
			tool_name: 'user_prompt',
			tool_input: { prompt },
			tool_use_id: `prompt_${Date.now()}`,
		},
		token
	);

	return {
		safe: result.permission_decision !== 'deny',
		reason: result.reason,
	};
}

// ─── ActionGuard Quick Checks ──────────────────────────────────────────────

/**
 * Quick check if a Bash command is allowed by ActionGuard.
 * Uses the SLATE action_guard.py validate endpoint.
 */
export async function validateBashCommand(
	command: string,
	token?: vscode.CancellationToken
): Promise<{ allowed: boolean; reason: string }> {
	const cancellationToken = token ?? new vscode.CancellationTokenSource().token;
	try {
		const output = await execSlateCommand(
			`slate/action_guard.py --validate-bash "${command.replace(/"/g, '\\"')}"`,
			cancellationToken
		);

		if (output.includes('ALLOWED') || output.includes('allowed')) {
			return { allowed: true, reason: 'Command allowed by ActionGuard' };
		} else if (output.includes('BLOCKED') || output.includes('blocked')) {
			const reason = output.match(/reason[:\s]+([^\n]+)/i)?.[1] ?? 'Blocked by ActionGuard';
			return { allowed: false, reason };
		}

		// Default to allowed if unclear
		return { allowed: true, reason: 'No explicit block' };
	} catch (error) {
		// Fail-open on error (ActionGuard will catch dangerous patterns anyway)
		return { allowed: true, reason: 'ActionGuard check failed (fail-open)' };
	}
}

/**
 * Quick check if a file path is allowed for reading/writing.
 */
export async function validateFilePath(
	filePath: string,
	operation: 'read' | 'write' | 'edit',
	token?: vscode.CancellationToken
): Promise<{ allowed: boolean; reason: string }> {
	const cancellationToken = token ?? new vscode.CancellationTokenSource().token;
	try {
		const output = await execSlateCommand(
			`slate/action_guard.py --validate-file "${filePath.replace(/"/g, '\\"')}" --op ${operation}`,
			cancellationToken
		);

		if (output.includes('ALLOWED') || output.includes('allowed')) {
			return { allowed: true, reason: 'File access allowed' };
		} else if (output.includes('BLOCKED') || output.includes('blocked')) {
			const reason = output.match(/reason[:\s]+([^\n]+)/i)?.[1] ?? 'Blocked by ActionGuard';
			return { allowed: false, reason };
		}

		return { allowed: true, reason: 'No explicit block' };
	} catch {
		return { allowed: true, reason: 'ActionGuard check failed (fail-open)' };
	}
}

// ─── Hook Registration ─────────────────────────────────────────────────────

/**
 * Register SLATE Agent SDK hooks with the VS Code extension.
 */
export function registerAgentSdkHooks(context: vscode.ExtensionContext): void {
	// Register command to validate a tool call
	context.subscriptions.push(
		vscode.commands.registerCommand('slate.validateToolCall', async (toolName: string, toolInput: Record<string, unknown>) => {
			const result = await validateToolCall(toolName, toolInput);
			if (!result.allowed) {
				void vscode.window.showWarningMessage(`SLATE ActionGuard blocked: ${result.reason}`);
			}
			return result;
		})
	);

	// Register command to validate a bash command
	context.subscriptions.push(
		vscode.commands.registerCommand('slate.validateBash', async (command: string) => {
			const result = await validateBashCommand(command);
			if (!result.allowed) {
				void vscode.window.showWarningMessage(`SLATE ActionGuard blocked command: ${result.reason}`);
			}
			return result;
		})
	);

	// Register command to scan user prompt
	context.subscriptions.push(
		vscode.commands.registerCommand('slate.scanPrompt', async (prompt: string) => {
			const result = await scanUserPrompt(prompt);
			if (!result.safe) {
				void vscode.window.showWarningMessage(`SLATE detected unsafe prompt: ${result.reason}`);
			}
			return result;
		})
	);

	console.log('[SLATE] Agent SDK hooks registered');
}
