# /slate-diagnose

Run diagnostics on the SLATE plugin installation.

## Instructions

Run the SLATE plugin diagnostic tool to check:
- Python environment and venv
- Plugin directory structure
- Slash commands availability
- Skills configuration
- MCP server configuration
- Hooks configuration

Execute this command:

```powershell
python slate/plugin_diagnose.py
```

Or if running from the cached plugin location:

```powershell
python "${SLATE_PLUGIN_ROOT}/slate/plugin_diagnose.py"
```

## Expected Output

The diagnostic tool will show:
- [OK] for passing checks
- [WARN] for non-critical issues
- [FAIL] for problems that need fixing

## Common Issues

### MCP Server Not Connecting
- Check that Python is in PATH or .venv exists
- Verify ${CLAUDE_PLUGIN_ROOT} is set correctly
- Run `claude mcp list` to see server status

### Commands Not Loading
- Verify .claude/commands/*.md files exist
- Check plugin.json points to correct commands path
- Run `/plugin validate` to check structure

### Skills Not Available
- Verify skills/*/SKILL.md files exist
- Check plugin.json points to correct skills path
