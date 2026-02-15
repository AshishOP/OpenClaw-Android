# Protocol 418: Active Knowledge Injection

> **Category**: Architecture / Session Management
> **When**: System boot, new session start

## Problem Statement

LLM-based agents write "learnings" to persistent files (e.g., `User_Profile_Core.md`, `AI_Learnings.md`), but these learnings are **passive documentation**. The agent doesn't *read* them unless explicitly prompted, creating a **Hydration Gap** where the same mistakes repeat across sessions.

## The Mechanism

**Context Stuffing > Caching**

| Approach | Behavior |
|----------|----------|
| **Caching (Passive)** | Information is fast to fetch *if* the AI asks for it. |
| **Injection (Active)** | Information is printed to stdout at T=0, forcing it into the context window. |

The fix is **Active Injection**: Force-feed critical constraints into the terminal during boot.

## Implementation

### 1. Create `boot_knowledge.py`

```python
#!/usr/bin/env python3
"""
boot_knowledge.py — Active Knowledge Injection
"""
from pathlib import Path
import re

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROFILE_PATH = PROJECT_ROOT / ".context" / "memories" / "User_Profile_Core.md"

def main():
    if not PROFILE_PATH.exists():
        return
    
    content = PROFILE_PATH.read_text()
    
    # Find sections labeled Constraint, Rule, Protocol, etc.
    sections = re.split(r'^# ', content, flags=re.MULTILINE)
    
    print("=" * 60)
    print("🧠 ACTIVE KNOWLEDGE RECALL")
    print("=" * 60)
    
    for section in sections:
        if any(kw in section for kw in ["Constraint", "Rule", "Protocol"]):
            header = section.split('\n')[0]
            print(f"⚡ {header}")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
```

### 2. Update `boot.py`

Insert the following after the SDK loads successfully:

```python
knowledge_script = PROJECT_ROOT / "scripts" / "core" / "boot_knowledge.py"
if knowledge_script.exists():
    import subprocess
    subprocess.run([sys.executable, str(knowledge_script)])
```

## Expected Output

On every boot, the terminal should display:

```text
🧠 ACTIVE KNOWLEDGE RECALL
============================================================
⚡ Constraint: The Asymmetry Detector
⚡ Protocol: The "Warning Shot" (Boundary Enforcement)
============================================================
```

## Why This Works

1. **Context Stuffing**: The constraints are physically printed to stdout, which the LLM reads as part of the conversation history.
2. **Zero-Shot Recall**: The agent doesn't need to "remember" to read the file; the file reads itself.
3. **Enforcement Loop**: Any forgotten constraint can be added to the profile, and it will automatically surface on the next boot.

---

**See Also**:

- [Protocol 417: Handoff Loop](./417-handoff-loop.md)
- [Protocol 271: Liquid Context](./271-liquid-context.md)
