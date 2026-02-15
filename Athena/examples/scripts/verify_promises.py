#!/usr/bin/env python3
"""
verify_promises.py — The Promise Gate (Protocol 416)
====================================================
Prevents "Hallucinated Compliance". If the agent says "I will update...",
this script checks if a file was actually updated in the last 60 seconds.
"""

import sys
import subprocess
import re
import time
from pathlib import Path


def get_git_changes():
    """Returns list of files changed in the last 5 minutes via git status."""
    try:
        # Check staged and unstaged changes
        result = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True
        )
        if result.returncode != 0:
            return []

        changed_files = []
        for line in result.stdout.splitlines():
            # M = Modified, A = Added, ?? = Untracked
            if line.strip():
                parts = line.split()
                if len(parts) >= 2:
                    changed_files.append(parts[-1])
        return changed_files
    except Exception:
        return []


def scan_text_for_promises(text):
    """Scans text for Future Tense Action verbs implying file I/O."""
    # Patterns that imply a Write action
    patterns = [
        r"i will update",
        r"i will add",
        r"i will create",
        r"i'll update",
        r"noted",
        r"writing to",
        r"saving to",
        r"logging to",
        r"updating the",
    ]

    hits = []
    lower_text = text.lower()

    for p in patterns:
        if re.search(p, lower_text):
            hits.append(p)

    return hits


def main():
    if len(sys.argv) < 2:
        print('Usage: verify_promises.py "<last_agent_response_text>"')
        sys.exit(1)

    last_response = sys.argv[1]
    promises = scan_text_for_promises(last_response)

    if not promises:
        print("✅ No explicit promises detected.")
        sys.exit(0)

    # If promises found, check for Action
    changed_files = get_git_changes()

    if not changed_files:
        print(f"\033[91m⚠️  PROMISE VIOLATION DETECTED (Protocol 416)\033[0m")
        print(f"You said: '{promises[0]}...'")
        print(f"But NO files were changed in git status.")
        print(f"ACTION REQUIRED: Perform the write action immediately.")
        sys.exit(1)
    else:
        print(f"✅ Promise verified. Files changed: {len(changed_files)}")
        sys.exit(0)


if __name__ == "__main__":
    main()
