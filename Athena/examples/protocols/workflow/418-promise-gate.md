---
type: protocol
id: 418
version: 1.0
created: 2026-02-05
last_updated: 2026-02-05
tags: [governance, enforcement, hooks]
---

# Protocol 418: The Promise Gate

> **Commandment**: "If you say you will do it, you must have already done it."

## The Problem

LLMs often hallucinate compliance. "I have updated the file" is a sentence, not an action.
If the context window closes without the `write_file` tool call, the "update" vanishes.

## The Enforcement Mechanism

A "Stop Hook" (`verify_promises.py`) runs after every response generation (or via `quicksave.py`).

1. **Scan**: The script scans the agent's last text output for "Promise Patterns".
    * "I will update..."
    * "Noted..."
    * "I have added..."
2. **Verify**: The script checks the filesystem (`git status`) for actual modifications.
3. **Gate**:
    * **Promise + File Change**: ✅ PASS
    * **Promise + No Change**: ❌ FAIL (Response Blocked / Error Thrown)

## The "Write-Before-Speak" Rule

To pass the Promise Gate, the Agent must adopt the **Write-Before-Speak** heuristic:

* **Wrong**: "I will update the file now." (Text first, Action later) -> *Risk of drift*.
* **Right**: [Call Tool: Write File] -> "I have updated the file." (Action first, Text confirmation) -> *Passes Gate*.

## Usage

This protocol is enforced autonomically by the `quicksave.py` wrapper.
See: [verify_promises.py](../scripts/verify_promises.py)
