#!/usr/bin/env python3
"""
boot_knowledge.py — Active Knowledge Injection
==============================================
Force-feeds critical constraints from User_Profile_Core.md into the
context window during system boot.

Target: Fixes the "Hydration Gap" where learnings exist but are ignored.
"""

import sys
import re
from pathlib import Path

# Setup Paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROFILE_PATH = PROJECT_ROOT / ".context" / "memories" / "User_Profile_Core.md"

# ANSI Colors
YELLOW = "\033[93m"
CYAN = "\033[96m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def fetch_active_constraints():
    """Parses User_Profile_Core.md for high-priority constraints."""
    if not PROFILE_PATH.exists():
        return None

    content = PROFILE_PATH.read_text(encoding="utf-8")
    constraints = []

    # Regex to find headers like "# [NEW] Constraint: ..." or "# [NEW] Rule: ..."
    # We want to capture the Header + the Blockquote content immediately following it

    # Simple strategy: Split by headers, look for keywords
    sections = re.split(r"^# ", content, flags=re.MULTILINE)

    for section in sections:
        if not section.strip():
            continue

        lines = section.split("\n")
        header = lines[0].strip()
        body = "\n".join(lines[1:]).strip()

        # Keywords that signal a Constraint/Rule/Protocol
        keywords = [
            "Constraint",
            "Rule",
            "Protocol",
            "Conviction",
            "Preference",
            "Boundary",
        ]

        if any(kw in header for kw in keywords):
            # Extract the core message from blockquotes
            core_message = []
            for line in body.split("\n"):
                if line.strip().startswith(">"):
                    core_message.append(line.strip())

            if core_message:
                constraints.append({"header": header, "body": "\n".join(core_message)})

    return constraints


def main():
    constraints = fetch_active_constraints()

    if not constraints:
        return

    print("\n" + "=" * 60)
    print(f"{YELLOW}{BOLD}🧠 ACTIVE KNOWLEDGE RECALL (User_Profile_Core.md){RESET}")
    print("=" * 60)

    for item in constraints:
        header = item["header"]
        # Clean header tags like [NEW] for display
        display_header = re.sub(r"\[.*?\]", "", header).strip()

        print(f"\n{CYAN}⚡ {display_header}{RESET}")
        print(f"{item['body']}")

    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
