#!/usr/bin/env python3
"""
SLATE GraphRAG Knowledge System
================================

Provides graph-based retrieval-augmented generation (RAG) that augments
ChromaDB vector search with structured knowledge graph relationships.

Architecture:
  ChromaDB (vector search) + Knowledge Graph (structured relationships)
  = GraphRAG (hybrid retrieval with entity-relationship context)

The knowledge graph captures:
- Module dependencies (imports, calls)
- Spec relationships (implements, depends-on)
- Service connections (data flow, health dependencies)
- Tech tree structure (phases, prerequisites)
- Brand token distribution (source, targets)

This is inspired by Microsoft GraphRAG but implemented locally using
a lightweight in-memory graph with JSON persistence — no external
dependencies beyond what SLATE already uses.
"""
# Modified: 2026-02-09T19:00:00Z | Author: Claude Opus 4.6 | Change: Create GraphRAG knowledge system

import json
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

WORKSPACE_ROOT = Path(__file__).parent.parent
GRAPH_DIR = WORKSPACE_ROOT / ".slate_index" / "graphrag"
GRAPH_FILE = GRAPH_DIR / "knowledge_graph.json"
ENTITIES_FILE = GRAPH_DIR / "entities.json"
RELATIONS_FILE = GRAPH_DIR / "relations.json"


# ── Data Classes ───────────────────────────────────────────────────────

@dataclass
class Entity:
    """A node in the knowledge graph."""
    id: str
    name: str
    entity_type: str  # module, spec, service, tech_node, token, file
    description: str = ""
    properties: dict = field(default_factory=dict)
    source_file: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.entity_type,
            "description": self.description,
            "properties": self.properties,
            "source_file": self.source_file,
        }


@dataclass
class Relation:
    """An edge in the knowledge graph."""
    source_id: str
    target_id: str
    relation_type: str  # imports, implements, depends_on, connects_to, distributes_to
    weight: float = 1.0
    properties: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "source": self.source_id,
            "target": self.target_id,
            "type": self.relation_type,
            "weight": self.weight,
            "properties": self.properties,
        }


@dataclass
class GraphQuery:
    """Result of a graph traversal query."""
    query: str
    entities: list
    relations: list
    context: str = ""
    depth: int = 0
    duration_ms: float = 0


# ── Knowledge Graph Engine ─────────────────────────────────────────────

class KnowledgeGraph:
    """In-memory knowledge graph with JSON persistence."""

    def __init__(self):
        self.entities: dict[str, Entity] = {}
        self.relations: list[Relation] = []
        self._adjacency: dict[str, list[tuple[str, Relation]]] = defaultdict(list)
        self._reverse: dict[str, list[tuple[str, Relation]]] = defaultdict(list)
        self._load()

    def _load(self):
        """Load graph from disk."""
        if GRAPH_FILE.exists():
            try:
                data = json.loads(GRAPH_FILE.read_text(encoding="utf-8"))
                for e in data.get("entities", []):
                    entity = Entity(
                        id=e["id"], name=e["name"], entity_type=e["type"],
                        description=e.get("description", ""),
                        properties=e.get("properties", {}),
                        source_file=e.get("source_file", ""),
                    )
                    self.entities[entity.id] = entity

                for r in data.get("relations", []):
                    rel = Relation(
                        source_id=r["source"], target_id=r["target"],
                        relation_type=r["type"],
                        weight=r.get("weight", 1.0),
                        properties=r.get("properties", {}),
                    )
                    self.relations.append(rel)
                    self._adjacency[rel.source_id].append((rel.target_id, rel))
                    self._reverse[rel.target_id].append((rel.source_id, rel))
            except Exception:
                pass

    def save(self):
        """Persist graph to disk."""
        GRAPH_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "version": "1.0.0",
            "updated": datetime.now(timezone.utc).isoformat(),
            "entity_count": len(self.entities),
            "relation_count": len(self.relations),
            "entities": [e.to_dict() for e in self.entities.values()],
            "relations": [r.to_dict() for r in self.relations],
        }
        GRAPH_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def add_entity(self, entity: Entity) -> bool:
        """Add or update an entity."""
        is_new = entity.id not in self.entities
        self.entities[entity.id] = entity
        return is_new

    def add_relation(self, relation: Relation) -> bool:
        """Add a relation (deduplicates by source+target+type)."""
        for existing in self.relations:
            if (existing.source_id == relation.source_id and
                    existing.target_id == relation.target_id and
                    existing.relation_type == relation.relation_type):
                existing.weight = relation.weight
                existing.properties.update(relation.properties)
                return False

        self.relations.append(relation)
        self._adjacency[relation.source_id].append((relation.target_id, relation))
        self._reverse[relation.target_id].append((relation.source_id, relation))
        return True

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID."""
        return self.entities.get(entity_id)

    def get_neighbors(self, entity_id: str, direction: str = "both") -> list[tuple[Entity, Relation]]:
        """Get neighboring entities and their relations."""
        results = []
        if direction in ("outgoing", "both"):
            for target_id, rel in self._adjacency.get(entity_id, []):
                if target_id in self.entities:
                    results.append((self.entities[target_id], rel))
        if direction in ("incoming", "both"):
            for source_id, rel in self._reverse.get(entity_id, []):
                if source_id in self.entities:
                    results.append((self.entities[source_id], rel))
        return results

    def traverse(self, start_id: str, max_depth: int = 2) -> GraphQuery:
        """BFS traversal from a starting entity."""
        start = time.time()
        visited_entities = {}
        visited_relations = []
        queue = [(start_id, 0)]
        seen = {start_id}

        while queue:
            current_id, depth = queue.pop(0)
            if depth > max_depth:
                continue

            entity = self.entities.get(current_id)
            if entity:
                visited_entities[current_id] = entity

            for neighbor, rel in self.get_neighbors(current_id, "both"):
                visited_relations.append(rel)
                if neighbor.id not in seen:
                    seen.add(neighbor.id)
                    queue.append((neighbor.id, depth + 1))

        # Build context string
        context_parts = []
        for e in visited_entities.values():
            context_parts.append(f"[{e.entity_type}] {e.name}: {e.description}")
        for r in visited_relations:
            src = visited_entities.get(r.source_id)
            tgt = visited_entities.get(r.target_id)
            if src and tgt:
                context_parts.append(f"  {src.name} --{r.relation_type}--> {tgt.name}")

        duration = (time.time() - start) * 1000
        return GraphQuery(
            query=f"traverse({start_id}, depth={max_depth})",
            entities=list(visited_entities.values()),
            relations=visited_relations,
            context="\n".join(context_parts),
            depth=max_depth,
            duration_ms=round(duration, 2),
        )

    def search_entities(self, query: str, entity_type: str = "") -> list[Entity]:
        """Search entities by name/description substring match."""
        query_lower = query.lower()
        results = []
        for e in self.entities.values():
            if entity_type and e.entity_type != entity_type:
                continue
            if query_lower in e.name.lower() or query_lower in e.description.lower():
                results.append(e)
        return results

    def get_stats(self) -> dict:
        """Get graph statistics."""
        type_counts = defaultdict(int)
        for e in self.entities.values():
            type_counts[e.entity_type] += 1

        rel_counts = defaultdict(int)
        for r in self.relations:
            rel_counts[r.relation_type] += 1

        return {
            "total_entities": len(self.entities),
            "total_relations": len(self.relations),
            "entity_types": dict(type_counts),
            "relation_types": dict(rel_counts),
        }


# ── Graph Builder ──────────────────────────────────────────────────────

class GraphBuilder:
    """Builds the knowledge graph from SLATE project structure."""

    def __init__(self, graph: KnowledgeGraph):
        self.graph = graph

    def build_all(self) -> dict:
        """Build the complete knowledge graph."""
        counts = {
            "modules": self._build_modules(),
            "specs": self._build_specs(),
            "services": self._build_services(),
            "tech_tree": self._build_tech_tree(),
            "imports": self._build_import_relations(),
        }
        self.graph.save()
        return counts

    def _build_modules(self) -> int:
        """Index Python modules as entities."""
        count = 0
        slate_dir = WORKSPACE_ROOT / "slate"
        if not slate_dir.exists():
            return 0

        for py_file in sorted(slate_dir.glob("*.py")):
            if py_file.name.startswith("__"):
                continue
            module_name = py_file.stem
            entity_id = f"mod:{module_name}"

            # Read first docstring for description
            desc = ""
            try:
                content = py_file.read_text(encoding="utf-8")
                if '"""' in content:
                    start = content.index('"""') + 3
                    end = content.index('"""', start)
                    doc = content[start:end].strip()
                    # First line of docstring
                    desc = doc.split("\n")[0][:200]
            except Exception:
                pass

            entity = Entity(
                id=entity_id,
                name=module_name,
                entity_type="module",
                description=desc,
                properties={"size_bytes": py_file.stat().st_size},
                source_file=str(py_file.relative_to(WORKSPACE_ROOT)),
            )
            if self.graph.add_entity(entity):
                count += 1

        return count

    def _build_specs(self) -> int:
        """Index specifications as entities."""
        count = 0
        specs_dir = WORKSPACE_ROOT / "specs"
        if not specs_dir.exists():
            return 0

        for spec_dir in sorted(specs_dir.iterdir()):
            if not spec_dir.is_dir():
                continue
            spec_md = spec_dir / "spec.md"
            if not spec_md.exists():
                continue

            # Extract spec number and name from directory name
            parts = spec_dir.name.split("-", 1)
            spec_num = parts[0] if parts else "000"
            spec_name = parts[1].replace("-", " ").title() if len(parts) > 1 else spec_dir.name

            # Read title from spec.md
            desc = ""
            try:
                content = spec_md.read_text(encoding="utf-8")
                for line in content.split("\n"):
                    if line.startswith("# "):
                        desc = line[2:].strip()
                        break
            except Exception:
                pass

            entity = Entity(
                id=f"spec:{spec_num}",
                name=f"Spec {spec_num}: {spec_name}",
                entity_type="spec",
                description=desc,
                properties={"number": spec_num, "directory": spec_dir.name},
                source_file=str(spec_md.relative_to(WORKSPACE_ROOT)),
            )
            if self.graph.add_entity(entity):
                count += 1

        return count

    def _build_services(self) -> int:
        """Index SLATE services as entities."""
        services = [
            ("svc:dashboard", "Dashboard", "FastAPI dashboard server on port 8080", 8080),
            ("svc:ollama", "Ollama", "Local LLM inference service on port 11434", 11434),
            ("svc:chromadb", "ChromaDB", "Vector store for RAG memory on port 8000", 8000),
            ("svc:foundry", "Foundry Local", "ONNX-optimized inference on port 5272", 5272),
            ("svc:runner", "GitHub Runner", "Self-hosted GitHub Actions runner", 0),
            ("svc:mcp", "MCP Server", "Model Context Protocol integration", 0),
            ("svc:agent-router", "Agent Router", "Task routing service on port 8081", 8081),
            ("svc:autonomous", "Autonomous Loop", "Self-healing autonomous system on port 8082", 8082),
            ("svc:trellis2", "TRELLIS.2", "Image-to-3D generation on port 8086", 8086),
        ]
        count = 0
        for eid, name, desc, port in services:
            entity = Entity(
                id=eid, name=name, entity_type="service",
                description=desc,
                properties={"port": port},
            )
            if self.graph.add_entity(entity):
                count += 1

            # Service-to-service connections
            if eid == "svc:dashboard":
                self.graph.add_relation(Relation(eid, "svc:ollama", "connects_to", weight=0.9))
                self.graph.add_relation(Relation(eid, "svc:chromadb", "connects_to", weight=0.7))
            elif eid == "svc:agent-router":
                self.graph.add_relation(Relation(eid, "svc:ollama", "connects_to", weight=1.0))
                self.graph.add_relation(Relation(eid, "svc:foundry", "connects_to", weight=0.5))
            elif eid == "svc:autonomous":
                self.graph.add_relation(Relation(eid, "svc:ollama", "connects_to", weight=1.0))
                self.graph.add_relation(Relation(eid, "svc:runner", "connects_to", weight=0.8))

        return count

    def _build_tech_tree(self) -> int:
        """Index tech tree nodes as entities with dependency relations."""
        count = 0
        tech_file = WORKSPACE_ROOT / ".slate_tech_tree" / "tech_tree.json"
        if not tech_file.exists():
            return 0

        try:
            data = json.loads(tech_file.read_text(encoding="utf-8"))
        except Exception:
            return 0

        for node in data.get("nodes", []):
            entity = Entity(
                id=f"tech:{node['id']}",
                name=node.get("name", node["id"]),
                entity_type="tech_node",
                description=node.get("description", ""),
                properties={
                    "status": node.get("status", "unknown"),
                    "phase": node.get("phase", 0),
                },
            )
            if self.graph.add_entity(entity):
                count += 1

        # Build dependency relations from edges
        for edge in data.get("edges", []):
            src = f"tech:{edge.get('from', edge.get('source', ''))}"
            tgt = f"tech:{edge.get('to', edge.get('target', ''))}"
            if src and tgt:
                self.graph.add_relation(Relation(src, tgt, "depends_on"))

        return count

    def _build_import_relations(self) -> int:
        """Analyze Python imports to build module dependency relations."""
        count = 0
        slate_dir = WORKSPACE_ROOT / "slate"
        if not slate_dir.exists():
            return 0

        for py_file in sorted(slate_dir.glob("*.py")):
            if py_file.name.startswith("__"):
                continue
            module_name = py_file.stem
            source_id = f"mod:{module_name}"

            try:
                content = py_file.read_text(encoding="utf-8")
            except Exception:
                continue

            # Find imports of other slate modules
            import_lines = [line.strip() for line in content.split("\n")
                            if "from slate." in line or "import slate." in line]

            for line in import_lines:
                # Extract module name from "from slate.foo import ..." or "import slate.foo"
                if "from slate." in line:
                    parts = line.split("from slate.")[1].split(" import")[0].split(".")
                    imported = parts[0]
                elif "import slate." in line:
                    parts = line.split("import slate.")[1].split(".")
                    imported = parts[0]
                else:
                    continue

                target_id = f"mod:{imported}"
                if target_id in self.graph.entities and source_id != target_id:
                    if self.graph.add_relation(Relation(source_id, target_id, "imports")):
                        count += 1

        return count


# ── GraphRAG Query Engine ──────────────────────────────────────────────

class GraphRAG:
    """Combines vector search (ChromaDB) with graph traversal."""

    def __init__(self):
        self.graph = KnowledgeGraph()
        self.builder = GraphBuilder(self.graph)

    def build_index(self) -> dict:
        """Build/rebuild the knowledge graph from project sources."""
        return self.builder.build_all()

    def query(self, question: str, max_depth: int = 2) -> GraphQuery:
        """Query the graph with a natural language question.

        Finds relevant entities and traverses their neighborhoods
        to provide structured context for RAG augmentation.
        """
        start = time.time()

        # Find matching entities
        matches = self.graph.search_entities(question)

        if not matches:
            # Try individual words
            words = question.lower().split()
            for word in words:
                if len(word) > 3:
                    matches.extend(self.graph.search_entities(word))

        if not matches:
            return GraphQuery(
                query=question,
                entities=[],
                relations=[],
                context="No matching entities found in knowledge graph.",
                duration_ms=round((time.time() - start) * 1000, 2),
            )

        # Traverse from best match
        best = matches[0]
        result = self.graph.traverse(best.id, max_depth)
        result.query = question
        result.duration_ms = round((time.time() - start) * 1000, 2)
        return result

    def get_module_context(self, module_name: str) -> str:
        """Get structured context about a module for RAG augmentation."""
        entity_id = f"mod:{module_name}"
        result = self.graph.traverse(entity_id, max_depth=1)

        if not result.entities:
            return f"No graph context found for module '{module_name}'"

        return result.context

    def get_status(self) -> dict:
        """Get GraphRAG system status."""
        stats = self.graph.get_stats()
        stats["graph_file"] = str(GRAPH_FILE)
        stats["graph_exists"] = GRAPH_FILE.exists()
        if GRAPH_FILE.exists():
            stats["graph_size_bytes"] = GRAPH_FILE.stat().st_size
        return stats

    def print_status(self):
        """Print GraphRAG status to CLI."""
        stats = self.get_status()
        print()
        print("============================================================")
        print("  SLATE GraphRAG Knowledge System")
        print("============================================================")
        print()
        print(f"  Graph File: {'exists' if stats['graph_exists'] else 'not built'}")
        if stats.get("graph_size_bytes"):
            print(f"  Graph Size: {stats['graph_size_bytes']:,} bytes")
        print(f"  Entities:   {stats['total_entities']}")
        print(f"  Relations:  {stats['total_relations']}")
        print()

        if stats.get("entity_types"):
            print("  Entity Types:")
            for etype, count in sorted(stats["entity_types"].items()):
                print(f"    {etype:15s}: {count}")
            print()

        if stats.get("relation_types"):
            print("  Relation Types:")
            for rtype, count in sorted(stats["relation_types"].items()):
                print(f"    {rtype:15s}: {count}")
            print()

        print("============================================================")
        print()


# ── Module-Level Helpers ───────────────────────────────────────────────

_graphrag: Optional[GraphRAG] = None


def get_graphrag() -> GraphRAG:
    """Get or create the GraphRAG singleton."""
    global _graphrag
    if _graphrag is None:
        _graphrag = GraphRAG()
    return _graphrag


# ── CLI ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="SLATE GraphRAG Knowledge System")
    parser.add_argument("--status", action="store_true", help="Show GraphRAG status")
    parser.add_argument("--build", action="store_true", help="Build/rebuild knowledge graph")
    parser.add_argument("--query", type=str, help="Query the knowledge graph")
    parser.add_argument("--module", type=str, help="Get context for a module")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--depth", type=int, default=2, help="Traversal depth (default: 2)")

    args = parser.parse_args()
    rag = get_graphrag()

    if args.build:
        print("Building knowledge graph...")
        counts = rag.build_index()
        print(f"  Modules:     {counts.get('modules', 0)}")
        print(f"  Specs:       {counts.get('specs', 0)}")
        print(f"  Services:    {counts.get('services', 0)}")
        print(f"  Tech nodes:  {counts.get('tech_tree', 0)}")
        print(f"  Imports:     {counts.get('imports', 0)}")
        stats = rag.get_status()
        print(f"\n  Total: {stats['total_entities']} entities, {stats['total_relations']} relations")

    elif args.query:
        result = rag.query(args.query, max_depth=args.depth)
        if args.json:
            print(json.dumps({
                "query": result.query,
                "entities": [e.to_dict() for e in result.entities],
                "relations": [r.to_dict() for r in result.relations],
                "context": result.context,
                "duration_ms": result.duration_ms,
            }, indent=2))
        else:
            print(f"\nQuery: {result.query}")
            print(f"Found: {len(result.entities)} entities, {len(result.relations)} relations")
            print(f"Time:  {result.duration_ms}ms")
            print(f"\nContext:\n{result.context}")

    elif args.module:
        context = rag.get_module_context(args.module)
        print(context)

    elif args.json:
        print(json.dumps(rag.get_status(), indent=2))

    else:
        rag.print_status()
