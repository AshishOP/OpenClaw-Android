# Athena Spec Sheet

> **Version**: v8.5.0
> **Date**: 13 February 2026
> **Architect**: Winston Koh
> **Status**: Production (1,079+ sessions)

---

## 1. System Overview

**Athena** is a local operating system for AI agents. It provides persistent memory, bounded autonomy, and time-awareness to any LLM.

| Attribute | Value |
|-----------|-------|
| **Type** | Local-first AI agent OS |
| **License** | MIT |
| **Runtime** | Python 3.10+ |
| **Primary Storage** | Markdown files (Git-versioned) |
| **Secondary Storage** | Supabase + pgvector (cloud backup + semantic search) |
| **Fallback Storage** | SQLite / LanceDB (offline mode) |
| **Interface** | Any MCP-compatible IDE (Antigravity, Cursor, VS Code) |

---

## 2. Architecture

```text
┌──────────────────────────────────────────────┐
│              Your Machine (Owned)             │
│  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │ Markdown  │  │ Session  │  │  Tag Index  │  │
│  │  Files    │  │  Logs    │  │  (8K tags)  │  │
│  └────┬─────┘  └────┬─────┘  └──────┬─────┘  │
│       └──────────────┼───────────────┘        │
│                      ▼                        │
│            ┌──────────────────┐               │
│            │   Git (Versioned) │               │
│            └────────┬─────────┘               │
└─────────────────────┼────────────────────────┘
                      ▼
            ┌──────────────────┐
            │  Supabase Cloud   │
            │  (Insurance Copy) │
            └──────────────────┘
```

### Directory Structure

| Directory | Purpose | Analogy |
|-----------|---------|---------|
| `.framework/` | Core identity, laws, constitution | The DNA |
| `.context/` | Memories, session logs, tag indexes | The Brain |
| `.agent/` | Skills, workflows, scripts | The Hands |
| `src/athena/` | Python SDK (search, MCP, governance) | The Nervous System |
| `docs/` | Documentation | The Manual |
| `examples/` | Quickstart demos, protocols, templates | The Textbook |

---

## 3. Core Loop

```text
/start → Load Identity + Recall → Work Session → Quicksave (auto) → /end → Persist + Git Commit
```

| Phase | Compute Level | Operations |
|-------|--------------|------------|
| `/start` | **Maximum** | Load core identity, recall last session, create log, health check |
| Work | **Adaptive** | Responds at complexity-appropriate depth (Λ+5 to Λ+100) |
| `/end` | **Maximum** | Finalize log, harvest insights, sync memory, git commit |

---

## 4. Data Schema

### Session Logs (Markdown)

```yaml
# Frontmatter
date: 2026-02-13
session: 1085
version: v8.5.0
tags: [memory, search, mcp]

# Body
## Key Decisions
## Checkpoints (auto-appended)
## Synthetic RLHF (end-of-session calibration)
```

### Vector Embeddings (Supabase)

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `content` | TEXT | Raw text chunk |
| `embedding` | VECTOR(768) | text-embedding-004 |
| `metadata` | JSONB | Source file, tags, timestamp |

### Tag Index (Markdown)

```text
#memory → 47 files
#search → 31 files
#protocol → 330 files
Total: 8,079 tags across 1,460 communities
```

---

## 5. API Surface (MCP Server)

9 tools + 2 resources via Model Context Protocol.

| Tool | Permission | Latency |
|------|-----------|---------|
| `smart_search` | read | < 200ms |
| `agentic_search` | read | < 2s (multi-step) |
| `quicksave` | write | < 100ms |
| `health_check` | read | < 500ms |
| `recall_session` | read | < 100ms |
| `governance_status` | read | < 100ms |
| `list_memory_paths` | read | < 100ms |
| `set_secret_mode` | admin | instant |
| `permission_status` | read | instant |

**Transport**: stdio (IDE integration) or SSE (remote access, port 8765).

---

## 6. Search Architecture

```text
Query → [Keyword Search (Tag Index)] ──┐
                                        ├── RRF Fusion → Reranker → Results
Query → [Semantic Search (pgvector)] ──┘
```

| Metric | Value |
|--------|-------|
| **Search MRR** | 0.44 (vs 0.21 baseline, +105%) |
| **Latency** | < 200ms (p95) |
| **Index Size** | 8,079 tags, 46MB knowledge graph, 78MB vectors |
| **Fusion Method** | Reciprocal Rank Fusion (RRF) with score-modulated weights |

---

## 7. Tech Stack

| Layer | Technology |
|-------|-----------|
| **Language** | Python 3.12 |
| **Embeddings** | Google text-embedding-004 (768d) |
| **Vector DB** | Supabase + pgvector (IVFFlat index) |
| **Graph** | Microsoft GraphRAG pattern (community detection) |
| **Packaging** | pyproject.toml (PEP 621) |
| **Version Control** | Git |
| **CI/CD** | None (single-user local tool) |
| **Hosting** | Local machine (primary), GitHub (remote backup) |

---

## 8. Governance & Constraints

| Rule | Description | Enforcement |
|------|-------------|-------------|
| **Triple Lock** | Every session: Search → Save → Output | `governance.py` |
| **No Monoliths** | 1 Skill = 1 File | Convention + audit scripts |
| **Entropy Limit** | Maintenance > 2 hrs/week for 4 weeks → degrade gracefully | Protocol 106 |
| **Amnesia Failure** | Session restore fails 3x/month → system declared FAILED | Boot health check |
| **Secret Mode** | Demo mode blocks internal tools, redacts sensitive content | `permissions.py` |

---

## 9. Performance Benchmarks

| Metric | Target | Actual |
|--------|--------|--------|
| Boot time | < 60s | **< 30s** |
| Search latency | < 500ms | **< 200ms** |
| Context injection | < 10K tokens | **~4K tokens** |
| Quicksave overhead | < 500ms | **< 100ms** |
| Session log write | < 1s | **< 500ms** |

→ Full benchmarks: [BENCHMARKS.md](BENCHMARKS.md)

---

## 10. Acceptance Criteria

| Test | Expected | Result |
|------|----------|--------|
| **Sunset Test** | Unused skills auto-archived after 90 days | ✅ Protocol 106 |
| **Sidecar Verify** | Agent queries vector index, not raw grep | ✅ pgvector + RRF |
| **Triple Lock** | Log entries exist for every session | ✅ Enforced by governance engine |
| **Crash Recovery** | `/start` after crash restores last checkpoint | ✅ Quicksave durability |
| **Model Swap** | Memory persists across LLM provider switch | ✅ Markdown-based |

---

## Related Documents

| Document | Purpose |
|----------|---------|
| [REQUIREMENTS.md](REQUIREMENTS.md) | User stories, functional requirements, constraints |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design, data flow, hub model |
| [BENCHMARKS.md](BENCHMARKS.md) | Quantitative performance data |
| [FEATURES.md](FEATURES.md) | User-facing feature descriptions |
| [CAPABILITIES.md](CAPABILITIES.md) | Full automation catalog |
| [GLOSSARY.md](GLOSSARY.md) | Term definitions |
