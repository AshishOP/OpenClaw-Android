#!/usr/bin/env python3
"""
quicksave.py — SDK Shim
========================
Saves a checkpoint to the current session log via athena.sessions.
"""

import sys
import argparse
from pathlib import Path

from lib.shared_utils import setup_paths, log_violation

setup_paths()

from athena.sessions import append_checkpoint, log_to_decision_ledger
from athena.core.governance import get_governance


def main():
    parser = argparse.ArgumentParser(description="Athena Quicksave (SDK Shim)")
    parser.add_argument("summary", help="Summary of activity")
    parser.add_argument("--bullets", nargs="+", help="Optional bullet points")
    parser.add_argument(
        "--decision", action="store_true", help="Log to decision ledger too"
    )
    args = parser.parse_args()

    # Governance: Check if Triple-Lock protocol was followed
    gov = get_governance()
    semantic = gov._state.get("semantic_search_performed", False)
    web = gov._state.get("web_search_performed", False)

    if not (semantic and web):
        missing = []
        if not semantic:
            missing.append("Semantic Search")
        if not web:
            missing.append("Web Research")

        print(
            f"\033[91m⚠️  TRIPLE-LOCK VIOLATION: Quicksave initiated. Missing: {', '.join(missing)}.\033[0m"
        )
        # Log violation via shared util
        log_violation(
            "triple_lock", f"Quicksave triggered. Missing: {', '.join(missing)}"
        )

    # === NEW: Protocol 416 (Promise Gate) ===
    # Check if the summary contains promise triggers ("I will...", "Noted")
    # and if so, verify files were actually changed.
    script_dir = Path(__file__).parent
    verifier = script_dir / "verify_promises.py"

    if verifier.exists():
        import subprocess

        # We pass the summary to the verifier as the "response text"
        # Since quicksave summary is effectively the agent's statement of intent/action.
        res = subprocess.run(
            [sys.executable, str(verifier), args.summary],
            capture_output=True,
            text=True,
        )

        if res.returncode != 0:
            print(f"\n{res.stdout}")  # Print the specific violation message
            print(
                f"\033[91m❌ QUICKSAVE BLOCKED: Promise Violation (Protocol 416).\033[0m"
            )
            print("You promised an action in the summary but no files were changed.")
            sys.exit(1)
        elif res.stdout and "✅" in res.stdout:
            print(res.stdout.strip())

    # === NEW: Protocol 168 (Context Hygiene) ===
    # Monitor session entropy and print warnings if limits reached.
    monitor = script_dir / "context_monitor.py"
    if monitor.exists():
        import subprocess

        subprocess.run([sys.executable, str(monitor)])
    # ==========================================

    gov.verify_exchange_integrity()  # Resets state regardless of result

    try:
        log_path = append_checkpoint(args.summary, args.bullets)
        print(f"✅ Quicksave → {log_path.name}")

        if args.decision or "[CIRCUIT" in args.summary:
            log_to_decision_ledger(args.summary)
            print("⚖️  Decision logged to ledger.")

    except Exception as e:
        print(f"❌ Quicksave failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
