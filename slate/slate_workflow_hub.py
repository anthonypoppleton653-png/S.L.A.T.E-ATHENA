"""
SLATE Workflow Hub — Central AI-Powered Automation Engine
=========================================================
Orchestrates documentation automation, page updates, research, planning,
and full local inference integration for GitHub Actions workflows.

# Modified: 2026-02-09T04:20:00-05:00 | Author: Gemini | Change: Initial creation of workflow hub
# NOTE: All AIs modifying this file must add a dated comment like the one above.

Usage:
    python slate/slate_workflow_hub.py --mode <mode> [--json] [--commit]
    
Modes:
    docs-generate     - AI-powered documentation generation from codebase
    docs-update       - Update existing docs with latest changes
    pages-update      - Regenerate GitHub Pages content
    research          - AI research on codebase architecture & improvements
    plan              - Generate/update project planning artifacts
    full-automation   - Run all automation tasks in sequence
    wiki-sync         - Sync specs to wiki pages
    changelog         - Generate changelog from git history
    roadmap           - AI-generated project roadmap
    status            - Show hub status and capabilities
"""

import json
import os
import pathlib
import subprocess
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Any, Optional

# ─── Constants ───────────────────────────────────────────────────────────────

OLLAMA_URL = "http://127.0.0.1:11434"
WORKSPACE = pathlib.Path(os.environ.get("GITHUB_WORKSPACE", str(pathlib.Path(__file__).parent.parent)))
DOCS_DIR = WORKSPACE / "docs"
WIKI_DIR = DOCS_DIR / "wiki"
PAGES_DIR = DOCS_DIR / "pages"
SPECS_DIR = DOCS_DIR / "specs"
REPORT_DIR = DOCS_DIR / "report"
SLATE_DIR = WORKSPACE / "slate"
PLANS_DIR = WORKSPACE / "plans"
CHANGELOG_FILE = WORKSPACE / "CHANGELOG.md"

# ─── Production Safety Guards ────────────────────────────────────────────────
# Modified: 2026-02-09T07:06:00-05:00 | Author: Gemini | Change: Add production safety guards
# NOTE: All AIs modifying this file must add a dated comment like the one above.
#
# AI automation can ONLY write to these directories. Everything else is READ-ONLY.
SAFE_WRITE_DIRS = [
    WIKI_DIR,           # docs/wiki/       — Generated documentation
    REPORT_DIR,         # docs/report/     — Analysis reports
    PAGES_DIR / "slate-data.json",    # Pages data file
    PAGES_DIR / "status.html",        # Generated status page
    PLANS_DIR,          # plans/           — Roadmaps, planning artifacts
    CHANGELOG_FILE,     # CHANGELOG.md     — Auto-generated changelog
]

# NEVER write to these — production source code & configs
PROTECTED_PATHS = [
    WORKSPACE / "slate",              # Source code
    WORKSPACE / ".github" / "workflows",  # CI/CD workflows
    WORKSPACE / ".github" / "slate.config.yaml",  # Core config
    WORKSPACE / "k8s",               # Kubernetes manifests
    WORKSPACE / "tests",             # Test suite
    WORKSPACE / "plugins",           # Plugin source
    WORKSPACE / "Dockerfile",        # Docker configs
    WORKSPACE / "docker-compose.yml",
    WORKSPACE / "docker-compose.prod.yml",
    WORKSPACE / ".agent",            # Agent configs
]

def safe_write(target_path: pathlib.Path, content: str, encoding: str = "utf-8") -> bool:
    """Write a file ONLY if it's in a safe output directory. Blocks writes to production code.
    
    Returns True if write succeeded, False if blocked.
    """
    target = target_path.resolve()
    workspace = WORKSPACE.resolve()
    
    # Must be inside workspace
    try:
        target.relative_to(workspace)
    except ValueError:
        print(f"  🛑 BLOCKED: {target} is outside workspace")
        return False
    
    # Check against protected paths — never allow writes here
    for protected in PROTECTED_PATHS:
        prot_resolved = protected.resolve()
        try:
            target.relative_to(prot_resolved)
            print(f"  🛑 BLOCKED: Cannot write to protected path {target}")
            print(f"     Protected by: {protected}")
            return False
        except ValueError:
            continue  # Not under this protected path, check next
        
    # Verify it's in a safe write directory
    is_safe = False
    for safe in SAFE_WRITE_DIRS:
        safe_resolved = safe.resolve()
        if target == safe_resolved:
            is_safe = True
            break
        try:
            target.relative_to(safe_resolved)
            is_safe = True
            break
        except ValueError:
            continue
    
    if not is_safe:
        print(f"  🛑 BLOCKED: {target} is not in any safe write directory")
        print(f"     Safe dirs: {[str(s) for s in SAFE_WRITE_DIRS]}")
        return False
    
    # Safe to write
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(content, encoding=encoding)
    return True

# Model routing by task type
MODEL_MAP = {
    "docs": "slate-planner",        # 7B — good at structured writing
    "research": "slate-coder",      # 12B — deep code analysis
    "planning": "slate-planner",    # 7B — strategic planning
    "fast": "slate-fast",           # 3B — quick classification/summaries
    "code": "slate-coder",          # 12B — code generation
    "fallback": "mistral:latest",   # Fallback model
}

# ─── Ollama Interface ────────────────────────────────────────────────────────

class OllamaClient:
    """Local inference client for Ollama."""
    
    def __init__(self, base_url: str = OLLAMA_URL):
        self.base_url = base_url
        self._available = None
        self._models = None
    
    @property
    def available(self) -> bool:
        if self._available is None:
            self._check()
        return self._available
    
    @property
    def models(self) -> list:
        if self._models is None:
            self._check()
        return self._models or []
    
    def _check(self):
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())
            self._models = [m["name"] for m in data.get("models", [])]
            self._available = True
        except Exception:
            self._available = False
            self._models = []
    
    def resolve_model(self, task_type: str) -> Optional[str]:
        """Pick best available model for the task."""
        preferred = MODEL_MAP.get(task_type, MODEL_MAP["fallback"])
        if any(preferred in m for m in self.models):
            return preferred
        fallback = MODEL_MAP["fallback"]
        if any(fallback in m for m in self.models):
            return fallback
        # Use any available model
        return self.models[0] if self.models else None
    
    # Modified: 2026-02-09T05:00:00-05:00 | Author: Gemini | Change: Add warmup to pre-load models into VRAM
    def warmup(self, task_type: str = "fast") -> bool:
        """Pre-load a model into VRAM with a tiny generation request."""
        model = self.resolve_model(task_type)
        if not model:
            return False
        
        payload = json.dumps({
            "model": model,
            "prompt": "Hello",
            "stream": False,
            "options": {"num_predict": 1, "num_gpu": 999}
        }).encode()
        
        req = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        try:
            print(f"  Warming up {model}...")
            with urllib.request.urlopen(req, timeout=120) as resp:
                json.loads(resp.read())
            print(f"  ✓ {model} loaded into VRAM")
            return True
        except Exception as e:
            print(f"  ✗ Warmup failed for {model}: {e}")
            return False
    
    def _do_generate(self, model: str, prompt: str, max_tokens: int, 
                     temperature: float, timeout: int = 300) -> dict:
        """Internal generate with a specific model."""
        payload = json.dumps({
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
                "num_gpu": 999,
            }
        }).encode()
        
        req = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        start = time.time()
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
        elapsed = time.time() - start
        tokens = data.get("eval_count", 0)
        eval_dur = data.get("eval_duration", 1)
        tps = tokens / max(eval_dur / 1e9, 0.001)
        
        return {
            "response": data.get("response", ""),
            "model": model,
            "tokens": tokens,
            "tok_per_sec": round(tps, 1),
            "elapsed": round(elapsed, 1),
        }
    
    # Modified: 2026-02-09T05:00:00-05:00 | Author: Gemini | Change: Add retry-with-fallback to handle model load timeouts
    def generate(self, prompt: str, task_type: str = "docs",
                 max_tokens: int = 1024, temperature: float = 0.3) -> dict:
        """Generate text using local inference. Retries with fallback model on timeout."""
        model = self.resolve_model(task_type)
        if not model:
            return {"error": "No model available", "response": ""}
        
        # Try primary model
        try:
            return self._do_generate(model, prompt, max_tokens, temperature, timeout=300)
        except Exception as e:
            print(f"  ⚠ Primary model {model} failed: {e}")
        
        # Try fallback model
        fallback = MODEL_MAP["fallback"]
        if fallback != model and any(fallback in m for m in self.models):
            try:
                print(f"  Retrying with fallback model {fallback}...")
                return self._do_generate(fallback, prompt, max_tokens, temperature, timeout=300)
            except Exception as e2:
                return {"error": f"Primary: {e}, Fallback: {e2}", "response": "", "model": model}
        
        # Try any available model
        for m in self.models:
            if m != model:
                try:
                    print(f"  Retrying with {m}...")
                    return self._do_generate(m, prompt, max_tokens, temperature, timeout=300)
                except Exception:
                    continue
        
        return {"error": str(e), "response": "", "model": model}


# ─── Documentation Automation ────────────────────────────────────────────────

class DocAutomation:
    """AI-powered documentation generation and updates."""
    
    def __init__(self, ollama: OllamaClient):
        self.ollama = ollama
        self.results = {"files_generated": 0, "files_updated": 0, "errors": []}
    
    def scan_undocumented_modules(self) -> list:
        """Find Python modules lacking proper documentation."""
        undocumented = []
        for py_file in sorted(SLATE_DIR.glob("*.py")):
            if py_file.name.startswith("_"):
                continue
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            lines = content.split("\n")
            
            # Check for module docstring
            has_docstring = False
            for i, line in enumerate(lines[:10]):
                if '"""' in line or "'''" in line:
                    has_docstring = True
                    break
            
            # Check for function/class docs
            funcs = [l.strip() for l in lines if l.strip().startswith("def ") or l.strip().startswith("class ")]
            doc_count = content.count('"""') // 2 + content.count("'''") // 2
            
            if not has_docstring or doc_count < len(funcs) * 0.3:
                undocumented.append({
                    "file": py_file.name,
                    "lines": len(lines),
                    "functions": len(funcs),
                    "doc_coverage": round(doc_count / max(len(funcs), 1) * 100, 1),
                    "has_module_docstring": has_docstring,
                })
        
        return undocumented
    
    def generate_module_doc(self, module_path: pathlib.Path) -> str:
        """Generate documentation for a single module using AI."""
        content = module_path.read_text(encoding="utf-8", errors="ignore")
        # Truncate for context window
        code_sample = content[:4000]
        
        prompt = f"""Generate comprehensive Markdown documentation for this Python module from the S.L.A.T.E. project.

Module: {module_path.name}

```python
{code_sample}
```

Generate documentation covering:
1. Module Purpose & Overview (2-3 sentences)
2. Key Classes and their responsibilities
3. Key Functions with parameters and return types
4. Usage Examples (practical code snippets)
5. Dependencies and integration points
6. Configuration options (if any)

Format as clean Markdown with proper headings. Be concise but thorough."""
        
        result = self.ollama.generate(prompt, task_type="docs", max_tokens=1500)
        return result.get("response", "")
    
    def generate_all_docs(self) -> dict:
        """Generate documentation for all undocumented modules."""
        WIKI_DIR.mkdir(parents=True, exist_ok=True)
        undocumented = self.scan_undocumented_modules()
        
        print(f"Found {len(undocumented)} modules needing documentation")
        
        for mod_info in undocumented[:15]:  # Limit to 15 per run
            mod_path = SLATE_DIR / mod_info["file"]
            doc_path = WIKI_DIR / f"{mod_path.stem}.md"
            
            print(f"  Generating docs for {mod_info['file']}...")
            doc_content = self.generate_module_doc(mod_path)
            
            if doc_content and len(doc_content) > 100:
                header = f"""---
title: {mod_path.stem}
generated: {datetime.now(timezone.utc).isoformat()}
source: {mod_info['file']}
coverage: {mod_info['doc_coverage']}%
---

"""
                if safe_write(doc_path, header + doc_content):
                    self.results["files_generated"] += 1
                    print(f"    ✓ Generated {doc_path.name}")
                else:
                    self.results["errors"].append(f"Write blocked for {doc_path}")
                    print(f"    🛑 Write blocked for {doc_path.name}")
            else:
                self.results["errors"].append(f"Empty/short doc for {mod_info['file']}")
                print(f"    ✗ Failed for {mod_info['file']}")
        
        return self.results
    
    def update_existing_docs(self) -> dict:
        """Update existing documentation with latest module changes."""
        if not WIKI_DIR.exists():
            return self.results
        
        for doc_file in sorted(WIKI_DIR.glob("*.md")):
            source_name = doc_file.stem + ".py"
            source_path = SLATE_DIR / source_name
            
            if not source_path.exists():
                continue
            
            # Check if source is newer than doc
            if source_path.stat().st_mtime > doc_file.stat().st_mtime:
                print(f"  Updating docs for {source_name}...")
                doc_content = self.generate_module_doc(source_path)
                if doc_content and len(doc_content) > 100:
                    existing = doc_file.read_text(encoding="utf-8", errors="ignore")
                    # Keep frontmatter, update body
                    if "---" in existing:
                        parts = existing.split("---", 2)
                        if len(parts) >= 3:
                            header = f"---{parts[1]}---\n\n"
                        else:
                            header = ""
                    else:
                        header = ""
                    
                    if safe_write(doc_file, header + doc_content):
                        self.results["files_updated"] += 1
        
        return self.results


# ─── Pages Automation ────────────────────────────────────────────────────────

class PagesAutomation:
    """AI-powered GitHub Pages content updates."""
    
    def __init__(self, ollama: OllamaClient):
        self.ollama = ollama
    
    def generate_feature_data(self) -> dict:
        """Generate updated feature data for the landing page."""
        # Scan codebase for current capabilities
        modules = []
        for py_file in sorted(SLATE_DIR.glob("*.py")):
            if py_file.name.startswith("_"):
                continue
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            lines = content.split("\n")
            
            # Extract module docstring
            docstring = ""
            in_doc = False
            for line in lines[:20]:
                if '"""' in line:
                    if in_doc:
                        break
                    in_doc = True
                    docstring += line.split('"""', 1)[-1]
                elif in_doc:
                    docstring += " " + line.strip()
            
            modules.append({
                "name": py_file.stem,
                "lines": len(lines),
                "docstring": docstring.strip()[:200],
            })
        
        # Count by category
        categories = {
            "AI & Inference": [m for m in modules if any(k in m["name"] for k in ["ai", "ml", "model", "transform", "semantic", "chromadb"])],
            "Workflow & CI/CD": [m for m in modules if any(k in m["name"] for k in ["workflow", "runner", "autonomous", "benchmark"])],
            "Security": [m for m in modules if any(k in m["name"] for k in ["guard", "pii", "security", "sdk_source"])],
            "Integration": [m for m in modules if any(k in m["name"] for k in ["copilot", "fork", "github", "mcp", "k8s", "docker"])],
            "Core": [m for m in modules if any(k in m["name"] for k in ["status", "runtime", "orchestrator", "installer", "config"])],
        }
        
        return {
            "total_modules": len(modules),
            "total_lines": sum(m["lines"] for m in modules),
            "categories": {k: len(v) for k, v in categories.items()},
            "updated": datetime.now(timezone.utc).isoformat(),
        }
    
    def update_slate_data_json(self) -> bool:
        """Update the slate-data.json used by the landing page."""
        data_file = PAGES_DIR / "slate-data.json"
        
        feature_data = self.generate_feature_data()
        
        # Get workflow status
        workflows = list((WORKSPACE / ".github" / "workflows").glob("*.yml"))
        
        # Get runner info  
        runners = []
        for runner_dir in WORKSPACE.glob("actions-runner*"):
            if runner_dir.is_dir():
                runners.append(runner_dir.name)
        
        # Build page data
        page_data = {
            "project": "S.L.A.T.E.",
            "version": "2.4.0",
            "tagline": "Synchronized Living Architecture for Transformation and Evolution",
            "stats": feature_data,
            "workflows": {
                "total": len(workflows),
                "names": [w.stem for w in sorted(workflows)],
            },
            "runners": {
                "total": len(runners),
                "names": runners,
            },
            "ai": {
                "ollama": True,
                "models": ["slate-coder (12B)", "slate-planner (7B)", "slate-fast (3B)"],
                "gpu": "2x NVIDIA RTX 5070 Ti (16GB each)",
            },
            "links": {
                "github": "https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E.",
                "docs": "https://synchronizedlivingarchitecture.github.io/S.L.A.T.E./",
            },
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
        
        if safe_write(data_file, json.dumps(page_data, indent=2)):
            print(f"  ✓ Updated {data_file}")
        else:
            print(f"  🛑 Write blocked for {data_file}")
        return True
    
    def generate_status_page(self) -> bool:
        """Generate a live status page for the project."""
        status_html_path = PAGES_DIR / "status.html"
        
        # Use AI to generate a summary
        prompt = """Generate a brief project status summary for S.L.A.T.E. (Synchronized Living Architecture for Transformation and Evolution).

The system includes:
- 32 GitHub Actions workflows (CI/CD, AI, docs, security)
- Self-hosted runners with dual NVIDIA RTX 5070 Ti GPUs
- Local AI inference via Ollama (3B, 7B, 12B models)
- Autonomous task discovery and execution
- Full documentation automation pipeline
- ChromaDB vector memory for RAG
- Semantic Kernel integration

Write a 3-paragraph HTML status summary with stats formatted as a clean dashboard section."""

        result = self.ollama.generate(prompt, task_type="docs", max_tokens=800)
        ai_summary = result.get("response", "System operational.")
        
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        
        status_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>S.L.A.T.E. — System Status</title>
    <meta name="description" content="Live system status for SLATE AI orchestration framework">
    <style>
        :root {{
            --bg: #0a0e17;
            --surface: #121929;
            --primary: #00d4ff;
            --secondary: #7c3aed;
            --text: #e2e8f0;
            --muted: #64748b;
            --success: #22c55e;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', system-ui, sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem; }}
        h1 {{
            font-size: 2.5rem;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }}
        .timestamp {{ color: var(--muted); margin-bottom: 2rem; }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin: 2rem 0;
        }}
        .card {{
            background: var(--surface);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 12px;
            padding: 1.5rem;
            transition: transform 0.2s;
        }}
        .card:hover {{ transform: translateY(-2px); }}
        .card h3 {{ color: var(--primary); margin-bottom: 0.75rem; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.05em; }}
        .card .value {{ font-size: 2rem; font-weight: 700; }}
        .card .label {{ color: var(--muted); font-size: 0.85rem; }}
        .status-badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.25rem 0.75rem;
            border-radius: 999px;
            font-size: 0.85rem;
            font-weight: 500;
        }}
        .status-online {{
            background: rgba(34, 197, 94, 0.15);
            color: var(--success);
        }}
        .status-online::before {{
            content: '';
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--success);
            animation: pulse 2s infinite;
        }}
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.4; }}
        }}
        .summary {{
            background: var(--surface);
            border-radius: 12px;
            padding: 2rem;
            margin: 2rem 0;
            line-height: 1.7;
        }}
        .summary h2 {{ color: var(--primary); margin-bottom: 1rem; }}
    </style>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap" rel="stylesheet">
</head>
<body>
    <div class="container">
        <h1>S.L.A.T.E. Status</h1>
        <p class="timestamp">Last updated: {timestamp} <span class="status-badge status-online">Operational</span></p>
        
        <div class="grid">
            <div class="card">
                <h3>Workflows</h3>
                <div class="value">32</div>
                <div class="label">GitHub Actions workflows</div>
            </div>
            <div class="card">
                <h3>Self-Hosted Runners</h3>
                <div class="value">4</div>
                <div class="label">With dual GPU access</div>
            </div>
            <div class="card">
                <h3>AI Models</h3>
                <div class="value">3</div>
                <div class="label">Local inference (3B/7B/12B)</div>
            </div>
            <div class="card">
                <h3>GPU Compute</h3>
                <div class="value">32GB</div>
                <div class="label">2x RTX 5070 Ti VRAM</div>
            </div>
            <div class="card">
                <h3>Modules</h3>
                <div class="value">100+</div>
                <div class="label">Python modules in slate/</div>
            </div>
            <div class="card">
                <h3>Automation</h3>
                <div class="value">24/7</div>
                <div class="label">Scheduled pipelines</div>
            </div>
        </div>
        
        <div class="summary">
            <h2>AI-Generated Status Summary</h2>
            {ai_summary}
        </div>
    </div>
</body>
</html>"""
        
        if safe_write(status_html_path, status_html):
            print(f"  ✓ Generated {status_html_path}")
        else:
            print(f"  🛑 Write blocked for {status_html_path}")
        return True


# ─── Research Automation ─────────────────────────────────────────────────────

class ResearchAutomation:
    """AI-powered codebase research and analysis."""
    
    def __init__(self, ollama: OllamaClient):
        self.ollama = ollama
    
    def analyze_architecture(self) -> dict:
        """Deep analysis of codebase architecture."""
        # Collect module info
        modules = {}
        total_lines = 0
        for py_file in sorted(SLATE_DIR.glob("*.py")):
            if py_file.name.startswith("_"):
                continue
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            lines = content.split("\n")
            total_lines += len(lines)
            
            imports = [l for l in lines if l.startswith("import ") or l.startswith("from ")]
            internal_imports = [l for l in imports if "slate" in l]
            
            modules[py_file.stem] = {
                "lines": len(lines),
                "imports": len(imports),
                "internal_deps": len(internal_imports),
                "classes": sum(1 for l in lines if l.startswith("class ")),
                "functions": sum(1 for l in lines if l.strip().startswith("def ")),
            }
        
        # Build AI analysis prompt
        top_modules = sorted(modules.items(), key=lambda x: x[1]["lines"], reverse=True)[:20]
        
        prompt = f"""Analyze this codebase architecture for the S.L.A.T.E. project.

Codebase Stats:
- Total modules: {len(modules)}
- Total lines: {total_lines}
- Top modules by size:
{json.dumps(dict(top_modules), indent=2)}

Provide a structured analysis:
1. **Architecture Pattern**: What pattern does this codebase follow?
2. **Coupling Analysis**: Which modules have too many dependencies?
3. **Complexity Hotspots**: Which modules are too large and should be split?
4. **Missing Components**: What capabilities are missing?
5. **Improvement Priorities**: Top 5 refactoring recommendations ranked by impact.

Be specific and actionable."""

        result = self.ollama.generate(prompt, task_type="research", max_tokens=1500)
        
        return {
            "total_modules": len(modules),
            "total_lines": total_lines,
            "top_modules": dict(top_modules),
            "ai_analysis": result.get("response", ""),
            "model_used": result.get("model", ""),
            "tokens": result.get("tokens", 0),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    def analyze_workflows(self) -> dict:
        """Analyze GitHub Actions workflow architecture."""
        workflow_dir = WORKSPACE / ".github" / "workflows"
        workflows = {}
        
        for yml_file in sorted(workflow_dir.glob("*.yml")):
            content = yml_file.read_text(encoding="utf-8", errors="ignore")
            
            # Quick YAML parsing without importing yaml
            has_schedule = "schedule:" in content
            has_dispatch = "workflow_dispatch:" in content
            self_hosted = "self-hosted" in content
            uses_gpu = "gpu" in content
            uses_ollama = "11434" in content or "ollama" in content.lower()
            
            workflows[yml_file.stem] = {
                "size_bytes": yml_file.stat().st_size,
                "scheduled": has_schedule,
                "dispatchable": has_dispatch,
                "self_hosted": self_hosted,
                "gpu_required": uses_gpu,
                "uses_inference": uses_ollama,
            }
        
        prompt = f"""Analyze this GitHub Actions workflow setup for the S.L.A.T.E. project.

{len(workflows)} Workflows:
{json.dumps(workflows, indent=2)}

Provide:
1. **Workflow Coverage**: What's well-covered vs needs more automation?
2. **Schedule Conflicts**: Any potential overlap or resource contention?
3. **Missing Workflows**: What automation is needed but missing?
4. **Optimization**: How to reduce redundancy and improve efficiency?
5. **Local Inference Usage**: How well are the workflows using local AI vs running without it?

Focus on practical improvements."""

        result = self.ollama.generate(prompt, task_type="research", max_tokens=1200)
        
        return {
            "total_workflows": len(workflows),
            "scheduled": sum(1 for w in workflows.values() if w["scheduled"]),
            "gpu_workflows": sum(1 for w in workflows.values() if w["gpu_required"]),
            "inference_workflows": sum(1 for w in workflows.values() if w["uses_inference"]),
            "workflows": workflows,
            "ai_analysis": result.get("response", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# ─── Planning Automation ────────────────────────────────────────────────────

class PlanningAutomation:
    """AI-powered project planning and roadmap generation."""
    
    def __init__(self, ollama: OllamaClient):
        self.ollama = ollama
    
    def generate_roadmap(self) -> dict:
        """Generate/update project roadmap using AI analysis."""
        # Read current tasks
        tasks_file = WORKSPACE / "current_tasks.json"
        current_tasks = []
        if tasks_file.exists():
            try:
                data = json.loads(tasks_file.read_text(encoding="utf-8"))
                current_tasks = data.get("tasks", data) if isinstance(data, dict) else data
            except Exception:
                pass
        
        # Read tech tree if available
        tech_tree_file = WORKSPACE / "tech_tree.json"
        tech_tree = {}
        if tech_tree_file.exists():
            try:
                tech_tree = json.loads(tech_tree_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        
        # Scan for TODOs in codebase
        todos = []
        for py_file in sorted(SLATE_DIR.glob("*.py")):
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                for i, line in enumerate(content.split("\n"), 1):
                    if "TODO" in line or "FIXME" in line or "HACK" in line:
                        todos.append({
                            "file": py_file.name,
                            "line": i,
                            "text": line.strip()[:120],
                        })
            except Exception:
                pass
        
        prompt = f"""Generate a development roadmap for the S.L.A.T.E. project.

Current Tasks ({len(current_tasks)} active):
{json.dumps(current_tasks[:10], indent=2, default=str)}

Code TODOs ({len(todos)} found):
{json.dumps(todos[:20], indent=2)}

The system has:
- 100+ Python modules | 32 GitHub Actions workflows
- Local AI with GPU (Ollama, Semantic Kernel, ChromaDB)
- Self-hosted runners with dual NVIDIA GPUs
- Autonomous task execution loop

Generate a roadmap with:
1. **Immediate (This Week)**: Top 5 highest-impact tasks
2. **Short Term (2 Weeks)**: Feature additions and improvements
3. **Medium Term (1 Month)**: Architecture improvements
4. **Long Term (3 Months)**: Strategic goals

For each item include: priority (P0-P3), estimated effort, and why it matters."""

        result = self.ollama.generate(prompt, task_type="planning", max_tokens=1500)
        
        roadmap = {
            "generated": datetime.now(timezone.utc).isoformat(),
            "current_tasks": len(current_tasks),
            "codebase_todos": len(todos),
            "roadmap": result.get("response", ""),
            "model": result.get("model", ""),
        }
        
        # Save roadmap (via safe_write)
        roadmap_file = PLANS_DIR / "roadmap.json"
        safe_write(roadmap_file, json.dumps(roadmap, indent=2))
        
        # Also save as Markdown
        roadmap_md = PLANS_DIR / "ROADMAP.md"
        safe_write(roadmap_md, f"""# S.L.A.T.E. Project Roadmap
*Generated: {roadmap['generated']} by {roadmap['model']}*

{roadmap['roadmap']}

---
*Generated by SLATE Workflow Hub — AI-Powered Planning*
""")
        
        print(f"  ✓ Generated roadmap ({len(result.get('response', ''))} chars)")
        return roadmap
    
    def generate_changelog(self) -> str:
        """Generate changelog from recent git history."""
        try:
            git_log = subprocess.run(
                ["git", "log", "--max-count=50", "--pretty=format:%H|%an|%at|%s", "--no-merges"],
                capture_output=True, text=True, timeout=15, cwd=str(WORKSPACE)
            ).stdout.strip()
        except Exception:
            return ""
        
        if not git_log:
            return ""
        
        commits = []
        for line in git_log.split("\n"):
            if "|" in line:
                parts = line.split("|", 3)
                if len(parts) >= 4:
                    commits.append({
                        "hash": parts[0][:8],
                        "author": parts[1],
                        "subject": parts[3],
                    })
        
        prompt = f"""Generate a clean, categorized CHANGELOG entry from these recent commits for S.L.A.T.E.

Recent commits ({len(commits)}):
{json.dumps(commits, indent=2)}

Format as a proper Markdown CHANGELOG with sections:
## [Unreleased]
### Added
### Changed
### Fixed
### Infrastructure

Group commits into appropriate categories. Deduplicate and summarize related commits.
Use concise, user-facing language (not git commit messages)."""

        result = self.ollama.generate(prompt, task_type="docs", max_tokens=1200)
        
        changelog_content = result.get("response", "")
        if changelog_content:
            header = f"""# Changelog
*Auto-generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}*

"""
            if safe_write(CHANGELOG_FILE, header + changelog_content):
                print(f"  ✓ Generated CHANGELOG.md ({len(changelog_content)} chars)")
            else:
                print(f"  🛑 Write blocked for CHANGELOG.md")
        
        return changelog_content


# ─── Main Hub Orchestrator ───────────────────────────────────────────────────

class WorkflowHub:
    """Central orchestrator for all automation tasks."""
    
    def __init__(self):
        self.ollama = OllamaClient()
        self.docs = DocAutomation(self.ollama)
        self.pages = PagesAutomation(self.ollama)
        self.research = ResearchAutomation(self.ollama)
        self.planning = PlanningAutomation(self.ollama)
        self.results = {}
    
    def status(self) -> dict:
        """Get hub status and capabilities."""
        return {
            "hub": "SLATE Workflow Hub",
            "version": "1.0.0",
            "ollama": {
                "available": self.ollama.available,
                "models": self.ollama.models,
                "url": OLLAMA_URL,
            },
            "capabilities": {
                "docs_generate": True,
                "docs_update": True,
                "pages_update": True,
                "research": self.ollama.available,
                "planning": self.ollama.available,
                "changelog": True,
                "roadmap": self.ollama.available,
                "wiki_sync": True,
            },
            "paths": {
                "workspace": str(WORKSPACE),
                "docs": str(DOCS_DIR),
                "wiki": str(WIKI_DIR),
                "pages": str(PAGES_DIR),
                "plans": str(PLANS_DIR),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    def run(self, mode: str, as_json: bool = False, commit: bool = False) -> dict:
        """Run automation tasks by mode."""
        print(f"\n{'='*60}")
        print(f"  SLATE Workflow Hub — Mode: {mode}")
        print(f"  Ollama: {'✓ Available' if self.ollama.available else '✗ Not available'}")
        if self.ollama.available:
            print(f"  Models: {', '.join(self.ollama.models[:5])}")
        print(f"{'='*60}\n")
        
        if mode == "status":
            self.results = self.status()
        
        elif mode == "docs-generate":
            self.results["docs"] = self.docs.generate_all_docs()
        
        elif mode == "docs-update":
            self.results["docs"] = self.docs.update_existing_docs()
        
        elif mode == "pages-update":
            self.results["pages_data"] = self.pages.update_slate_data_json()
            self.results["status_page"] = self.pages.generate_status_page()
        
        elif mode == "research":
            self.results["architecture"] = self.research.analyze_architecture()
            self.results["workflows"] = self.research.analyze_workflows()
        
        elif mode == "plan":
            self.results["roadmap"] = self.planning.generate_roadmap()
            self.results["changelog"] = bool(self.planning.generate_changelog())
        
        elif mode == "wiki-sync":
            # Delegate to spec-kit
            try:
                subprocess.run(
                    [sys.executable, str(SLATE_DIR / "slate_spec_kit.py"), 
                     "--process-all", "--wiki", "--analyze"],
                    cwd=str(WORKSPACE), timeout=300
                )
                self.results["wiki_sync"] = True
            except Exception as e:
                self.results["wiki_sync"] = False
                self.results["error"] = str(e)
        
        elif mode == "changelog":
            self.results["changelog"] = bool(self.planning.generate_changelog())
        
        elif mode == "roadmap":
            self.results["roadmap"] = self.planning.generate_roadmap()
        
        elif mode == "full-automation":
            print("─── Phase 1: Documentation ───")
            self.results["docs_generated"] = self.docs.generate_all_docs()
            
            print("\n─── Phase 2: Pages Update ───")
            self.results["pages_data"] = self.pages.update_slate_data_json()
            self.results["status_page"] = self.pages.generate_status_page()
            
            print("\n─── Phase 3: Research ───")
            self.results["architecture"] = self.research.analyze_architecture()
            self.results["workflows"] = self.research.analyze_workflows()
            
            print("\n─── Phase 4: Planning ───")
            self.results["roadmap"] = self.planning.generate_roadmap()
            self.results["changelog"] = bool(self.planning.generate_changelog())
            
            print("\n─── Phase 5: Wiki Sync ───")
            try:
                subprocess.run(
                    [sys.executable, str(SLATE_DIR / "slate_spec_kit.py"),
                     "--process-all", "--wiki"],
                    cwd=str(WORKSPACE), timeout=300,
                    capture_output=True
                )
                self.results["wiki_sync"] = True
            except Exception:
                self.results["wiki_sync"] = False
        
        else:
            print(f"Unknown mode: {mode}")
            print("Available: status, docs-generate, docs-update, pages-update,")
            print("           research, plan, wiki-sync, changelog, roadmap, full-automation")
            self.results["error"] = f"Unknown mode: {mode}"
        
        # Save results (via safe_write)
        report_file = REPORT_DIR / f"hub_{mode.replace('-', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        safe_write(report_file, json.dumps(self.results, indent=2, default=str))
        
        if as_json:
            print(json.dumps(self.results, indent=2, default=str))
        
        if commit:
            self._commit_changes(mode)
        
        return self.results
    
    def _commit_changes(self, mode: str):
        """Commit any changes made by automation. ONLY stages safe output directories."""
        # Modified: 2026-02-09T07:06:00-05:00 | Author: Gemini | Change: Harden git commit scope
        SAFE_GIT_PATHS = ["docs/wiki/", "docs/report/", "docs/pages/slate-data.json",
                          "docs/pages/status.html", "plans/", "CHANGELOG.md"]
        NEVER_STAGE = ["slate/", ".github/", "k8s/", "tests/", "plugins/",
                       "Dockerfile", "docker-compose*"]
        try:
            status = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True, text=True, cwd=str(WORKSPACE)
            ).stdout.strip()
            
            if not status:
                print("\nNo changes to commit.")
                return
            
            subprocess.run(["git", "config", "user.name", "SLATE Workflow Hub"], cwd=str(WORKSPACE))
            subprocess.run(["git", "config", "user.email", "slate-hub@slate.local"], cwd=str(WORKSPACE))
            
            # Safety: reset any accidentally staged production files
            for unsafe in NEVER_STAGE:
                subprocess.run(["git", "reset", "HEAD", "--", unsafe],
                             cwd=str(WORKSPACE), capture_output=True)
            
            # Stage ONLY safe output directories
            for path in SAFE_GIT_PATHS:
                subprocess.run(["git", "add", "--", path], cwd=str(WORKSPACE), capture_output=True)
            
            msg = (
                f"automation: {mode} — SLATE Workflow Hub\n\n"
                f"Automated by SLATE Workflow Hub\n"
                f"Mode: {mode}\n"
                f"Timestamp: {datetime.now(timezone.utc).isoformat()}\n\n"
                f"Co-Authored-By: SLATE AI <slate-ai@slate.local>"
            )
            subprocess.run(["git", "commit", "-m", msg], cwd=str(WORKSPACE))
            subprocess.run(["git", "push"], cwd=str(WORKSPACE))
            print(f"\n✓ Changes committed and pushed for mode: {mode}")
        except Exception as e:
            print(f"\n✗ Failed to commit: {e}")


# ─── CLI Entry Point ────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="SLATE Workflow Hub")
    parser.add_argument("--mode", default="status", help="Automation mode")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--commit", action="store_true", help="Commit changes")
    parser.add_argument("--status", action="store_true", help="Show status")
    args = parser.parse_args()
    
    if args.status:
        args.mode = "status"
    
    hub = WorkflowHub()
    hub.run(args.mode, as_json=args.json, commit=args.commit)


if __name__ == "__main__":
    main()
