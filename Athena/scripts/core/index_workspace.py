#!/usr/bin/env python3
"""
index_workspace.py — Unified Indexing Engine
============================================
Generates and maintains the map of the workspace.
1. TAG_INDEX.md: Maps #tags to files.
2. PROTOCOL_SUMMARIES.md: Compressed index of all protocols.

Usage: python3 .agent/scripts/index_workspace.py
"""

import os
import re
from pathlib import Path
from datetime import datetime

# Setup Paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTEXT_DIR = PROJECT_ROOT / ".context"
PROTOCOLS_DIR = PROJECT_ROOT / ".agent" / "skills" / "protocols"
TAG_INDEX_FILE = CONTEXT_DIR / "TAG_INDEX.md"
PROTOCOL_SUMMARIES_FILE = CONTEXT_DIR / "PROTOCOL_SUMMARIES.md"


def generate_tag_index():
    """Scans the workspace for #tags and builds an index."""
    tag_map = {}

    # Files and directories to ignore
    ignore_patterns = {
        ".git",
        ".agent",
        "node_modules",
        "dist",
        "build",
        ".venv",
        ".context/cache",
        ".athena",
        "winstonkoh87_backup",
        "Athena-Public.wiki",
        "__pycache__",
        ".pytest_cache",
        ".shared",
        ".athena",
        ". Clawdhub",
    }

    for root, dirs, files in os.walk(PROJECT_ROOT):
        # Prune ignored directories from recursion
        dirs[:] = [
            d
            for d in dirs
            if not any(p in str(Path(root) / d) for p in ignore_patterns)
        ]

        for file in files:
            if file.endswith((".md", ".py", ".js", ".ts", ".astro")):
                path = Path(root) / file
                try:
                    # Skip if any ignore pattern is in the absolute path
                    if any(p in str(path) for p in ignore_patterns):
                        continue

                    content = path.read_text(encoding="utf-8", errors="ignore")
                    # Match tags that start with # but are not hex codes (3 or 6 chars)
                    # Filter: Must start with letter, at least 3 chars.
                    candidates = re.findall(r"(?<!\w)#([a-zA-Z][\w-]{2,})", content)
                    for tag in candidates:
                        # Further filter out common noise
                        if tag.lower() in {"py", "md", "js", "ts", "astro", "tmp"}:
                            continue

                        if tag not in tag_map:
                            tag_map[tag] = []
                        rel_path = path.relative_to(PROJECT_ROOT)
                        if str(rel_path) not in tag_map[tag]:
                            tag_map[tag].append(str(rel_path))
                except Exception:
                    continue

    # Write TAG_INDEX.md
    output = [
        "# Tag Index\n",
        f"> **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
        "---\n",
    ]
    for tag in sorted(tag_map.keys()):
        output.append(f"## #{tag}")
        for path in sorted(tag_map[tag]):
            output.append(f"- [{os.path.basename(path)}]({path})")
        output.append("")

    TAG_INDEX_FILE.write_text("\n".join(output))
    print(f"✅ Generated {TAG_INDEX_FILE}")


def generate_protocol_summaries():
    """Scans protocol folders and builds a compressed summary table."""
    protocols = []

    for path in PROTOCOLS_DIR.rglob("*.md"):
        try:
            content = path.read_text(encoding="utf-8")
            # Extract Code/Title
            title_match = re.search(
                r"^# (?:Protocol )?(\d+)[:.]?\s*(.*)", content, re.MULTILINE
            )
            if title_match:
                code = title_match.group(1)
                title = title_match.group(2).strip()
            else:
                code = "???"
                title = path.stem

            # Extract Trigger (When)
            trigger_match = re.search(r"\*\*When\*\*:\s*(.*)", content)
            trigger = trigger_match.group(1).strip() if trigger_match else "---"

            # Extract Summary
            summary_match = re.search(
                r"^#.*?$.*?^(.+)", content, re.MULTILINE | re.DOTALL
            )
            summary = (
                summary_match.group(1).strip()[:100] + "..." if summary_match else "---"
            )

            protocols.append(
                {
                    "code": code,
                    "title": title,
                    "trigger": trigger,
                    "summary": summary,
                    "path": path.relative_to(PROJECT_ROOT),
                }
            )
        except Exception:
            continue

    # Sort by code
    protocols.sort(key=lambda x: x["code"])

    # Write PROTOCOL_SUMMARIES.md
    output = [
        "# Protocol Summaries (Compressed)\n",
        f"> **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
        f"> **Total**: {len(protocols)} protocols\n",
        "---\n",
        "| Code | Title | Trigger | Summary |",
        "|------|-------|---------|---------|",
    ]

    for p in protocols:
        row = f"| {p['code']} | [{p['title']}]({p['path']}) | {p['trigger']} | {p['summary']} |"
        output.append(row)

    PROTOCOL_SUMMARIES_FILE.write_text("\n".join(output))
    print(f"✅ Generated {PROTOCOL_SUMMARIES_FILE}")


if __name__ == "__main__":
    CONTEXT_DIR.mkdir(parents=True, exist_ok=True)
    generate_tag_index()
    generate_protocol_summaries()
