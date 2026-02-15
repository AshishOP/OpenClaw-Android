#!/usr/bin/env python3
"""
query_graphrag.py
=================
Simple query interface for the JSON-based Knowledge Graph.
"""

import sys
import json
import argparse
from pathlib import Path

# Constants matching the restored structure
AGENT_DIR = Path(__file__).parent.parent
GRAPH_FILE = AGENT_DIR / "graphrag" / "knowledge_graph.json"


def load_graph():
    if not GRAPH_FILE.exists():
        print(f"Error: Graph file not found at {GRAPH_FILE}")
        sys.exit(1)
    try:
        return json.loads(GRAPH_FILE.read_text())
    except Exception as e:
        print(f"Error reading graph file: {e}")
        sys.exit(1)


def search_nodes(graph, query, limit=5):
    """Search for nodes matching the query in name or description."""
    results = []
    query_lower = query.lower()

    for entity in graph.get("entities", []):
        name = entity.get("name", "")
        desc = entity.get("description", "")

        score = 0
        if query_lower in name.lower():
            score += 2
        if query_lower in desc.lower():
            score += 1

        if score > 0:
            results.append({"type": "entity", "name": name, "description": desc, "score": score})

    return sorted(results, key=lambda x: x["score"], reverse=True)[:limit]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query the Knowledge Graph")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--json", action="store_true", help="Output JSON (default)")
    parser.add_argument("--global-only", action="store_true", help="Ignored")
    parser.add_argument("--community", help="Ignored")
    args = parser.parse_args()

    graph = load_graph()
    results = search_nodes(graph, args.query)

    if results:
        print(json.dumps(results, indent=2))
    else:
        print("[]")
