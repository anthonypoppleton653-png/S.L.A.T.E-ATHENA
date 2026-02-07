// Modified: 2026-02-06T22:30:00Z | Author: COPILOT | Change: SLATE tool implementations with /install and /update
import * as vscode from 'vscode';
import { execSlateCommand, execSlateCommandLong } from './slateRunner';

// ─── Tool Implementations ──────────────────────────────────────────────

interface IStatusParams { quick?: boolean }
interface IRuntimeParams { /* no params */ }
interface IRunnerParams { action?: string; workflow?: string }
interface IHardwareParams { optimize?: boolean }
interface IOrchestratorParams { action?: string }
interface IWorkflowParams { action?: string }
interface IBenchmarkParams { /* no params */ }
interface IRunCommandParams { command: string }
interface IInstallParams { target?: string; beta?: boolean }
interface IUpdateParams { /* no params */ }
interface ICheckDepsParams { /* no params */ }

class SystemStatusTool implements vscode.LanguageModelTool<IStatusParams> {
	async invoke(options: vscode.LanguageModelToolInvocationOptions<IStatusParams>, token: vscode.CancellationToken) {
		const flag = options.input.quick ? '--quick' : '--json';
		const output = await execSlateCommand(`slate/slate_status.py ${flag}`, token);
		return new vscode.LanguageModelToolResult([new vscode.LanguageModelTextPart(output)]);
	}

	async prepareInvocation(_options: vscode.LanguageModelToolInvocationPrepareOptions<IStatusParams>, _token: vscode.CancellationToken) {
		return { invocationMessage: 'Checking SLATE system status...' };
	}
}

class RuntimeCheckTool implements vscode.LanguageModelTool<IRuntimeParams> {
	async invoke(_options: vscode.LanguageModelToolInvocationOptions<IRuntimeParams>, token: vscode.CancellationToken) {
		const output = await execSlateCommand('slate/slate_runtime.py --check-all', token);
		return new vscode.LanguageModelToolResult([new vscode.LanguageModelTextPart(output)]);
	}

	async prepareInvocation(_options: vscode.LanguageModelToolInvocationPrepareOptions<IRuntimeParams>, _token: vscode.CancellationToken) {
		return { invocationMessage: 'Checking SLATE runtime integrations...' };
	}
}

class RunnerStatusTool implements vscode.LanguageModelTool<IRunnerParams> {
	async invoke(options: vscode.LanguageModelToolInvocationOptions<IRunnerParams>, token: vscode.CancellationToken) {
		const action = options.input.action ?? 'status';
		let cmd: string;
		switch (action) {
			case 'detect':
				cmd = 'slate/slate_runner_manager.py --detect';
				break;
			case 'dispatch':
				cmd = `slate/slate_runner_manager.py --dispatch "${options.input.workflow ?? 'ci.yml'}"`;
				break;
			default:
				cmd = 'slate/slate_runner_manager.py --status';
		}
		const output = await execSlateCommand(cmd, token);
		return new vscode.LanguageModelToolResult([new vscode.LanguageModelTextPart(output)]);
	}

	async prepareInvocation(options: vscode.LanguageModelToolInvocationPrepareOptions<IRunnerParams>, _token: vscode.CancellationToken) {
		const action = options.input.action ?? 'status';
		const messages: Record<string, string> = {
			status: 'Checking runner status...',
			detect: 'Detecting runner configuration...',
			dispatch: `Dispatching workflow ${options.input.workflow ?? 'ci.yml'}...`,
		};
		return { invocationMessage: messages[action] ?? 'Checking runner...' };
	}
}

class HardwareInfoTool implements vscode.LanguageModelTool<IHardwareParams> {
	async invoke(options: vscode.LanguageModelToolInvocationOptions<IHardwareParams>, token: vscode.CancellationToken) {
		const flag = options.input.optimize ? '--optimize' : '';
		const output = await execSlateCommand(`slate/slate_hardware_optimizer.py ${flag}`.trim(), token);
		return new vscode.LanguageModelToolResult([new vscode.LanguageModelTextPart(output)]);
	}

	async prepareInvocation(options: vscode.LanguageModelToolInvocationPrepareOptions<IHardwareParams>, _token: vscode.CancellationToken) {
		return {
			invocationMessage: options.input.optimize ? 'Optimizing GPU settings...' : 'Detecting hardware...',
		};
	}
}

class OrchestratorTool implements vscode.LanguageModelTool<IOrchestratorParams> {
	async invoke(options: vscode.LanguageModelToolInvocationOptions<IOrchestratorParams>, token: vscode.CancellationToken) {
		const action = options.input.action ?? 'status';
		const output = await execSlateCommand(`slate/slate_orchestrator.py ${action}`, token);
		return new vscode.LanguageModelToolResult([new vscode.LanguageModelTextPart(output)]);
	}

	async prepareInvocation(options: vscode.LanguageModelToolInvocationPrepareOptions<IOrchestratorParams>, _token: vscode.CancellationToken) {
		const action = options.input.action ?? 'status';
		const messages: Record<string, string> = {
			status: 'Checking service status...',
			start: 'Starting SLATE services...',
			stop: 'Stopping SLATE services...',
		};
		return { invocationMessage: messages[action] ?? 'Managing orchestrator...' };
	}
}

class WorkflowTool implements vscode.LanguageModelTool<IWorkflowParams> {
	async invoke(options: vscode.LanguageModelToolInvocationOptions<IWorkflowParams>, token: vscode.CancellationToken) {
		const action = options.input.action ?? 'status';
		const flags: Record<string, string> = {
			status: '--status',
			cleanup: '--cleanup',
			enforce: '--enforce',
		};
		const output = await execSlateCommand(`slate/slate_workflow_manager.py ${flags[action] ?? '--status'}`, token);
		return new vscode.LanguageModelToolResult([new vscode.LanguageModelTextPart(output)]);
	}

	async prepareInvocation(options: vscode.LanguageModelToolInvocationPrepareOptions<IWorkflowParams>, _token: vscode.CancellationToken) {
		return { invocationMessage: `Workflow manager: ${options.input.action ?? 'status'}...` };
	}
}

class BenchmarkTool implements vscode.LanguageModelTool<IBenchmarkParams> {
	async invoke(_options: vscode.LanguageModelToolInvocationOptions<IBenchmarkParams>, token: vscode.CancellationToken) {
		const output = await execSlateCommand('slate/slate_benchmark.py', token);
		return new vscode.LanguageModelToolResult([new vscode.LanguageModelTextPart(output)]);
	}

	async prepareInvocation(_options: vscode.LanguageModelToolInvocationPrepareOptions<IBenchmarkParams>, _token: vscode.CancellationToken) {
		return { invocationMessage: 'Running SLATE benchmarks...' };
	}
}

class RunCommandTool implements vscode.LanguageModelTool<IRunCommandParams> {
	async invoke(options: vscode.LanguageModelToolInvocationOptions<IRunCommandParams>, token: vscode.CancellationToken) {
		const output = await execSlateCommand(options.input.command, token);
		return new vscode.LanguageModelToolResult([new vscode.LanguageModelTextPart(output)]);
	}

	async prepareInvocation(options: vscode.LanguageModelToolInvocationPrepareOptions<IRunCommandParams>, _token: vscode.CancellationToken) {
		return {
			invocationMessage: `Running: ${options.input.command}`,
			confirmationMessages: {
				title: 'Run SLATE Command',
				message: new vscode.MarkdownString(`Run this command?\n\n\`\`\`\n${options.input.command}\n\`\`\``),
			},
		};
	}
}

class InstallTool implements vscode.LanguageModelTool<IInstallParams> {
	async invoke(options: vscode.LanguageModelToolInvocationOptions<IInstallParams>, token: vscode.CancellationToken) {
		let cmd = 'slate/slate_installer.py --install';
		if (options.input.target) {
			cmd += ` --target "${options.input.target}"`;
		}
		if (options.input.beta) {
			cmd += ' --beta';
		}
		const output = await execSlateCommandLong(cmd, token);
		return new vscode.LanguageModelToolResult([new vscode.LanguageModelTextPart(output)]);
	}

	async prepareInvocation(options: vscode.LanguageModelToolInvocationPrepareOptions<IInstallParams>, _token: vscode.CancellationToken) {
		const target = options.input.target ? ` to ${options.input.target}` : '';
		const beta = options.input.beta ? ' (BETA fork)' : '';
		return {
			invocationMessage: `Installing SLATE ecosystem${target}${beta}...`,
			confirmationMessages: {
				title: 'Install SLATE Ecosystem',
				message: new vscode.MarkdownString(
					`This will set up the full SLATE ecosystem${target}${beta}:\n\n` +
					'- Git repository clone/verify\n' +
					'- Python virtual environment\n' +
					'- pip dependencies (requirements.txt)\n' +
					'- PyTorch (GPU-aware)\n' +
					'- Ollama (local LLM)\n' +
					'- Docker (containerization)\n' +
					'- VS Code extension\n' +
					'- SLATE custom models\n' +
					'- Workspace configuration\n\n' +
					'Continue?'
				),
			},
		};
	}
}

class UpdateTool implements vscode.LanguageModelTool<IUpdateParams> {
	async invoke(_options: vscode.LanguageModelToolInvocationOptions<IUpdateParams>, token: vscode.CancellationToken) {
		const output = await execSlateCommandLong('slate/slate_installer.py --update', token);
		return new vscode.LanguageModelToolResult([new vscode.LanguageModelTextPart(output)]);
	}

	async prepareInvocation(_options: vscode.LanguageModelToolInvocationPrepareOptions<IUpdateParams>, _token: vscode.CancellationToken) {
		return {
			invocationMessage: 'Updating SLATE from git...',
			confirmationMessages: {
				title: 'Update SLATE',
				message: new vscode.MarkdownString(
					'This will:\n\n' +
					'- Pull latest code from git\n' +
					'- Update pip dependencies\n' +
					'- Rebuild VS Code extension\n' +
					'- Re-validate ecosystem\n\n' +
					'Continue?'
				),
			},
		};
	}
}

class CheckDepsTool implements vscode.LanguageModelTool<ICheckDepsParams> {
	async invoke(_options: vscode.LanguageModelToolInvocationOptions<ICheckDepsParams>, token: vscode.CancellationToken) {
		const output = await execSlateCommand('slate/slate_installer.py --check', token);
		return new vscode.LanguageModelToolResult([new vscode.LanguageModelTextPart(output)]);
	}

	async prepareInvocation(_options: vscode.LanguageModelToolInvocationPrepareOptions<ICheckDepsParams>, _token: vscode.CancellationToken) {
		return { invocationMessage: 'Checking SLATE ecosystem dependencies...' };
	}
}

// ─── Registration ───────────────────────────────────────────────────────

export function registerSlateTools(context: vscode.ExtensionContext) {
	context.subscriptions.push(vscode.lm.registerTool('slate_systemStatus', new SystemStatusTool()));
	context.subscriptions.push(vscode.lm.registerTool('slate_runtimeCheck', new RuntimeCheckTool()));
	context.subscriptions.push(vscode.lm.registerTool('slate_runnerStatus', new RunnerStatusTool()));
	context.subscriptions.push(vscode.lm.registerTool('slate_hardwareInfo', new HardwareInfoTool()));
	context.subscriptions.push(vscode.lm.registerTool('slate_orchestrator', new OrchestratorTool()));
	context.subscriptions.push(vscode.lm.registerTool('slate_workflow', new WorkflowTool()));
	context.subscriptions.push(vscode.lm.registerTool('slate_benchmark', new BenchmarkTool()));
	context.subscriptions.push(vscode.lm.registerTool('slate_runCommand', new RunCommandTool()));
	context.subscriptions.push(vscode.lm.registerTool('slate_install', new InstallTool()));
	context.subscriptions.push(vscode.lm.registerTool('slate_update', new UpdateTool()));
	context.subscriptions.push(vscode.lm.registerTool('slate_checkDeps', new CheckDepsTool()));
}
