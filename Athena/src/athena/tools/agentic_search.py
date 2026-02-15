"""
athena.tools.agentic_search
============================

Agentic RAG v2 — Multi-step query decomposition → parallel search → validation.

Pipeline:
    1. Planner:    Decompose complex query into 2-4 sub-queries (rule-based NLP)
    2. Retriever:  Run each sub-query through existing run_search() in parallel
    3. Validator:  Deduplicate, cosine-validate against original query
    4. Synthesizer: Merge ranked results with provenance

Design decisions:
    - No LLM for decomposition (fast, free, deterministic)
    - Reuses existing run_search() — no new search infrastructure
    - Validation uses cosine similarity from existing get_embedding()
"""

import json
import re
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Tuple

from athena.core.models import SearchResult
from athena.memory.vectors import get_embedding

# ── Decomposition Config ─────────────────────────────────────────────────────

# Conjunctions and clause separators that signal multi-part queries
SPLIT_PATTERNS = [
    r"\band\b",  # "trading risk and psychology"
    r"\bor\b",  # "protocol 49 or protocol 75"
    r"\bvs\.?\b",  # "GraphRAG vs VectorRAG"
    r"\bversus\b",
    r"\bcompared?\s+to\b",
    r"\bas\s+well\s+as\b",
    r",\s+(?:and\s+)?",  # Comma-separated lists
]

# Question decomposition patterns
QUESTION_PATTERNS = [
    (
        r"(what|how|which|where|when|why)\s+(.+?)\s+and\s+(what|how|which|where|when|why)\s+(.+)",
        "multi_question",
    ),  # "What is X and how does Y work?"
    (r"(.+?)\s+(?:and|then|also)\s+(.+)", "sequential"),  # "Find X and then do Y"
]

# Stopwords for keyword extraction
STOPWORDS = {
    "the",
    "a",
    "an",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "could",
    "should",
    "may",
    "might",
    "shall",
    "can",
    "need",
    "dare",
    "ought",
    "in",
    "on",
    "at",
    "to",
    "for",
    "of",
    "with",
    "by",
    "from",
    "about",
    "into",
    "through",
    "during",
    "before",
    "after",
    "above",
    "below",
    "between",
    "out",
    "off",
    "over",
    "under",
    "again",
    "further",
    "then",
    "that",
    "this",
    "these",
    "those",
    "i",
    "me",
    "my",
    "we",
    "our",
    "it",
    "its",
    "what",
    "which",
    "who",
    "whom",
    "when",
    "where",
    "why",
    "how",
    "all",
    "each",
    "every",
    "both",
    "few",
    "more",
    "most",
    "other",
    "some",
    "such",
    "no",
    "nor",
    "not",
    "only",
    "own",
    "same",
    "so",
    "than",
    "too",
    "very",
    "just",
    "because",
    "if",
    "but",
    "or",
    "and",
    "show",
    "find",
    "get",
    "give",
    "tell",
    "list",
    "search",
}

# Minimum sub-query length (tokens) to be viable
MIN_SUBQUERY_TOKENS = 2
MAX_SUBQUERIES = 4
VALIDATION_THRESHOLD = 0.25  # Cosine similarity floor for result validation


# ── Decomposition Engine ─────────────────────────────────────────────────────


def decompose_query(query: str) -> List[str]:
    """
    Decompose a complex query into 2-4 sub-queries using rule-based NLP.

    Strategy:
        1. Check for multi-question patterns (What X and how Y?)
        2. Check for conjunction/comma splits
        3. If no splits found, extract keyword clusters as sub-queries
        4. Always include the original query as a sub-query (ensures recall)

    Returns:
        List of sub-query strings (always includes original)
    """
    query = query.strip()
    sub_queries = []

    # Strategy 1: Multi-question detection
    for pattern, ptype in QUESTION_PATTERNS:
        match = re.match(pattern, query, re.IGNORECASE)
        if match:
            groups = match.groups()
            if ptype == "multi_question":
                q1 = f"{groups[0]} {groups[1]}".strip()
                q2 = f"{groups[2]} {groups[3]}".strip()
                sub_queries = [q1, q2]
            elif ptype == "sequential":
                sub_queries = [groups[0].strip(), groups[1].strip()]
            break

    # Strategy 2: Conjunction/comma splitting
    if not sub_queries:
        for pattern in SPLIT_PATTERNS:
            parts = re.split(pattern, query, flags=re.IGNORECASE)
            parts = [p.strip() for p in parts if p and len(p.split()) >= MIN_SUBQUERY_TOKENS]
            if len(parts) >= 2:
                sub_queries = parts[:MAX_SUBQUERIES]
                break

    # Strategy 3: Keyword cluster extraction (fallback for single dense queries)
    if not sub_queries:
        tokens = [w for w in query.split() if w.lower() not in STOPWORDS and len(w) > 2]
        if len(tokens) >= 4:
            # Split tokens into 2 clusters
            mid = len(tokens) // 2
            sub_queries = [
                " ".join(tokens[:mid]),
                " ".join(tokens[mid:]),
            ]

    # Always include the full original query for recall
    if query not in sub_queries:
        sub_queries.insert(0, query)

    # If we only have the original query, return just it (simple query, no decomposition needed)
    if len(sub_queries) == 1:
        return sub_queries

    # Cap at MAX_SUBQUERIES
    return sub_queries[:MAX_SUBQUERIES]


# ── Cosine Similarity ────────────────────────────────────────────────────────


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = sum(a * a for a in vec_a) ** 0.5
    norm_b = sum(b * b for b in vec_b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# ── Retriever (Parallel Search) ──────────────────────────────────────────────


def _run_subquery_search(subquery: str, limit: int = 10) -> Tuple[str, List[Dict]]:
    """Run a single search sub-query and return JSON results."""
    # Import here to avoid circular imports at module level
    from athena.tools.search import (
        collect_canonical,
        collect_tags,
        collect_vectors,
        collect_graphrag,
        collect_filenames,
        collect_sqlite,
        weighted_rrf,
    )
    from athena.memory.vectors import get_embedding as _get_embedding

    try:
        query_embedding = _get_embedding(subquery)

        # Run collectors (parallel within each sub-query)
        collection_tasks = {
            "canonical": lambda: collect_canonical(subquery),
            "tags": lambda: collect_tags(subquery),
            "graphrag": lambda: collect_graphrag(subquery),
            "vector": lambda: collect_vectors(subquery, embedding=query_embedding),
            "sqlite": lambda: collect_sqlite(subquery),
            "filename": lambda: collect_filenames(subquery),
        }

        lists = {}
        with ThreadPoolExecutor(max_workers=len(collection_tasks)) as executor:
            future_to_source = {
                executor.submit(func): source for source, func in collection_tasks.items()
            }
            for future in as_completed(future_to_source, timeout=8):
                source = future_to_source[future]
                try:
                    lists[source] = future.result()
                except Exception:
                    lists[source] = []

        # Split vector results by type
        vector_items = lists.pop("vector", [])
        for item in vector_items:
            type_key = item.source
            if type_key not in lists:
                lists[type_key] = []
            lists[type_key].append(item)

        # Fuse
        fused = weighted_rrf(lists)
        return subquery, fused[:limit]

    except Exception as e:
        print(f"   ⚠️ Sub-query failed: '{subquery}': {e}", file=sys.stderr)
        return subquery, []


# ── Validator ─────────────────────────────────────────────────────────────────


def validate_results(
    results: List[SearchResult],
    query_embedding: List[float],
    threshold: float = VALIDATION_THRESHOLD,
) -> List[SearchResult]:
    """
    Validate results against the original query using cosine similarity.
    Filters out results below the threshold.
    """
    validated = []
    for result in results:
        try:
            # Use the result's content for validation
            result_embedding = get_embedding(result.content[:500])
            sim = cosine_similarity(query_embedding, result_embedding)
            if sim >= threshold:
                result.metadata["validation_score"] = round(sim, 4)
                validated.append(result)
        except Exception:
            # If embedding fails, keep the result (fail-open)
            result.metadata["validation_score"] = -1
            validated.append(result)

    return validated


# ── Main Pipeline ─────────────────────────────────────────────────────────────


def agentic_search(
    query: str,
    limit: int = 10,
    validate: bool = True,
    debug: bool = False,
) -> Dict[str, Any]:
    """
    Agentic RAG v2 — Full pipeline.

    Args:
        query: The complex search query
        limit: Maximum results to return
        validate: Whether to run cosine validation
        debug: Show debug information

    Returns:
        dict with 'results', 'sub_queries', 'meta'
    """
    # Phase 1: Decompose
    sub_queries = decompose_query(query)
    was_decomposed = len(sub_queries) > 1

    if debug:
        print(f"🧩 Decomposition: {len(sub_queries)} sub-queries", file=sys.stderr)
        for i, sq in enumerate(sub_queries, 1):
            print(f"   {i}. '{sq}'", file=sys.stderr)

    # Phase 2: Parallel Retrieval
    all_results: Dict[str, SearchResult] = {}  # Dedup by doc ID
    provenance: Dict[str, List[str]] = defaultdict(list)  # doc_id -> [sub_queries that found it]

    # Run sub-queries in parallel
    with ThreadPoolExecutor(max_workers=min(len(sub_queries), 4)) as executor:
        future_to_sq = {executor.submit(_run_subquery_search, sq, limit): sq for sq in sub_queries}
        for future in as_completed(future_to_sq, timeout=30):
            sq = future_to_sq[future]
            try:
                _, results = future.result()
                for result in results:
                    if result.id not in all_results:
                        all_results[result.id] = result
                    else:
                        # Boost score for results found by multiple sub-queries
                        existing = all_results[result.id]
                        existing.rrf_score = max(existing.rrf_score, result.rrf_score) * 1.1
                    provenance[result.id].append(sq)
            except Exception as e:
                print(f"   ⚠️ Sub-query execution failed: {e}", file=sys.stderr)

    # Sort by fused score
    merged = sorted(all_results.values(), key=lambda x: x.rrf_score, reverse=True)

    # Phase 3: Validate (optional)
    if validate and merged:
        try:
            query_embedding = get_embedding(query)
            merged = validate_results(merged, query_embedding)
        except Exception as e:
            if debug:
                print(f"   ⚠️ Validation skipped: {e}", file=sys.stderr)

    # Phase 4: Final ranking
    final = merged[:limit]

    # Add provenance to metadata
    for result in final:
        result.metadata["found_by"] = provenance.get(result.id, [])
        result.metadata["multi_source"] = len(provenance.get(result.id, [])) > 1

    return {
        "results": final,
        "sub_queries": sub_queries,
        "decomposed": was_decomposed,
        "meta": {
            "total_candidates": len(all_results),
            "returned": len(final),
            "sub_query_count": len(sub_queries),
        },
    }


# ── CLI Output ────────────────────────────────────────────────────────────────


def run_agentic_search(
    query: str,
    limit: int = 10,
    validate: bool = True,
    debug: bool = False,
    json_output: bool = False,
):
    """CLI-friendly wrapper for agentic_search."""
    result = agentic_search(query, limit=limit, validate=validate, debug=debug)

    if json_output:
        output = {
            "results": [r.to_dict() for r in result["results"]],
            "sub_queries": result["sub_queries"],
            "decomposed": result["decomposed"],
            "meta": result["meta"],
        }
        print(json.dumps(output, indent=2))
        return

    # Human-readable output
    sq_count = len(result["sub_queries"])
    total = result["meta"]["total_candidates"]

    print(f'\n🧠 AGENTIC SEARCH: "{query}"')
    print("=" * 60)

    if result["decomposed"]:
        print(f"   🧩 Decomposed into {sq_count} sub-queries:")
        for i, sq in enumerate(result["sub_queries"], 1):
            print(f'      {i}. "{sq}"')
    else:
        print("   📎 Single-query mode (no decomposition needed)")

    print(f"   📊 {total} unique candidates found → returning top {len(result['results'])}")

    if result["results"]:
        print("\n<athena_grounding>")
        print(f"\n🏆 TOP {limit} RESULTS:")
        for i, doc in enumerate(result["results"], 1):
            multi = "🔗" if doc.metadata.get("multi_source") else "  "
            vscore = doc.metadata.get("validation_score", "—")
            if isinstance(vscore, float):
                vscore = f"{vscore:.2f}"

            print(f"\n  {multi} {i}. [RRF:{doc.rrf_score:.4f} V:{vscore}] {doc.id}")

            if doc.metadata.get("path"):
                print(f"        📁 {doc.metadata['path']}")
            else:
                print(f"        📄 {doc.content[:100]}...")

            if debug and doc.metadata.get("found_by"):
                print(f"        🧩 Found by: {doc.metadata['found_by']}")

        print("-" * 60)
        print("</athena_grounding>\n")
    else:
        print("\n  (No results found)")
