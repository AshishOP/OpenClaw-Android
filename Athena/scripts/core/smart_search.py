#!/usr/bin/env python3
"""
smart_search.py — Semantic Search (Public Example)
===================================================
Demonstrates hybrid semantic search over local markdown files.
Uses sentence-transformers for embeddings (optional dependency).

Usage:
    python3 scripts/core/smart_search.py "limerence protocol"
    python3 scripts/core/smart_search.py "trading strategy" --limit 5

Dependencies:
    pip install sentence-transformers

If sentence-transformers is not installed, falls back to simple keyword search.
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

# Project structure
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# Directories to search
SEARCHABLE_DIRS = [
    PROJECT_ROOT / "examples" / "protocols",
    PROJECT_ROOT / "docs" / "protocols",
    PROJECT_ROOT / "session_logs",
]


def keyword_search(query: str, limit: int = 10) -> list[dict]:
    """
    Simple keyword-based search fallback.
    Returns files containing any query terms.
    """
    terms = query.lower().split()
    results = []

    for search_dir in SEARCHABLE_DIRS:
        if not search_dir.exists():
            continue
        for md_file in search_dir.rglob("*.md"):
            try:
                content = md_file.read_text(errors="ignore").lower()
                score = sum(1 for term in terms if term in content)
                if score > 0:
                    results.append(
                        {
                            "path": str(md_file.relative_to(PROJECT_ROOT)),
                            "score": score,
                            "method": "keyword",
                        }
                    )
            except Exception:
                continue

    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]


def semantic_search(query: str, limit: int = 10) -> list[dict]:
    """
    Semantic search using sentence-transformers.
    Falls back to keyword search if library is unavailable.
    """
    try:
        from sentence_transformers import SentenceTransformer, util
        import torch
    except ImportError:
        print("⚠️  sentence-transformers not installed. Falling back to keyword search.")
        print("   Install: pip install sentence-transformers\n")
        return keyword_search(query, limit)

    # Load a lightweight model
    model = SentenceTransformer("all-MiniLM-L6-v2")
    query_embedding = model.encode(query, convert_to_tensor=True)

    documents = []
    for search_dir in SEARCHABLE_DIRS:
        if not search_dir.exists():
            continue
        for md_file in search_dir.rglob("*.md"):
            try:
                content = md_file.read_text(errors="ignore")
                # Extract first 500 chars as document "preview"
                preview = content[:500].replace("\n", " ").strip()
                documents.append(
                    {
                        "path": str(md_file.relative_to(PROJECT_ROOT)),
                        "content": preview,
                        "full_path": md_file,
                    }
                )
            except Exception:
                continue

    if not documents:
        print("No documents found to search.")
        return []

    # Encode document previews
    doc_texts = [d["content"] for d in documents]
    doc_embeddings = model.encode(doc_texts, convert_to_tensor=True)

    # Compute cosine similarity
    cos_scores = util.cos_sim(query_embedding, doc_embeddings)[0]

    # Build results with scores
    results = []
    for idx, score in enumerate(cos_scores):
        results.append(
            {
                "path": documents[idx]["path"],
                "score": float(score),
                "method": "semantic",
            }
        )

    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]


def main():
    parser = argparse.ArgumentParser(
        description="Athena Smart Search — Semantic or keyword search over local files"
    )
    parser.add_argument("query", help="Search query")
    parser.add_argument("--limit", type=int, default=10, help="Max results (default: 10)")
    parser.add_argument("--keyword", action="store_true", help="Force keyword-only search (no ML)")
    args = parser.parse_args()

    print(f'🔍 Searching: "{args.query}"\n')

    if args.keyword:
        results = keyword_search(args.query, args.limit)
    else:
        results = semantic_search(args.query, args.limit)

    if not results:
        print("No results found.")
        return

    print(f"Found {len(results)} result(s):\n")
    for i, r in enumerate(results, 1):
        method_icon = "🧠" if r["method"] == "semantic" else "🔤"
        print(f"  {i}. {method_icon} [{r['score']:.3f}] {r['path']}")
    print()


if __name__ == "__main__":
    main()
