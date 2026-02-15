"""
athena.boot.shutdown — Session Close & Save
============================================

Handles the /end workflow:
1. Find current session log
2. Add closing timestamp
3. Update session status to "Closed"
4. Optionally trigger Supabase sync

Usage:
    from athena.boot.shutdown import run_shutdown
    run_shutdown()
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional


def find_current_session(logs_dir: Path) -> Optional[Path]:
    """Find the most recent session log for today."""
    today = datetime.now().strftime("%Y-%m-%d")
    sessions = sorted(logs_dir.glob(f"{today}-session-*.md"), reverse=True)
    return sessions[0] if sessions else None


def close_session(session_file: Path) -> bool:
    """
    Close a session log by updating its status and adding end timestamp.

    Returns True if successful.
    """
    if not session_file.exists():
        print(f"❌ Session file not found: {session_file}")
        return False

    content = session_file.read_text()
    now = datetime.now()

    # Update status
    if "> **Status**: Active" in content:
        content = content.replace(
            "> **Status**: Active", f"> **Status**: Closed ({now.strftime('%H:%M')})"
        )

    # Add closing section if not present
    if "## Session Closed" not in content:
        content += f"""

---

## Session Closed

**End Time**: {now.strftime("%Y-%m-%d %H:%M")}
**Duration**: (calculated by user)

### Key Takeaways
-

### Deferred to Next Session
-
"""

    session_file.write_text(content)
    print(f"✅ Session closed: {session_file.name}")
    return True


def run_shutdown(project_root: Optional[Path] = None) -> bool:
    """
    Execute the full shutdown sequence.

    1. Find current session
    2. Close it
    3. (Optional) Sync to Supabase

    Returns True if successful.
    """
    if project_root is None:
        # Auto-discover project root
        current = Path.cwd()
        for parent in [current] + list(current.parents):
            if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
                project_root = parent
                break
        else:
            project_root = current

    print("━" * 60)
    print("🔚 ATHENA SHUTDOWN SEQUENCE")
    print("━" * 60)

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
        print("⚠️  No active session found for today")
        print("   (Run /start first to create a session)")
        return True  # Not an error, just no session

    # Close the session
    success = close_session(session_file)

    if success:
        # Optional: Trigger Supabase sync if configured
        supabase_url = os.getenv("SUPABASE_URL")
        if supabase_url:
            print("🔄 Supabase sync available (run manually: python -m athena.memory.sync)")

        print("━" * 60)
        print("✅ ATHENA SHUTDOWN COMPLETE")
        print("━" * 60)

    return success


if __name__ == "__main__":
    run_shutdown()
