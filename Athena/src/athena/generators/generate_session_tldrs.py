#!/usr/bin/env python3
"""
generate_session_tldrs.py — Generate one-liner summaries for all sessions.

Creates session_tldrs.json with quick-reference summaries for context recall.
Pure regex extraction — no LLM calls, runs in <30s.

Usage:
    python3 generate_session_tldrs.py
"""

import json
import re
import hashlib
from pathlib import Path
from datetime import datetime

# Configuration
WORKSPACE = Path(__file__).resolve().parent.parent.parent
SESSIONS_DIR = WORKSPACE / ".context" / "memories" / "session_logs"
ARCHIVE_DIR = SESSIONS_DIR / "archive"
OUTPUT_JSON = WORKSPACE / ".context" / "cache" / "session_tldrs.json"
OUTPUT_MD = WORKSPACE / ".context" / "cache" / "SESSION_TLDRS.md"


def extract_tldr(content: str) -> str:
    """Extract a one-liner summary from session content."""

    # Priority 1: Explicit TL;DR or Summary section
    patterns = [
        r"##\s*(?:TL;?DR|Summary|Key Insights?)\s*\n+(.+?)(?:\n\n|\n##|\Z)",
        r"\*\*(?:TL;?DR|Summary)\*\*:?\s*(.+?)(?:\n\n|\n##|\Z)",
        r"##\s*Session Summary\s*\n+(.+?)(?:\n\n|\n##|\Z)",
    ]

    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            text = match.group(1).strip()
            # Clean and truncate
            text = re.sub(r"\s+", " ", text)  # Collapse whitespace
            text = re.sub(r"^[-*•]\s*", "", text)  # Remove bullet
            if len(text) > 20:
                return text[:150].strip() + ("..." if len(text) > 150 else "")

    # Priority 2: First H2 section content
    h2_match = re.search(
        r"^##\s+(.+?)\n+(.+?)(?:\n\n|\n##|\Z)", content, re.MULTILINE | re.DOTALL
    )
    if h2_match:
        section_title = h2_match.group(1).strip()
        section_content = h2_match.group(2).strip()
        # Skip metadata sections
        if section_title.lower() not in ["metadata", "context", "session info"]:
            text = re.sub(r"\s+", " ", section_content)
            text = re.sub(r"^[-*•]\s*", "", text)
            if len(text) > 20:
                return text[:150].strip() + ("..." if len(text) > 150 else "")

    # Priority 3: First meaningful paragraph
    paragraphs = content.split("\n\n")
    for p in paragraphs:
        p = p.strip()
        # Skip headers, frontmatter, and short lines
        if p.startswith("#") or p.startswith("---") or len(p) < 30:
            continue
        text = re.sub(r"\s+", " ", p)
        if len(text) > 30:
            return text[:150].strip() + ("..." if len(text) > 150 else "")

    return "Session summary pending."


def extract_date(filename: str) -> str:
    """Extract date from session filename."""
    match = re.match(r"(\d{4}-\d{2}-\d{2})", filename)
    return match.group(1) if match else "unknown"


def main():
    print("📋 SESSION TL;DR GENERATOR")
    print("=" * 50)

    # Ensure output directory exists
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)

    # Collect all session files
    session_files = []
    for dir_path in [SESSIONS_DIR, ARCHIVE_DIR]:
        if dir_path.exists():
            session_files.extend(list(dir_path.glob("*.md")))

    # Sort by date (newest first)
    session_files = sorted(session_files, key=lambda f: f.name, reverse=True)

    print(f"   Found {len(session_files)} session files")

    # Process sessions
    tldrs = {}
    for file_path in session_files:
        try:
            content = file_path.read_text(encoding="utf-8")
            tldr = extract_tldr(content)
            date = extract_date(file_path.name)

            tldrs[file_path.name] = {
                "date": date,
                "tldr": tldr,
                "path": str(file_path.relative_to(WORKSPACE)),
            }
        except Exception as e:
            print(f"   ⚠️ Error processing {file_path.name}: {e}")

    # Check if content changed (lazy update)
    new_content = json.dumps(tldrs, indent=2, ensure_ascii=False)
    if OUTPUT_JSON.exists():
        existing_hash = hashlib.md5(OUTPUT_JSON.read_bytes()).hexdigest()
        new_hash = hashlib.md5(new_content.encode()).hexdigest()
        if existing_hash == new_hash:
            print("⏭️ SESSION_TLDRS unchanged, skipping regeneration")
            return

    # Write JSON
    OUTPUT_JSON.write_text(new_content, encoding="utf-8")
    print(f"✅ Wrote {len(tldrs)} entries to {OUTPUT_JSON}")

    # Write Markdown summary
    md_content = f"""# Session TL;DRs (Quick Reference)

> **Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M")}
> **Total**: {len(tldrs)} sessions
> **Purpose**: One-liner session summaries for fast context recall.

---

| Date | Session | TL;DR |
|------|---------|-------|
"""

    for filename, data in sorted(tldrs.items(), reverse=True)[:100]:  # Top 100
        md_content += (
            f"| {data['date']} | `{filename[:30]}` | {data['tldr'][:80]}... |\n"
        )

    md_content += """
---

#index #sessions #cache
"""

    OUTPUT_MD.write_text(md_content, encoding="utf-8")
    print(f"✅ Wrote summary to {OUTPUT_MD}")


if __name__ == "__main__":
    main()
