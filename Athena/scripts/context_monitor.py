#!/usr/bin/env python3
"""
context_monitor.py — Session Hygiene
====================================
Monitors session entropy and triggers compression protocols.
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

try:
    from athena.sessions import get_current_session_path, read_session_log
except ImportError:
    # Fallback/Mock for standalone testing
    def get_current_session_path():
        return None

    def read_session_log(path):
        return ""


def count_turns(content: str) -> int:
    """Count turns based on '## Turn' or checkpoint markers."""
    return content.count("## Turn") or content.count("### [")  # Simple heuristic


def main():
    parser = argparse.ArgumentParser(description="Athena Context Monitor")
    parser.add_argument("--turn-count", type=int, help="Manual turn count for testing")
    parser.add_argument("--dry-run", action="store_true", help="Don't perform actions")
    args = parser.parse_args()

    session_path = get_current_session_path()
    if not session_path and not args.turn_count:
        print("No active session found.")
        return

    if args.turn_count:
        turns = args.turn_count
    else:
        content = read_session_log(session_path)
        turns = count_turns(content)

    print(f"📊 Session Hygiene: {turns} turns detected.")

    if turns >= 80:
        print(
            "\033[91m🚨 CRITICAL ENTROPY: Hard Archival required (Protocol 280).\033[0m"
        )
        print("Action: Move oldest blocks to .context/history/")
    elif turns >= 40:
        print("\033[93m⚠️  HIGH ENTROPY: Summary Injection recommended.\033[0m")
        print("Action: Compress previous 40 turns into a Context Injection block.")
    else:
        print("✅ Context status: Healthy.")


if __name__ == "__main__":
    main()
