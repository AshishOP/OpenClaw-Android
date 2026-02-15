---
created: '2025-12-26'
last_updated: 2026-02-06
graphrag_extracted: true
---

# Tech Debt Tracker

> **Purpose**: Track identified inefficiencies for future cleanup.
> **Last Updated**: 2026-02-06 (Protocol Min-Max Sprint)

---

## 🟢 API Status (Feb 2026)

> **Status**: ACTIVE (All services operational)

| Service | Endpoint | Cost | Status |
|---------|----------|------|--------|
| Gemini Embedding | `generativelanguage.googleapis.com` (AI Studio) | ✅ **FREE** | ACTIVE |
| GraphRAG Extraction | Protocol 404 (Human Conduit) | ✅ **FREE** | ACTIVE |
| Supabase | Vector DB storage/queries | ✅ **FREE** (free tier) | ACTIVE |

> **Note**: The Jan 2026 GCP bill ($31.82 SGD) was NOT from embeddings — likely Cloud Run or other services.

---

## Recently Completed (Feb 02, 2026 - The Great Steal)

| Status | Item | Notes |
|--------|------|-------|
| ✅ Done | **Protocol 413 (Multi-Agent Safety)** | Added to `Core_Identity.md`. Git corruption prevention. |
| ✅ Done | **Protocol 412 (DM Pairing)** | Telegram security layer implemented (`pairing.py`). |
| ✅ Done | **Protocol 415 (Sandbox)** | Config schema defined for client/untrusted work. |
| ⚠️ Bound | **Protocol 409 (Parallel Worktrees)** | Implemented but hardware-bound (M2 limit). marked as *Aspirational*. |
| ✅ Done | **Protocol 410 (Status)** | `agent_broadcast.py` for orchestration visibility. |

---

## Recently Completed (Feb 01, 2026)

| Status | Item | Notes |
|--------|------|-------|
| ✅ Done | **Boot Resilience** | `boot.py` is now stdlib-only with Recovery Shell fallback |
| ✅ Done | **Config Unification** | `CORE_DIRS` + `EXTENDED_DIRS` in `config.py` |
| ✅ Done | **Athena-Public Cleanup** | v1.5.1: SDK parity, CLI-first docs, duplicate removal |

---

## Recently Completed (Jan 31, 2026)

| Status | Item | Notes |
|--------|------|-------|
| ✅ Done | **The Great Archival** | Moved 20+ Orphaned Scripts & Legacy SQL to `archive/consolidated_2026_01/` |
| ✅ Done | Sidecar exclusion patterns | Prevents indexing of `Winston/`, `Athena-Public/`, `archive/`, `history/` |
| ✅ Done | Master Schema consolidation | `supabase/MASTER_SCHEMA.sql` — single source of truth (8 tables, 8 functions) |
| ✅ Done | Context history folder | Created `.context/history/implementation_plans_2025/` for RAG noise reduction |
| ✅ Done | Public repo blind spots | Fixed 12 issues in `Athena-Public` (see commit a22016d) |

---

## Recently Completed (Dec 28, 2025)

| Status | Item | Notes |
|--------|------|-------|
| ✅ Done | Create `tests/` structure | `.agent/tests/` with pytest smoke tests |
| ✅ Done | Add `atomic_io.py` utility | Atomic write + lockfile + content normalization |
| ✅ Done | Archive `memory_search.py` | Verified no imports, moved to archive/ |
| ✅ Done | 13/14 smoke tests passing | Critical path coverage for sync + quicksave |

---

## Script Consolidation (Resolved)

| Status | Scripts | Consolidated Into |
|--------|---------|-------------------|
| ✅ Done | `get_latest_session.py`, `create_session.py`, `context_capture.py`, `auto_semantic.py` | `boot.py` |
| ✅ Done | `harvest_check.py`, `git_commit.py`, `protocol_compliance.py` (called by) | `shutdown.py` |
| ✅ Done | `batch_audit.py`, `orphan_detector.py`, `structure_map.py` (called by) | `diagnose.py` |
| ✅ Existed | Multiple refactor scripts | `refactor.py` |
| ✅ Done | `memory_search.py` | Archived (was unused legacy wrapper) |
| ✅ Done | **Ollama Dependency** | **DEPRECATED**. Replaced by Gemini 3 Flash (Vectors + Entity Extraction). |

---

## Priority Queue (Revised per Meta-Analysis)

### P0: Circuit Breakers + Timeouts (✅ IMPLEMENTED)

**Invariant**: All external API calls must have timeout + retry + graceful degradation.

| Component | Status | Implementation |
|-----------|--------|----------------|
| Gemini embedding | ✅ Done | 10s timeout, 3x retry, exponential backoff, returns None on fail |
| Supabase sync | ✅ Done | Null-check on embedding, skips chunks gracefully |
| Boot semantic prime | 🟡 Partial | Subprocess timeout exists |

**DoD**:

- [x] Embeddings fail gracefully with retry + backoff
- [x] Failed embeddings don't crash sync (chunk skipped)
- [x] Degraded mode detection with `.athena/degraded_mode.flag`

---

### P0.5: Boot Layer Hardening (✅ IMPLEMENTED Dec 29, 2025)

**Invariant**: Boot failures are detected, bounded, and recoverable.

| Component | Status |
|-----------|--------|
| Boot watchdog (90s timeout) | ✅ SIGALRM handler triggers safe mode suggestion |
| Semantic prime integrity | ✅ SHA-384 verification on Core_Identity.md |
| Safe boot fallback | ✅ `safe_boot.sh` zero-dependency emergency shell |
| Boot self-test | ✅ `boot.py --verify` for pre-flight checks |
| Health canary | ✅ `DEAD_MAN_SWITCH.md` with 90-day audit schedule |
| Watchdog Test | ✅ `test_watchdog.py` verifies SIGALRM trigger |
| Protocol discoverability | ✅ `SKILL_INDEX.md` auto-regenerated with tag index |

---

### P1: Atomic Writes Everywhere (✅ IMPLEMENTED)

**Invariant**: No partial writes. Either old content or new content, never corrupted.

| File | Status |
|------|--------|
| `atomic_io.py` | ✅ Created with write-to-temp + fsync + rename |
| `quicksave.py` | ✅ Integrated atomic_write for checkpoint + correction |
| `supabase_sync.py` | ✅ Done: PID-based lockfile with TTL + degraded mode detection |

**DoD**:

- [x] `atomic_io.py` self-tests pass
- [x] `quicksave.py` uses atomic_write (SIGKILL-safe)
- [x] Concurrent sync runs prevented by lockfile

---

### P2: Hash-Based Delta Sync (PLANNED)

**Invariant**: Unchanged files produce no sync operations (idempotency).

**Implementation**: Add `.athena/state/manifest.json`:

```json
{
  "files": {
    "path/to/file.md": {
      "content_hash": "abc123",
      "last_modified": "2025-12-28T15:00:00Z",
      "last_synced_at": "2025-12-28T15:01:00Z",
      "remote_id": "uuid"
    }
  }
}
```

**DoD**:

- [x] Manifest file created on first sync
- [x] Running sync twice with no changes = zero remote writes
- [x] Hash uses normalized content (via `atomic_io.normalize_for_hash`)

---

## Open Items (Lower Priority)

### P2: README Post-Clone CTA (NEW — Feb 02, 2026)

**Context**: GitHub Traffic Analysis (14-day window)

- 805 clones / 259 unique cloners
- 300 unique visitors to README, only 7-10 going deeper into `/docs`
- **Problem**: High clone-to-visit ratio (~100%) but low post-clone engagement

**Action Required**:

1. Add explicit CTA to README: "Cloned? Start here: [YOUR_FIRST_AGENT.md](docs/YOUR_FIRST_AGENT.md)"
2. Consider Reddit follow-up post (highest quality external traffic source: 40 unique visitors)

**Traffic Sources**:

| Source | Unique Visitors |
|--------|-----------------|
| github.com | 23 |
| Reddit | 40 |
| Google | 9 |
| ProductHunt | 2 |

---

### 1. Bloated Scripts (Resolved)

| Script | Lines | Status |
|--------|-------|--------|
| `supabase_sync.py` | 87 | ✅ Refactored into SDK Shim |
| `query_graphrag.py` | 516 | Functional |
| `supabase_search.py` | 527 | Integrated with GraphRAG |

**Note**: `supabase_sync.py` formerly 1248 lines is now a lightweight shim for `athena.memory.sync`.

### 2. New Items

| Status | Item | Notes | Implementation |
|--------|------|-------|----------------|
| ⚠️ High | System Boot Hardening | [NEW] | boot.py v2.0 shim installed; needs triple-lock audit. |
| ✅ Done | Hash-Based Delta Sync | IMPLEMENTED | O(1) Quick-checks active in `supabase_sync.py`. |
| ✅ Done | Sharded Tag Search | IMPLEMENTED | `search.py` updated to support `A-M` and `N-Z` shards. |
| ✅ Done | Framework v8 Repair | IMPLEMENTED | Fixed broken v7 links and updated manifest. |

---

### 2. Search Scripts (Consolidated)

| Script | Purpose | Status |
|--------|---------|--------|
| `supabase_search.py` | Vector search against Supabase | Active |
| `smart_search.py` | Hybrid search (vector + grep) | Active (primary) |
| `memory_search.py` | Legacy wrapper | ✅ Archived |

---

## Strategic Backlog (Content & Concepts)

| Status | Item | Notes | Implementation |
|--------|------|-------|----------------|
| 📅 Deferred | **IDE Therapist Article** | Concept: `concept-ide-therapist.md` | "Version Controlling Your Personality" hook. Link `vibe-coding` + `melvin-lim`. |
| 📅 Deferred | **Gemini Context Caching** | Advanced | Platform-level integration for zero-latency hot-swapping. Wishlist for now. |
| 📅 Deferred | **Athena Dashboard** | Source: Antigravity Cockpit | Build CLI status script + Portfolio Web Dashboard. Ref: `TECHNICAL_DEBT.md` (Legacy). |
| 📅 Deferred | **GraphRAG Reindex** | ~167 sessions (Jan '26) | Backlog growing. Trigger: 500+ sessions or Portfolio Demo. |
| 📅 Deferred | **Hybrid Model Strategy** | Cost Optimization | **Plan**: Use Gemini 2.5 Flash-Lite ($0.40) for `extract_entities.py` (Translation) and Gemini 3 Flash ($3.00) for Reasoning. Potential 7x savings. |

---

### 3. Boot Layer Constraint

> **Invariant**: `boot.py` must use only stdlib. No SDK dependencies. It is the recovery layer.

If SDK fails or has circular dependency, agent must still boot to fix itself.

**Status**: Currently boot.py uses Path + subprocess + dotenv (acceptable). Do NOT migrate to SDK.

---

## Architecture Improvements (High Priority)

### 4. Evolution to Continuous Gardening (ICM)

**Objective**: Shift from Batch Refactoring (`/refactor`) to Event-Driven Maintenance.
**Status**: [Planned]

| Milestone | Implementation Goal |
|-----------|---------------------|
| **Architecture** | Implement "Hot/Warm/Cold" tiering strategy |
| **Delta Sync** | Replace full scans with `git diff`-based triggers |
| **Queue System** | Add `autoloop.py` worker for background indexing |
| **Backstop** | Converted `/refactor` to lightweight "Cold Audit" |

**Next Step**: Modularize `supabase_sync.py` to support single-file updates.

---

### 3. Archive Candidates (For Reference)

Already archived in `.agent/scripts/archive/`:

- `analyzers/` — Old cost analysis versions (v2, v3)
- `consolidated/` — Scripts folded into orchestrators
- `visualize_graph_lite.py` — Superseded by full version

---

---

## Adversarial Audit Findings (Feb 05, 2026)

> **Context**: "Boss is Watching" Audit. Identified critical fragility in "Zero-Point" Architecture.

| Priority | Item | Description | Status |
|----------|------|-------------|--------|
| ✅ **P0** | **The 429 Trap** | `parallel_orchestrator.py` triggers quota limits (6 calls/query). **FIX**: Token Bucket + Semaphore(2) in v3.0. | **RESOLVED (Feb 06, 2026)** |
| ✅ **P1** | **Context Entropy** | No in-session compression. **FIX**: `context_monitor.py` integrated into `quicksave.py`. | **RESOLVED (Feb 06, 2026)** |
| 🟠 **P2** | **Hardware Ceiling** | M2 Ultra limits prevent true swarm parallelism (Protocol 409). Agent hangs under load. | **OPEN** |
| 🟡 **P2** | **Mirror Maze** | Protocol 75 relies on single-model (Flash). All "adversarial" tracks share the same blind spots. | **OPEN** |
| 🔵 **P3** | **Sovereign Isolation** | No cloud persistence for State. Risk of data loss if hardware fails. | **OPEN** |

---

## Tagging

# tech-debt #efficiency #maintenance
