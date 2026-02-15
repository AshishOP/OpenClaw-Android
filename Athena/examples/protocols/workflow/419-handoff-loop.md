---
type: protocol
id: 419
version: 1.0
created: 2026-02-05
last_updated: 2026-02-05
tags: [governance, continuity, memory]
---

# Protocol 419: The Handoff Loop (Wake-Up Architecture)

> **Commandment**: "Every session begins where the last one ended."

## The Problem

"Amnesia" is the default state of LLM sessions. Context reconstruction via logs is messy and high-latency.
The Agent needs a specific "Shift Change" briefing.

## The Solution: `wake_up.md`

A dedicated, single-source-of-truth file located at `.context/wake_up.md`.

* **NOT** a history log (past).
* **BUT** a handoff note (future).

## The Workflow

### Phase 1: Sunrise (Boot)

* **Script**: `boot_handoff.py` (No args)
* **Action**: Reads `wake_up.md` and prints it to the console immediately after boot.
* **Agent Duty**: Consume the Handoff Note and initialize short-term memory (RAM) with these priorities.

### Phase 2: Sunset (Shutdown)

* **Script**: `boot_handoff.py "<content>"`
* **Action**: Overwrites `wake_up.md` with the new briefing.
* **Agent Duty**: At `/end`, explicitly formulate the note for the *next* instance.

## Structure of a Good Handoff

1. **Critical State**: "We are mid-refactor on `auth.py`."
2. **Pending Loops**: "Verify the simulation results for $30k bankroll."
3. **Watch Items**: "Keep an eye on token usage."

## Usage

Included in `boot.py` sequence.
See: [boot_handoff.py](../scripts/boot_handoff.py)
