# Protocol 101: Native Swarm (Parallel Agent Orchestration)

> **Source**: Inspired by `Maestro` (r/ClaudeCode), adapted for Athena.
> **Status**: ACTIVE (v8.0-Stable)
> **Tags**: `#parallelism` `#orchestration` `#protocol` `#architecture`

---

## 1. Purpose

Protocol 101 enables parallel execution of AI reasoning tracks (Protocol 75) by physically isolating each track in a **Git Worktree** (Protocol 100) and spawning dedicated terminal sessions.

This is a "Token Burner" strategy for maximizing throughput on subscription-based AI plans.

---

## 2. Architecture

```
┌───────────────────────────────────────────────────────────────┐
│               parallel_swarm.py (Launcher)                    │
│                         │                                     │
│    ┌────────────────────┼────────────────────┐                │
│    │                    │                    │                │
│    ▼                    ▼                    ▼                │
│ ┌─────────┐       ┌─────────┐         ┌─────────┐            │
│ │ Track A │       │ Track B │  ...    │ Track D │            │
│ │ Domain  │       │ Advers. │         │ Zero Pt │            │
│ └────┬────┘       └────┬────┘         └────┬────┘            │
│      │                 │                   │                  │
│      ▼                 ▼                   ▼                  │
│   Worktree A        Worktree B          Worktree D           │
│   (Isolated)        (Isolated)          (Isolated)           │
└───────────────────────────────────────────────────────────────┘
```

---

## 3. Components

| Script | Role |
| :--- | :--- |
| `worktree_manager.py` | CRUD operations for Git worktrees. |
| `parallel_swarm.py` | Orchestrator. Creates worktrees, spawns Terminal windows. |
| `swarm_agent.py` | The process running in each window. Role-specific persona. |

---

## 4. Usage

### Launch the Swarm

```bash
python3 examples/scripts/parallel_swarm.py "Your objective here" "branch-base-name"
```

**Example:**

```bash
python3 examples/scripts/parallel_swarm.py "Audit this codebase for security vulnerabilities" "sec-audit"
```

### Cleanup

```bash
python3 examples/scripts/worktree_manager.py clean-all
```

---

## 5. References

- [Protocol 75: Synthetic Parallel Reasoning](../decision/75-synthetic-parallel-reasoning.md)
- [Protocol 100: Git Worktree Parallelism](../engineering/100-git-worktree-parallelism.md)
