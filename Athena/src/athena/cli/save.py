#!/usr/bin/env python3
"""
athena.cli.save — Quicksave Session Checkpoint
================================================

Append a checkpoint to the current session log. This is the SDK equivalent
of the `quicksave.py` script.

Usage:
    python -m athena save "Brief summary of what happened"
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def find_current_session(logs_dir: Path) -> Optional[Path]:
    """Find the most recent session log for today."""
    today = datetime.now().strftime("%Y-%m-%d")
    sessions = sorted(logs_dir.glob(f"{today}-session-*.md"), reverse=True)
    return sessions[0] if sessions else None


def run_quicksave(summary: str, project_root: Optional[Path] = None) -> bool:
    """
    Append a checkpoint to the current session log.

    Args:
        summary: Brief description of the checkpoint.
        project_root: Project root directory (auto-detected if None).

    Returns:
        True if successful, False otherwise.
    """
    if project_root is None:
        # Auto-discover project root
        current = Path.cwd()
        for parent in [current] + list(current.parents):
            if (parent / ".athena_root").exists():
                project_root = parent
                break
            if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
                project_root = parent
                break
        else:
            project_root = current

    # Check multiple possible session log locations
    possible_dirs = [
        project_root / "session_logs",
        project_root / ".context" / "memories" / "session_logs",
    ]

    session_file = None
    for logs_dir in possible_dirs:
        if logs_dir.exists():
            session_file = find_current_session(logs_dir)
            if session_file:
                break

    if not session_file:
        print(f"⚠️ No session log found for today")
        print("   (Run /start or `python -m athena` first to create a session)")
        return False

    timestamp = datetime.now().strftime("%H:%M")
    checkpoint = f"\n\n### ⚡ Checkpoint [{timestamp}]\n{summary}\n"

    with open(session_file, "a") as f:
        f.write(checkpoint)

    print(f"✅ Quicksave [{timestamp}] → {session_file.name}")
    return True


if __name__ == "__main__":
    if len(sys.argv) > 1:
        msg = " ".join(sys.argv[1:])
        run_quicksave(msg)
    else:
        print("Usage: python -m athena save <summary>")
