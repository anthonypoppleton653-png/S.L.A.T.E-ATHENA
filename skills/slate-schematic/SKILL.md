---
name: slate-schematic
description: Generate circuit-board style system diagrams and architecture visualizations.
---

# /slate-schematic

Generate SLATE system schematics and diagrams.

## Usage
/slate-schematic [from-system | from-tech-tree | components]

## Description

This skill generates visual schematics including:
- System architecture diagrams
- Tech tree visualizations
- Component relationship maps
- Blueprint-style SVG output

## Instructions

When the user invokes this skill, generate schematics:

**From current system:**
```powershell
.\.venv\Scripts\python.exe -c "from slate.mcp_server import slate_schematic; print(slate_schematic('from-system'))"
```

**From tech tree:**
```powershell
.\.venv\Scripts\python.exe -c "from slate.mcp_server import slate_schematic; print(slate_schematic('from-tech-tree'))"
```

**List components:**
```powershell
.\.venv\Scripts\python.exe -c "from slate.mcp_server import slate_schematic; print(slate_schematic('components'))"
```

Output is saved to `docs/assets/slate-schematic.svg`.

## Examples

User: "/slate-schematic"
→ Generate system diagram from current state

User: "/slate-schematic from-tech-tree"
→ Generate tech tree progress diagram

User: "Show me the architecture"
→ Invoke this skill with from-system action
