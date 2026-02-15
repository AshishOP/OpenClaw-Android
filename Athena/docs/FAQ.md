# Frequently Asked Questions (FAQ)

> **Last Updated**: 09 February 2026

---

## General

### What is Athena?

Athena is an **open-source framework** for building AI agents with persistent memory. Unlike ChatGPT or Claude's built-in memory, Athena stores everything in **Markdown files you own** — portable, version-controlled, and model-agnostic.

### Is this just a prompt library?

No. Athena is a **system architecture**:

- `.framework/` — Your AI's identity and operating principles
- `.context/` — Long-term memory (decisions, case studies, session logs)
- `.agent/` — Workflows, scripts, and automation

The prompts are part of it, but the real value is the **structure** that compounds over time.

### Which AI models does Athena support?

Athena is **model-agnostic**. It works with:

- **Claude** (Anthropic) — Primary reasoning engine
- **Gemini** (Google) — Embeddings and search
- **GPT** (OpenAI) — Trilateral validation
- Any LLM that can read Markdown files

---

## Setup & Installation

### How long does setup take?

**5 minutes** for the basic install:

```bash
pip install athena-cli
athena init MyAgent
```

For full power features (vector search, GraphRAG), budget 30-60 minutes.

### Do I need API keys?

**Minimal setup**: No API keys required. Works with local files only.

**Full setup** (recommended):

- `ANTHROPIC_API_KEY` — For Claude reasoning
- `GOOGLE_API_KEY` — For embeddings (text-embedding-004)
- `SUPABASE_URL` + `SUPABASE_ANON_KEY` — For vector database (optional)

### Does it work with Cursor? Windsurf?

Yes. Athena is IDE-agnostic. Use:

```bash
athena init --ide cursor    # Creates .cursor/rules.md
athena init --ide antigravity  # Creates AGENTS.md
```

---

## Cost & Performance

### How much does it cost to run?

| Component | Cost |
|-----------|------|
| **Basic usage** (local files only) | Free |
| **Embeddings** (Google API) | ~$0.001 per 1K tokens |
| **Claude API** (direct calls) | Depends on usage |
| **Supabase** (vector DB) | Free tier available |
| **GraphRAG** (knowledge graph) | ⚠️ ~$50 one-time API cost |

Most users spend **< $5/month** on API calls.

### What's the boot time?

| Mode | Time |
|------|------|
| Cold boot (first session) | ~30 seconds |
| Warm boot (cached) | < 5 seconds |

---

## Privacy & Security

### Where does my data go?

**Local Mode**: Everything stays on your machine. Zero data leaves.

**Cloud Mode**: Only embeddings (vectors) are sent to Supabase. Raw text stays local.

**Hybrid Mode** (default): Local files + cloud embeddings for search.

### Is it safe to use for work?

Yes, if you use **Local Mode**. For enterprise use, see [SECURITY.md](./SECURITY.md) for RLS policies and key management.

---

## Troubleshooting

### "athena: command not found"

Ensure the CLI is installed:

```bash
pip install athena-cli
# Or via uv:
uv tool install athena-cli
```

### Session logs not saving

Run `/start` at the beginning of your session. The agent needs to initialize before it can log.

### Context window errors

Athena auto-retrieves ~2K tokens of context. If you're hitting limits, your session may have drifted. Run `/save` to checkpoint and start fresh.

---

## Still stuck?

- **GitHub Issues**: [Report a bug](https://github.com/winstonkoh87/Athena-Public/issues)
- **Discussions**: [Ask a question](https://github.com/winstonkoh87/Athena-Public/discussions)

---

**[Back to README](../README.md)**
