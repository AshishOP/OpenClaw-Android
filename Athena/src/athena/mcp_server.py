"""
athena.mcp_server
=================

MCP Tool Server for Project Athena.
Exposes core capabilities (search, quicksave, health, session) as
standardized MCP tools, consumable by any MCP-compatible client.

Transport: stdio (default), SSE (optional via --sse flag).

Usage:
    # stdio (for IDE integration like Antigravity / Claude Desktop)
    python -m athena.mcp_server

    # SSE (for remote / multi-client access)
    python -m athena.mcp_server --sse --port 8765
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime

from fastmcp import FastMCP

from athena.core.permissions import (
    get_permissions,
    PermissionDenied,
    SecretModeViolation,
    Permission,
    Sensitivity,
)

# ---------------------------------------------------------------------------
# Server Init
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="athena",
    version="1.1.0",
    instructions=(
        "Project Athena MCP Server — a sovereign personal intelligence "
        "infrastructure. Use these tools to search memory, save checkpoints, "
        "check system health, and manage sessions.\n\n"
        "All tools are gated by the Permissioning Layer. Use permission_status "
        "to see what's accessible. Use set_secret_mode to toggle demo mode."
    ),
)

logger = logging.getLogger("athena.mcp")

# ---------------------------------------------------------------------------
# TOOL: smart_search
# ---------------------------------------------------------------------------


@mcp.tool(
    tags={"read", "memory", "search"},
)
def smart_search(
    query: str,
    limit: int = 10,
    strict: bool = False,
    rerank: bool = False,
) -> dict:
    """
    Search Athena's knowledge base using hybrid RAG (Canonical + Tags +
    Vectors + GraphRAG + SQLite + Filenames) with RRF fusion.

    Args:
        query: The search query string.
        limit: Maximum number of results to return (default 10).
        strict: If True, filter out low-confidence results.
        rerank: If True, apply LLM-based reranking to top candidates.

    Returns:
        dict with 'results' (list of matches) and 'meta' (query info).
    """
    from athena.tools.search import run_search
    from athena.core.governance import get_governance

    # Permission gate
    perms = get_permissions()
    perms.gate("smart_search")

    # Governance: Mark search as performed
    get_governance().mark_search_performed(query)

    # Capture results via json_output mode
    import io

    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()

    try:
        run_search(
            query=query,
            limit=limit,
            strict=strict,
            rerank=rerank,
            json_output=True,
        )
        output = buffer.getvalue()
    finally:
        sys.stdout = old_stdout

    # Parse the JSON output
    try:
        results = json.loads(output)
    except json.JSONDecodeError:
        results = {"raw_output": output}

    return {
        "results": results if isinstance(results, list) else results,
        "meta": {
            "query": query,
            "limit": limit,
            "strict": strict,
            "rerank": rerank,
            "timestamp": datetime.now().isoformat(),
        },
    }


# ---------------------------------------------------------------------------
# TOOL: agentic_search (RAG v2)
# ---------------------------------------------------------------------------


@mcp.tool(
    tags={"read", "memory", "search", "admin"},
)
def agentic_search(
    query: str,
    limit: int = 10,
    validate: bool = True,
) -> dict:
    """
    Agentic RAG v2 — Multi-step query decomposition with parallel search
    and cosine validation. Use this for complex, multi-part queries.

    Pipeline: Decompose → Parallel Retrieve → Validate → Synthesize

    Args:
        query: Complex search query (e.g. "trading risk protocols and case studies").
        limit: Maximum number of results to return (default 10).
        validate: If True, validate results via cosine similarity against original query.

    Returns:
        dict with 'results', 'sub_queries', 'decomposed', and 'meta'.
    """
    from athena.tools.agentic_search import agentic_search as _agentic_search

    # Permission gate
    perms = get_permissions()
    perms.gate("agentic_search")

    result = _agentic_search(query=query, limit=limit, validate=validate)

    return {
        "results": [r.to_dict() for r in result["results"]],
        "sub_queries": result["sub_queries"],
        "decomposed": result["decomposed"],
        "meta": {
            **result["meta"],
            "timestamp": datetime.now().isoformat(),
        },
    }


# ---------------------------------------------------------------------------
# TOOL: quicksave
# ---------------------------------------------------------------------------


@mcp.tool(
    tags={"write", "session", "checkpoint"},
)
def quicksave(
    summary: str,
    bullets: list[str] | None = None,
) -> dict:
    """
    Save a checkpoint to the current session log. Appends a timestamped
    block with a summary and optional bullet points.

    Args:
        summary: Brief description of what was accomplished/decided.
        bullets: Optional list of specific items to record.

    Returns:
        dict with 'status', 'log_file', and 'timestamp'.
    """
    from athena.sessions import append_checkpoint
    from athena.core.governance import get_governance

    # Permission gate
    perms = get_permissions()
    perms.gate("quicksave")

    # Governance: Check Triple-Lock compliance
    gov = get_governance()
    semantic = gov._state.get("semantic_search_performed", False)
    web = gov._state.get("web_search_performed", False)

    violation = None
    if not (semantic and web):
        missing = []
        if not semantic:
            missing.append("Semantic Search")
        if not web:
            missing.append("Web Research")
        violation = f"TRIPLE-LOCK VIOLATION: Missing: {', '.join(missing)}"

    gov.verify_exchange_integrity()  # Reset state

    try:
        log_path = append_checkpoint(summary, bullets)
        return {
            "status": "ok",
            "log_file": str(log_path),
            "timestamp": datetime.now().isoformat(),
            "governance": violation or "COMPLIANT",
        }
    except FileNotFoundError as e:
        return {
            "status": "error",
            "error": str(e),
            "hint": "No active session. Run boot first.",
        }


# ---------------------------------------------------------------------------
# TOOL: health_check
# ---------------------------------------------------------------------------


@mcp.tool(
    tags={"read", "system", "health"},
)
def health_check() -> dict:
    """
    Run a health audit of Athena's core services (Vector API, Database).

    Returns:
        dict with check results for each subsystem.
    """
    from athena.core.health import HealthCheck

    # Permission gate
    get_permissions().gate("health_check")

    vector = HealthCheck.check_vector_api()
    db = HealthCheck.check_database()

    return {
        "vector_api": vector,
        "database": db,
        "overall": "PASS" if (vector["status"] == "PASS" and db["status"] == "PASS") else "FAIL",
        "timestamp": datetime.now().isoformat(),
    }


# ---------------------------------------------------------------------------
# TOOL: recall_session
# ---------------------------------------------------------------------------


@mcp.tool(
    tags={"read", "session", "memory"},
)
def recall_session(lines: int = 50) -> dict:
    """
    Retrieve the most recent session log content.

    Args:
        lines: Number of lines from the end of the log to return (default 50).

    Returns:
        dict with session file path and recent content.
    """
    from athena.sessions import recall_last_session

    # Permission gate
    perms = get_permissions()
    perms.gate("recall_session")

    log_path = recall_last_session()

    if not log_path or not log_path.exists():
        return {
            "status": "error",
            "error": "No active session log found.",
        }

    content = log_path.read_text(encoding="utf-8")
    content_lines = content.splitlines()

    # Return the last N lines
    tail = content_lines[-lines:] if len(content_lines) > lines else content_lines
    tail_text = "\n".join(tail)

    # Redact if in secret mode
    if perms.secret_mode:
        tail_text = perms.redact(tail_text)

    return {
        "status": "ok",
        "session_file": str(log_path),
        "session_id": log_path.stem,
        "total_lines": len(content_lines),
        "content": tail_text,
    }


# ---------------------------------------------------------------------------
# TOOL: governance_status
# ---------------------------------------------------------------------------


@mcp.tool(
    tags={"read", "system", "governance"},
)
def governance_status() -> dict:
    """
    Check the current Triple-Lock governance state. Shows whether semantic
    search and web search have been performed in the current exchange.

    Returns:
        dict with governance state and integrity score.
    """
    from athena.core.governance import get_governance

    # Permission gate
    get_permissions().gate("governance_status")

    gov = get_governance()
    state = gov._state.copy()

    return {
        "semantic_search_performed": state.get("semantic_search_performed", False),
        "web_search_performed": state.get("web_search_performed", False),
        "integrity_score": gov.get_integrity_score(),
        "compliant": state.get("semantic_search_performed", False)
        and state.get("web_search_performed", False),
        "timestamp": datetime.now().isoformat(),
    }


# ---------------------------------------------------------------------------
# TOOL: list_memory_paths
# ---------------------------------------------------------------------------


@mcp.tool(
    tags={"read", "system", "config"},
)
def list_memory_paths() -> dict:
    """
    List all active memory directories that Athena searches over.
    Useful for understanding what knowledge domains are indexed.

    Returns:
        dict with core and extended memory paths.
    """
    from athena.core.config import (
        CORE_DIRS,
        EXTENDED_DIRS,
        get_active_memory_paths,
    )

    # Permission gate
    get_permissions().gate("list_memory_paths")

    core = {k: str(v) for k, v in CORE_DIRS.items()}
    extended = [{"path": str(p), "maps_to": t} for p, t in EXTENDED_DIRS]
    active = [str(p) for p in get_active_memory_paths()]

    return {
        "core_directories": core,
        "extended_directories": extended,
        "active_count": len(active),
    }


# ---------------------------------------------------------------------------
# RESOURCE: session_log (current)
# ---------------------------------------------------------------------------


@mcp.resource(
    uri="athena://session/current",
    name="Current Session Log",
    description="The full content of the active session log file.",
)
def current_session_resource() -> str:
    """Return the full current session log as a resource."""
    from athena.sessions import recall_last_session

    log_path = recall_last_session()
    if not log_path or not log_path.exists():
        return "No active session."
    return log_path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# RESOURCE: canonical memory
# ---------------------------------------------------------------------------


@mcp.resource(
    uri="athena://memory/canonical",
    name="Canonical Memory",
    description="The Canonical Memory (CANONICAL.md) — Athena's constitution.",
)
def canonical_memory_resource() -> str:
    """Return the Canonical Memory content."""
    from athena.core.config import CANONICAL_PATH

    if not CANONICAL_PATH.exists():
        return "CANONICAL.md not found."

    content = CANONICAL_PATH.read_text(encoding="utf-8")

    # Redact in secret mode
    perms = get_permissions()
    if perms.secret_mode:
        content = perms.redact(content)

    return content


# ---------------------------------------------------------------------------
# TOOL: set_secret_mode
# ---------------------------------------------------------------------------


@mcp.tool(
    tags={"admin", "security", "mode"},
)
def set_secret_mode(enabled: bool) -> dict:
    """
    Toggle Secret Mode (demo/external mode). When active, only PUBLIC
    tools are accessible and sensitive content is redacted.

    Args:
        enabled: True to activate secret mode, False to deactivate.

    Returns:
        dict with mode state and list of blocked tools.
    """
    perms = get_permissions()
    return perms.set_secret_mode(enabled)


# ---------------------------------------------------------------------------
# TOOL: permission_status
# ---------------------------------------------------------------------------


@mcp.tool(
    tags={"read", "system", "security"},
)
def permission_status() -> dict:
    """
    Show the current permission state: caller level, secret mode,
    accessible/blocked tools, and tool manifest.

    Returns:
        dict with full permission state and tool manifest.
    """
    perms = get_permissions()
    status = perms.get_status()
    status["manifest"] = perms.get_tool_manifest()
    return status


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Athena MCP Server")
    parser.add_argument("--sse", action="store_true", help="Use SSE transport")
    parser.add_argument("--port", type=int, default=8765, help="SSE port")
    args = parser.parse_args()

    if args.sse:
        mcp.run(transport="sse", port=args.port)
    else:
        mcp.run(transport="stdio")
