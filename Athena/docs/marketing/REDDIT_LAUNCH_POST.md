---
title: [Open Source] I open-sourced my production agent architecture after 1,000+ sessions: Hybrid RAG (Graph + Vector + RRF), protocol enforcement, and Git-style memory management.
flair: Resources & Guides
subreddit: r/google_antigravity
---

I saw u/MathiRaja's post asking how to actually set up agent skills from scratch. Same struggle here months ago. So I'm sharing the full **Reference Architecture** I've been running daily.

**TL;DR**: [github.com/winstonkoh87/Athena-Public](https://github.com/winstonkoh87/Athena-Public) — MIT licensed, clone and go.

---

### What's in the box

| Component | What it does |
|-----------|--------------|
| **Hybrid RAG (RRF)** | **Killer Feature**. Fuses Dense Vector Retrieval with Keyword Matching using Reciprocal Rank Fusion. Solves the issue where agents "forget" exact file paths or syntax. |
| **63 protocols** | Decision frameworks (not prompts — reusable thinking patterns) |
| **12 reference scripts** | `boot.py`, `quicksave.py`, `smart_search.py` — the actual commands |
| **6 case studies** | Real examples: boot optimization, search quality, protocol enforcement |
| **Session loop** | `/start` → Work → `/end` — your agent remembers across sessions |

---

### The folder structure

*(Standard scaffolding, but note `.context` is the persistent memory layer)*

```
Athena-Public/
├── .agent/
│   ├── skills/        ← Your protocols live here (The Brain)
├── .context/          ← Session logs, memories (The Hard Drive)
├── .framework/        ← Core identity, laws (The BIOS)
├── src/athena/        ← pip installable SDK
└── docs/              ← Deep dives (GraphRAG, VectorRAG, etc.)
```

---

### The loop

```
/start → retrieves context from long-term memory
Work → Athena has your history, protocols, decisions
/end → extracts insights, commits to memory, logs session
```

Think Git, but for conversations.

---

### Why this exists

I got tired of "agent frameworks" that are just glorified `while True` loops wrapping an LLM API. They work for 5 minutes but degrade into hallucination loops after 50 turns.

To run an agent for **1,000+ sessions**, I needed actual engineering, not just prompt engineering.

* I needed **RRF Fusion** because simple vector search misses semantic nuance.
* I needed **hard-coded protocols** because "asking nicely" stops working when the context window fills up.

This isn't a product. It's the engine room of my daily driver. I'm open-sourcing it because I'm tired of rewriting the same boilerplate for every new project.

---

**Link**: [github.com/winstonkoh87/Athena-Public](https://github.com/winstonkoh87/Athena-Public)

Happy to answer questions. AMA.
