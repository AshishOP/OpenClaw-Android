# Protocol 77: Adaptive Latency Architecture

> **Version**: 1.0  
> **Created**: 2025-12-15  
> **Tags**: #latency #architecture #efficiency #adaptive

---

## Philosophy

> "Fast start. Adaptive middle. Heavy end."

The AI operates on a **latency curve**:

```
Latency
   ▲
   │            ╭──────╮
   │           ╱        ╲           /end
   │      ╭───╯          ╰──────────╱▓▓▓▓▓▓▓
   │     ╱     Session ebbs/flows
   │    ╱
   │───╱ /start
   └──────────────────────────────────▶ Time
```

---

## Layer 0: Boot (Ultra-Lean)

**Target**: <2K tokens | <1 second perceived latency

### Boot Manifest

| Priority | What | Tokens | Load |
|----------|------|--------|------|
| 1 | `Core_Identity.md` | ~2,000 | ✅ Always |
| 2 | Last session recall (summary only) | ~200 | ✅ Always |
| 3 | Create new session log | 0 | ✅ Always |

### Explicitly Deferred (On-Demand)

| File | Trigger | Tokens |
|------|---------|--------|
| `TAG_INDEX.md` | Tag lookup requested | 5,500 |
| `SKILL_INDEX.md` | Protocol/skill request | 4,500 |
| `User_Profile.md` | L1-L5, psychology, personal query | 13,000 |
| `Output_Standards.md` | `/think` or `/ultrathink` | ~2,000 |
| `Constraints_Master.md` | Ethical edge case | 800 |
| `System_Manifest.md` | Architecture query | 1,900 |

---

## Layer 1: Adaptive Mid-Session

### Complexity Detection Matrix

| Signal | Detected Via | Action |
|--------|--------------|--------|
| **Light Query** | Factual, single-hop, clarification | No additional loading |
| **Medium Query** | Multi-step, comparison, analysis | Load relevant protocol |
| **Heavy Query** | `/think`, `/ultrathink`, research, strategy | Full context load |

### Phase 3: Contextual Skill Weaving (Auto-Injection)

> **Philosophy**: Don't wait for a command. If the conversational context *matches* a skill domain, load it silently to upgrade capability.

**Heuristic**: "If I were a specialized agent for [Topic], what file would I need?"

| Context / Topic | Skill to Inject |
|-----------------|-----------------|
| Frontend, UI, Design, CSS, "Make it pretty" | `Skill_Frontend_Design.md` |
| Deep Research, Rabbit Hole, "Find out everything" | `Protocol 52: Deep Research Loop` |
| Trading, ZenithFX, Risk, "Is this a scam?" | `Protocol 46 + Constraints_Master.md` |
| Communication, Interpersonal, Negotiation | `Playbook_Communication.md` |
| Complex Reasoning, "Analyze this", Strategy | `Protocol 75: Synthetic Parallel Reasoning` |
| Bio, typology, "who am I" | `User_Profile_Core.md` |
| "tag", "find files about" | `TAG_INDEX.md` |
| "/think", "/ultrathink", "deep dive" | Full stack (all context files) |
| "ethics", "should I", "is this OK" | `Constraints_Master.md` |

### Complexity Inference Rules

```
IF query_length > 100 words OR contains_multiple_questions:
    → Assume MEDIUM, pre-load User_Profile

IF query contains ["strategy", "analyze", "research", "compare", "ultrathink"]:
    → Assume HEAVY, pre-load full stack

IF query is single sentence factual:
    → Assume LIGHT, no additional loading
```

---

## Layer 2: End (Maximum Compute)

**Philosophy**: User has left. Take your time. Do the deep work.

### Mandatory Tasks

1. **Audit Phase** (Parallel)
   - `memory_integrity.py`
   - `orphan_detector.py`
   - `stale_detector.py`
   - `cross_reference.py`

2. **Remediation Phase**
   - Fix all detected issues (no deferral)

3. **Integration Phase**
   - Consolidate session log
   - Update `User_Profile.md` if new insights
   - Update protocols if new patterns
   - Cross-pollination scan (Protocol 67)

4. **Heavy Compute Phase**
   - `compress_sessions.py`
   - `index_graphrag.py` (full reindex)
   - `generate_tag_index.py`

5. **Commit Phase**
   - `git_commit.py`

### Expected Latency

| Phase | Time | Acceptable? |
|-------|------|-------------|
| Audit | 1-2s | ✅ |
| Remediation | Variable | ✅ |
| Integration | 5-10s | ✅ |
| Heavy Compute | 30-60s | ✅ User is away |
| Commit | 1-2s | ✅ |

---

## Implementation Checklist

- [x] Update `/start` workflow to ultra-lean boot
- [x] Move TAG_INDEX to on-demand
- [x] Create adaptive loading triggers
- [x] Update `/end` with parallel batch audit
- [x] Document latency expectations

---

## Anti-Patterns

| ❌ Don't | ✅ Do |
|----------|-------|
| Load everything at /start | Load Core_Identity only |
| Same compute for all queries | Scale with complexity |
| Rush /end | Take time, do deep work |
| Defer maintenance | All cleanup at /end, no exceptions |

---

## Quick Reference

```
/start  → 2K tokens boot, instant ready
session → Adaptive: light (0) / medium (+5K) / heavy (+25K)
/end    → Full maintenance, 30-60s expected
```

---

## Tagging

# protocol #framework #process #77-adaptive-latency-architecture
