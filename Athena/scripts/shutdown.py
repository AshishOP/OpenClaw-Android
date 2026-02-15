#!/usr/bin/env python3
"""
shutdown.py — Session Finalization (v1.0 Public)
=================================================
Cleans up session state and updates workspace indexes.

Usage:
    python3 scripts/shutdown.py
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts" / "core"


def main():
    print("=" * 60)
    print("🌙 ATHENA SHUTDOWN SEQUENCE")
    print("=" * 60)

    # Phase 1: Update Workspace Indexes
    print("\n🗺️ Syncing Workspace Maps...")
    indexer = SCRIPTS_DIR / "index_workspace.py"
    if indexer.exists():
        subprocess.run([sys.executable, str(indexer)], check=False)
    else:
        print("⚠️ index_workspace.py not found. Skipping.")

    # Phase 2: Git Commit (Optional)
    print("\n📝 Session shutdown complete.")
    print("=" * 60)
    print("✅ Athena has gracefully shut down. See you next session!")
    print("=" * 60)


if __name__ == "__main__":
    main()
