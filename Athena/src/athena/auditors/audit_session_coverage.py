#!/usr/bin/env python3
"""
audit_session_coverage.py
=========================
Audits all session logs to determine GraphRAG readiness.
Checks for:
1. YAML Frontmatter presence
2. 'graphrag_extracted' flag
3. Learning section presence
"""

import os
import re
import yaml
from pathlib import Path

SESSION_DIR = Path(".context/memories/session_logs")
ARCHIVE_DIR = SESSION_DIR / "archive"


def parse_frontmatter(content):
    match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
    if match:
        try:
            return yaml.safe_load(match.group(1))
        except:
            return None
    return None


def audit_file(filepath):
    try:
        with open(filepath, "r") as f:
            content = f.read()

        frontmatter = parse_frontmatter(content)
        has_learnings = "## 📝 Core Learnings" in content or "## Insights" in content

        is_extracted = False
        if frontmatter:
            is_extracted = frontmatter.get("graphrag_extracted", False)

        return {
            "file": filepath.name,
            "has_frontmatter": bool(frontmatter),
            "has_learnings": has_learnings,
            "is_extracted": is_extracted,
        }
    except Exception as e:
        return {"file": filepath.name, "error": str(e)}


def main():
    print(f"Auditing {SESSION_DIR}...")

    results = []

    # Audit active sessions
    for f in SESSION_DIR.glob("*.md"):
        results.append(audit_file(f))

    # Audit archive (sample or full?) -> Full for 100% completion
    for f in ARCHIVE_DIR.rglob("*.md"):
        results.append(audit_file(f))

    total = len(results)
    extracted = sum(1 for r in results if r.get("is_extracted"))
    missing_learnings = sum(
        1 for r in results if not r.get("has_learnings") and not r.get("error")
    )
    backlog = total - extracted

    print(f"\n📊 Session Audit Result")
    print(f"=======================")
    print(f"Total Sessions: {total}")
    print(f"GraphRAG Extracted: {extracted} ({extracted / total * 100:.1f}%)")
    print(f"Backlog: {backlog}")
    print(f"Missing Learnings (Quality Gap): {missing_learnings}")

    # Save detailed backlog to file for extract_entities.py to consume
    with open(".context/graphrag_backlog.txt", "w") as f:
        for r in results:
            if not r.get("is_extracted"):
                f.write(f"{r['file']}\n")

    print(f"\n✅ Backlog written to .context/graphrag_backlog.txt")


if __name__ == "__main__":
    main()
