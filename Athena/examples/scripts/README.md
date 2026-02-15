# Scripts

> **Status**: Selected scripts now **open-sourced** (Jan 2026).

This folder contains automation scripts that power Athena's parallel execution layer.

## Available Scripts

| Script | Purpose |
| :--- | :--- |
| `gemini_client.py` | Reusable Gemini API wrapper with model fallback cascade. |
| `parallel_orchestrator.py` | Protocol 75 implementation — 4-track parallel reasoning via API. |
| `parallel_swarm.py` | Protocol 101 Launcher — spawns 4 Terminal windows with isolated agents. |
| `swarm_agent.py` | Role-based agent process (Domain, Adversarial, Cross-Domain, Zero-Point). |
| `worktree_manager.py` | Git worktree CRUD (create, list, clean). |
| `git_commit.py` | AI-assisted semantic git commits. |

## Usage

```bash
# Run Protocol 75 (API-only, single process)
python3 examples/scripts/parallel_orchestrator.py "Your query here"

# Run Protocol 101 (Multi-window swarm)
python3 examples/scripts/parallel_swarm.py "Your objective" "branch-name"

# Cleanup worktrees
python3 examples/scripts/worktree_manager.py clean-all
```

## Dependencies

- Python 3.10+
- `google-generativeai` (`pip install google-generativeai`)
- `python-dotenv` (`pip install python-dotenv`)
- A `GOOGLE_API_KEY` in your environment.

---

# public #scripts #parallelism
