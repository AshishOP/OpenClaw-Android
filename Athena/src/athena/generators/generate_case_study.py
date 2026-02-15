#!/usr/bin/env python3
"""
Auto Case Study Generator
Feed a session log → get a structured case study.
"""
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))
from gemini_client import get_client

load_dotenv()

CASE_STUDY_DIR = Path(".context/memories/case_studies")
CASE_STUDY_DIR.mkdir(parents=True, exist_ok=True)

SYSTEM_PROMPT = """You are a case study generator for the Athena AI system. Given a session log, extract the key insight or pattern and generate a structured case study.

Output format (markdown):
```
# Case Study: [Descriptive Title]

## Pattern Identified
[One-line summary of the core pattern/insight]

## Context
[2-3 sentences of background]

## Analysis
[Key observations, mechanisms, implications]

## Takeaways
- [Bullet 1]
- [Bullet 2]
- [Bullet 3]

## Cross-References
- Related: [links to other protocols/case studies if obvious]

---
**Tags**: #casestudy #[relevant-tags]
```

Be concise. Focus on the transferable insight, not the specific details."""

def generate_case_study(session_content: str) -> tuple[str, str]:
    """Generate case study from session log. Returns (title, content)."""
    client = get_client()
    
    prompt = f"""{SYSTEM_PROMPT}

=== SESSION LOG ===
{session_content}
=== END SESSION LOG ===

Generate a case study based on this session:"""
    
    response = client.generate(prompt)
    
    # Extract title from first line
    lines = response.strip().split('\n')
    title = "Untitled"
    for line in lines:
        if line.startswith("# Case Study:"):
            title = line.replace("# Case Study:", "").strip()
            break
    
    return title, response

def main():
    parser = argparse.ArgumentParser(description="Generate case study from session log")
    parser.add_argument("session_file", nargs="?", help="Path to session log file")
    parser.add_argument("--latest", action="store_true", help="Use the latest session log")
    parser.add_argument("--output", help="Output filename (auto-generated if not specified)")
    parser.add_argument("--dry-run", action="store_true", help="Print to stdout without saving")
    args = parser.parse_args()

    # Get session file
    if args.latest:
        session_logs = Path(".context/memories/session_logs")
        logs = sorted(session_logs.glob("*.md"), reverse=True)
        if not logs:
            print("No session logs found")
            sys.exit(1)
        session_file = logs[0]
    elif args.session_file:
        session_file = Path(args.session_file)
    else:
        parser.print_help()
        sys.exit(1)

    if not session_file.exists():
        print(f"Error: File not found: {session_file}")
        sys.exit(1)

    print(f"📄 Reading: {session_file}")
    content = session_file.read_text(encoding="utf-8")
    
    print("🤖 Generating case study...")
    title, case_study = generate_case_study(content)
    
    if args.dry_run:
        print("\n" + case_study)
        return

    # Generate filename
    if args.output:
        output_file = CASE_STUDY_DIR / args.output
    else:
        # Create safe filename from title
        safe_title = "".join(c if c.isalnum() or c in " _-" else "" for c in title)
        safe_title = safe_title.replace(" ", "_")[:50]
        timestamp = datetime.now().strftime("%Y%m%d")
        output_file = CASE_STUDY_DIR / f"CS_{timestamp}_{safe_title}.md"

    output_file.write_text(case_study, encoding="utf-8")
    print(f"✅ Saved: {output_file}")

if __name__ == "__main__":
    main()
