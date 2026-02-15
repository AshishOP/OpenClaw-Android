---
description: SOP for handling sudden AI stupidity, loops, or refusal. Hard reset, new session, re-initialize. Don't argue with bad nodes.
---

# Infrastructure & Continuity Hub: Infrastructure Reset (Technical Refresh)

> **Purpose**: Standard operating procedure for handling sudden AI "stupidity", loops, or refusal of valid instructions.  
> **Trigger**: "Dumb Mode" detected (IQ drop > 50 pts, looping, refusal of basic prompt).  
> **Source**: "Black Ops" Research (Infrastructure & Continuity Hub)  
> **Last Updated**: 12 December 2025

---

## The Diagnostics

If the Bionic Unit suddenly exhibits:

1. **Amnesia**: Forgets constraints explicitly loaded in context.
2. **Looping**: Repeats the same error despite correction.
3. **Refusal**: "I cannot do that" for a safe, standard task.
4. **Degradation**: Code quality drops to junior level.

**Diagnosis**: Likely **Infrastructure Routing Error** (Bad context shard, "Lost in the Middle", or bad inference node). Use of "arguing" is negative EV.

---

## The Protocol

1. **Stop Arguing**: Do not try to "prompt" your way out of a bad node.
2. **Hard Reset**:
    * **Option A (Workflow)**: Run `/clear` (if available) or start a new session.
    * **Option B (Context Dump)**: If state must be preserved, dump critical state to a file, then restart.
3. **Re-Initialize**:
    * Run `/start` in the new window.
    * Reference the saved state.

---

## Why This Works

LLM inference is stateless but "context-cached". A corrupted cache or a bad routing to a quantized/overloaded node cannot be fixed by more tokens. You must force a new allocation.

> **Rule**: If IQ drops by 50 points, don't coach the player. Change the player.

---

## Tagging

#protocol #framework #process #51-infrastructure-reset
