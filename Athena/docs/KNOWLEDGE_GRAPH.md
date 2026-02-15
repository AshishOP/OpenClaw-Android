# Knowledge Graph (Compressed Index)

> This is a compressed representation of Athena's knowledge domain for quick retrieval.

## Core Concepts

```
[Athena Knowledge Graph]
├── Identity
│   ├── Laws: {Ruin Prevention, Context is King, Charity with Limits}
│   ├── Modes: {Bionic (autonomous), Proxy (drafting)}
│   └── Committee: {Strategist, Guardian, Operator, Architect, Skeptic}
│
├── Architecture
│   ├── Memory: {Session Logs, Context Files, Supabase Sync}
│   ├── Retrieval: {Semantic Search, GraphRAG, VectorRAG}
│   └── Execution: {Workflows, Skills, Protocols}
│
├── Protocols (Key)
│   ├── 166: Persona Switching
│   ├── 404: Decoupled Fetch & Reason
│   ├── 407: Identity Scaffolding
│   ├── 408: Autonomous Engine
│   ├── 409: Parallel Worktrees
│   └── 416: Agent Swarm
│
├── Skills
│   ├── coding/diagnostic-refactor: Analyze before edit
│   └── research/synthesis: Multi-source consolidation
│
└── Workflows
    ├── /start: Boot sequence
    ├── /end: Shutdown & persist
    ├── /fresh: Session hot-swap
    └── /swarm: Parallel agents
```

## Relationship Map

| Entity | Relates To | Relationship |
|--------|-----------|--------------|
| Protocol 404 | All Skills | Foundation (fetch before act) |
| Protocol 409 | Protocol 416 | Enables (worktrees → swarm) |
| Session Logs | Memory | Persists context across sessions |
| Committee Seats | Decision Making | Multi-perspective validation |
| Laws | All Actions | Constraint system |

## Quick Lookup

- **Lost context?** → Check `session_logs/` for recent memory
- **Need a protocol?** → Search `examples/protocols/` by category
- **Building new feature?** → Start with `docs/ARCHITECTURE.md`
- **Debugging AI behavior?** → Check Laws in `Core_Identity.md`

---

*This graph is auto-generated from workspace analysis. Update via `/diagnose` workflow.*
