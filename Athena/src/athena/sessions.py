"""
athena.sessions
===============

Unified session lifecycle and checkpointing logic.
"""

import re
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any

from athena.core.config import get_current_session_log, CONTEXT_DIR, SESSIONS_DIR


def parse_yaml_frontmatter(content: str) -> tuple[Dict[str, Any], int]:
    """Extract YAML frontmatter from session log. Returns (metadata, body_start_index)."""
    import yaml

    match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not match:
        return {}, 0

    yaml_content = match.group(1)
    body_start = match.end()

    try:
        metadata = yaml.safe_load(yaml_content)
        return metadata or {}, body_start
    except Exception:
        # Fallback: simple key-value parsing
        metadata = {}
        for line in yaml_content.split("\n"):
            if ":" in line:
                key, _, value = line.partition(":")
                key = key.strip()
                value = value.strip()
                if value and value != "null":
                    metadata[key] = value
        return metadata, body_start


def recall_last_session() -> Optional[Path]:
    """
    Find and return the most recent session log file.
    """
    return get_current_session_log()


def get_next_session_number() -> int:
    """Find the highest session number for today and return the next one."""
    today = datetime.now().strftime("%Y-%m-%d")

    if not SESSIONS_DIR.exists():
        return 1

    pattern = re.compile(rf"^{today}-session-(\d{{2,3}})\.md$")
    max_session = 0
    for file in SESSIONS_DIR.iterdir():
        match = pattern.match(file.name)
        if match:
            max_session = max(max_session, int(match.group(1)))

    return max_session + 1


def update_forward_lineage(prev_session_id: str, current_session_id: str):
    """Update the previous session's YAML to point to the current session."""
    if not prev_session_id:
        return

    filename = f"{prev_session_id}.md"
    filepath = SESSIONS_DIR / filename

    if not filepath.exists():
        # Check archive (if it exists)
        archive_path = SESSIONS_DIR / "archive" / filename
        if archive_path.exists():
            filepath = archive_path

    if not filepath.exists():
        return

    try:
        content = filepath.read_text(encoding="utf-8")
        pattern = r"^(next_session:\s*)(null|~)?\s*$"
        replacement = f"\\1{current_session_id}"
        new_content, count = re.subn(
            pattern, replacement, content, count=1, flags=re.MULTILINE
        )

        if count > 0:
            filepath.write_text(new_content, encoding="utf-8")
    except Exception:
        pass


def create_session() -> Path:
    """Create a new session log with template. Returns the Path to the new session."""
    today = datetime.now().strftime("%Y-%m-%d")
    time_iso = datetime.now().astimezone().isoformat()
    time_display = datetime.now().strftime("%H:%M")
    session_num = get_next_session_number()

    session_id = f"{today}-session-{session_num:02d}"
    filename = f"{session_id}.md"
    filepath = SESSIONS_DIR / filename

    prev_session_log = get_current_session_log()
    prev_session_id = prev_session_log.stem if prev_session_log else None
    prev_link = f"← {prev_session_id}" if prev_session_id else "None"

    template = f"""---
session_id: {session_id}
date: {today}
start: {time_iso}
end:
duration_min:
status: in_progress
verdict:
prev_session: {prev_session_id if prev_session_id else "null"}
next_session:
focus:
threads: []
tags: []
lambda_peak:
lambda_total:
lambda_coverage:
lambda_coverage_n:
lambda_coverage_d:
---

# Session Log: {today} (Session {session_num:02d})

**Date**: {today}
**Time**: {time_display} - ...
**Focus**: ...
**Related Sessions**: {prev_link}

---

## 0. R__ Compressed Context

> Auto-generated on close by `shutdown.py`. Do not manually edit.

```text
[[ R__ |
@focus:
@status:
@decided:
@pending:
@artifacts:
@lambda_peak:
@tags:
]]
```

---

## 1. Checkpoints

> Automatically appended by `quicksave.py`. Do not manually write.

---

## 2. Key Decisions & Insights

- **Decision**: ...
- **Insight**: ...

---

## 2.5 Learnings (Compiler Inputs)

> Write explicitly. `shutdown.py` will ingest and propagate these.

### Learned (System / Workflow)

- [S] ...

### Learned (About User)

- [U] ...

### Integration Requested

- [X] ...

---

## 3. Action Items & Deferred

| ID | Action | Owner | Status | Thread |
|----|--------|-------|--------|--------|
| {session_id}-A1 | ... | AI / User | Pending | — |

---

## 4. Artifacts & Outputs

- **Created**: ...
- **Modified**: ...

---

## Session Closed

**Status**: ⏳ In Progress
**Time**: ...
**Verdict**: ... (🚀 SQUAD / ⚠️ Partial / 🔴 Blocked)

---

## Tagging

#session #...
"""

    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    filepath.write_text(template, encoding="utf-8")

    if prev_session_id:
        update_forward_lineage(prev_session_id, session_id)

    return filepath


# Common Pattern constants for extraction
PLACEHOLDER_PATTERNS = [
    "**Insight**: ...",
    "**Decision**: ...",
    "**Pattern**: ...",
    "TODO:",
    "PLACEHOLDER",
]


def extract_lambda_stats(content: str) -> dict:
    """Parse [Λ+XX] tags to compute cognitive load metrics."""
    matches = re.findall(r"\[Λ\+(\d+)\]", content)
    values = [int(v) for v in matches]

    # Identify checkpoint headers (supports '### ⚡ Checkpoint [time]' and '### [time] Checkpoint')
    checkpoint_headers = re.findall(
        r"### (⚡ )?\[?\d{2}:\d{2}\s?(SGT)?\]? Checkpoint|### (⚡ )?Checkpoint \[?\d{2}:\d{2}\s?(SGT)?\]?",
        content,
    )
    checkpoint_count = len(checkpoint_headers)

    if not values:
        return {
            "peak": 0,
            "total": 0,
            "coverage": f"0/{checkpoint_count}",
            "coverage_n": 0,
            "coverage_d": checkpoint_count,
        }

    return {
        "peak": max(values),
        "total": sum(values),
        "coverage": f"{len(values)}/{checkpoint_count}",
        "coverage_n": len(values),
        "coverage_d": checkpoint_count,
    }


def extract_learnings(content: str) -> tuple[List[str], List[str], List[str]]:
    """Extract [S], [U], [X] learnings from the session log."""
    system_learnings = []
    user_learnings = []
    integration_requests = []

    # Find Learnings section
    learnings_match = re.search(
        r"## 2\.5 Learnings.*?(?=\n## [^2]|\Z)", content, re.DOTALL
    )
    if not learnings_match:
        return [], [], []

    section = learnings_match.group(0)
    for match in re.findall(r"- \[S\]\s*(.+)", section):
        if match.strip() and match.strip() != "...":
            system_learnings.append(match.strip())

    for match in re.findall(r"- \[U\]\s*(.+)", section):
        if match.strip() and match.strip() != "...":
            user_learnings.append(match.strip())

    for match in re.findall(r"- \[X\]\s*(?!✅)(.+)", section):
        if match.strip() and match.strip() != "...":
            integration_requests.append(match.strip())

    return system_learnings, user_learnings, integration_requests


def append_checkpoint(
    summary: str, bullets: Optional[List[str]] = None, log_path: Optional[Path] = None
):
    """
    Append a checkpoint block to the session log.
    """
    if log_path is None:
        log_path = get_current_session_log()

    if not log_path or not log_path.exists():
        raise FileNotFoundError(f"Active session log not found at {log_path}")

    timestamp = datetime.now().strftime("%H:%M")
    checkpoint_block = f"\n### [{timestamp} SGT] Checkpoint\n\n**Summary**: {summary}\n"

    if bullets:
        checkpoint_block += "\n" + "\n".join([f"- {b}" for b in bullets]) + "\n"

    checkpoint_block += "\n---\n"

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(checkpoint_block)

    return log_path


def log_to_decision_ledger(summary: str, rationale: Optional[str] = None):
    """
    Log high-stakes decisions to DECISION_LOG.md.
    """
    ledger_path = CONTEXT_DIR / "DECISION_LOG.md"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    entry = f"\n## [{timestamp}] {summary}\n"
    if rationale:
        entry += f"**Rationale**: {rationale}\n"
    entry += "---\n"

    with open(ledger_path, "a", encoding="utf-8") as f:
        f.write(entry)


def update_session_metadata(
    new_tokens: int = 0,
    thread_id: Optional[str] = None,
    log_path: Optional[Path] = None,
):
    """
    Update YAML frontmatter in session log.
    """
    if log_path is None:
        log_path = get_current_session_log()

    if not log_path or not log_path.exists():
        return

    content = log_path.read_text(encoding="utf-8")

    # Simple YAML extraction (assumes it starts with ---)
    if content.startswith("---"):
        try:
            parts = content.split("---", 2)
            if len(parts) >= 3:
                import yaml

                frontmatter = yaml.safe_load(parts[1]) or {}

                # Update logic
                frontmatter["tokens"] = frontmatter.get("tokens", 0) + new_tokens
                if thread_id:
                    frontmatter["thread_id"] = thread_id

                new_content = "---\n" + yaml.dump(frontmatter) + "---\n" + parts[2]
                log_path.write_text(new_content, encoding="utf-8")
        except Exception:
            # Fallback if YAML is malformed
            pass
