# Athena Agent Manifest

This is the **machine-readable source of truth** for the Athena Sovereign Agent architecture.

## What It Does

The manifest defines:

- **Session Protocol**: Boot (`/start`) and commit (`/end`) lifecycle hooks
- **Retrieval Pipeline**: RRF Fusion with configurable source weights
- **Orchestration**: ReAct loop with escalation to Tree/Graph search
- **Trilateral Feedback**: Cross-model disagreement detection
- **Budgets**: Token, tool call, and cost limits per session

## Integration

```python
from scripts.core.config_loader import ManifestLoader

# Load config
budgets = ManifestLoader.get_budget_config()
print(f"Token budget: {budgets.token_budget:,}")

# Get retrieval weights
retrieval = ManifestLoader.get_retrieval_config()
print(f"RRF k: {retrieval.rrf_k}")
```

## Files

| File | Purpose |
|------|---------|
| `.agent/config/athena.agent.manifest.json` | Configuration kernel |
| `scripts/core/retrieval/pipeline.py` | RRF Fusion implementation |
| `scripts/core/reflection.py` | Reflexion pattern |
| `scripts/core/auditor.py` | Trilateral feedback |

## Documentation

- [Architecture Overview](../docs/ARCHITECTURE.md)
- [Protocol 415: Exoskeleton](../examples/protocols/architecture/415-exoskeleton-architecture.md)
