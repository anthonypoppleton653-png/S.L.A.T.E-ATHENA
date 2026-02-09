---
name: slate-typescript
description: 'Coding standards for SLATE VS Code extensions and TypeScript modules'
applyTo: 'plugins/**/*.ts, plugins/**/*.tsx'
tags: [typescript, vscode, extension, slate]
---

# SLATE TypeScript Coding Standards

These instructions apply to all TypeScript files in SLATE VS Code extensions.

## Code Modification Header

**Every code edit MUST include a timestamp + author comment:**

```typescript
// Modified: YYYY-MM-DDTHH:MM:SSZ | Author: COPILOT | Change: description
```

## Extension Architecture (v5.1.0)

SLATE extensions use container-first architecture:

```
┌─────────────────────────────────────────────────────┐
│  VS Code Extension                                  │
│  ├── extension.ts          # Entry point            │
│  ├── slateRuntimeBackend   # K8s/Docker execution   │
│  ├── slateRuntimeAdapter   # Service URLs, health   │
│  ├── slateParticipant      # @slate chat            │
│  └── tools.ts              # 30+ LM Tools           │
└─────────────────────────────────────────────────────┘
         │
         ▼ HTTP POST / docker exec
┌─────────────────────────────────────────────────────┐
│  Kubernetes (copilot-bridge-svc:8083)               │
│  OR Docker (container: slate)                       │
└─────────────────────────────────────────────────────┘
```

## No Local Fallback

All command execution goes through K8s or Docker. Never add local Python fallback:

```typescript
// CORRECT - Container execution
async function executeCommand(cmd: string): Promise<string> {
    const backend = await getActiveBackend();
    if (backend === 'kubernetes') {
        return await httpPost('http://127.0.0.1:8083/api/exec', { command: cmd });
    } else if (backend === 'docker') {
        return await dockerExec('slate', `python ${cmd}`);
    }
    throw new Error('No backend available - deploy SLATE first');
}

// WRONG - No local execution
async function executeCommand(cmd: string): Promise<string> {
    return await execSync(`python ${cmd}`);  // Don't do this
}
```

## Language Model Tools

Define tools with proper schemas using Zod:

```typescript
import { z } from 'zod';
import { vscode } from 'vscode';

const SlateStatusTool: vscode.LanguageModelTool<{ format: string }> = {
    name: 'slate_systemStatus',
    description: 'Check SLATE system health including GPU, services, and K8s',
    inputSchema: z.object({
        format: z.enum(['quick', 'json', 'full']).default('quick')
            .describe('Output format')
    }),
    async invoke(options, token) {
        const result = await slateRunner.run(
            `slate/slate_status.py --${options.input.format}`
        );
        return { content: [{ type: 'text', text: result }] };
    }
};
```

## ActionGuard Integration

Use `slateAgentSdkHooks.ts` for security validation:

```typescript
import { validateBashCommand, validateFilePath } from './slateAgentSdkHooks';

// Validate before execution
const validation = await validateBashCommand(command);
if (!validation.allowed) {
    throw new Error(`Blocked by ActionGuard: ${validation.reason}`);
}
```

## Error Handling

Use try-catch with specific error types:

```typescript
try {
    const result = await slateRunner.run(command);
    return result;
} catch (error) {
    if (error instanceof BackendUnavailableError) {
        vscode.window.showWarningMessage(
            'SLATE backend not available. Deploy with K8s or Docker first.'
        );
    } else if (error instanceof ActionGuardError) {
        vscode.window.showErrorMessage(`Blocked: ${error.message}`);
    } else {
        throw error;
    }
}
```

## Activation Events

Extensions should activate on workspace open:

```json
{
    "activationEvents": [
        "onStartupFinished",
        "workspaceContains:**/CLAUDE.md",
        "workspaceContains:**/slate/**"
    ]
}
```

## Service Health Monitoring

Use `slateRuntimeAdapter` for service health:

```typescript
import { SlateRuntimeAdapter } from './slateRuntimeAdapter';

const adapter = new SlateRuntimeAdapter();
const health = await adapter.checkHealth();

if (!health.kubernetes && !health.docker) {
    // Show deploy guidance
    await showDeploymentPanel();
}
```
