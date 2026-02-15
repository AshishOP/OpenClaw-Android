#!/usr/bin/env python3
"""
boot.py — Resilient Boot Shim (v2.0 - Public)
==============================================
INVARIANT: Uses ONLY Python stdlib. This is the recovery layer.
If the SDK is broken, this script must still function.

Usage:
    python3 scripts/boot.py
"""

import os
import sys
from pathlib import Path

# === STDLIB-ONLY SECTION ===
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SDK_PATH = PROJECT_ROOT / "src"


def recovery_shell():
    """
    Emergency Recovery Shell — runs when SDK import fails.
    Uses ONLY stdlib to provide recovery options.
    """
    print("\n" + "=" * 60)
    print("🚨 ATHENA RECOVERY SHELL")
    print("=" * 60)
    print("The SDK failed to load. Choose a recovery action:\n")
    print("  [1] Re-install dependencies (pip install -e .)")
    print("  [2] Git reset to last commit (git checkout .)")
    print("  [3] Run safe_boot.sh (zero-dependency fallback)")
    print("  [4] Open Python REPL for manual debugging")
    print("  [5] Exit")
    print()

    try:
        choice = input("Enter choice [1-5]: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nExiting.")
        sys.exit(1)

    if choice == "1":
        print("\n🔧 Running: pip install -e .")
        os.system(f"cd {PROJECT_ROOT} && pip install -e .")
        print("\n✅ Done. Try running boot.py again.")
    elif choice == "2":
        print("\n⚠️  This will discard all uncommitted changes!")
        confirm = input("Are you sure? (y/N): ").strip().lower()
        if confirm == "y":
            os.system(f"cd {PROJECT_ROOT} && git checkout .")
            print("✅ Reset complete.")
        else:
            print("Aborted.")
    elif choice == "3":
        safe_boot = PROJECT_ROOT / "scripts" / "safe_boot.sh"
        if safe_boot.exists():
            print(f"\n🔧 Running: {safe_boot}")
            os.system(f"bash {safe_boot}")
        else:
            print("❌ safe_boot.sh not found.")
    elif choice == "4":
        print("\n🐍 Dropping into Python REPL. Use exit() to quit.")
        import code

        code.interact(local={"PROJECT_ROOT": PROJECT_ROOT, "Path": Path})
    else:
        print("Exiting.")
        sys.exit(0)

    sys.exit(0)


def main():
    """
    Main entry point. Attempts SDK boot, falls back to recovery shell.
    """
    # Ensure SDK is on path
    sys.path.insert(0, str(SDK_PATH))

    try:
        from athena import __version__
        from athena.core.config import get_project_root
    except ImportError as e:
        print(f"\n❌ SDK IMPORT FAILED: {e}")
        recovery_shell()
        return 1
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR DURING IMPORT: {e}")
        recovery_shell()
        return 1

    # SDK loaded successfully
    print("=" * 60)
    print("🏛️  ATHENA SDK BOOT CHECK")
    print("=" * 60)
    print(f"\n📦 SDK Version: {__version__}")

    root = get_project_root()
    print(f"📂 Project Root: {root}")

    # === Active Knowledge Injection ===
    knowledge_script = PROJECT_ROOT / "scripts" / "core" / "boot_knowledge.py"
    if knowledge_script.exists():
        import subprocess

        subprocess.run([sys.executable, str(knowledge_script)])
    # ===================================

    checks = [
        ("pyproject.toml", root / "pyproject.toml"),
        ("src/athena", root / "src" / "athena"),
        ("examples", root / "examples"),
    ]

    print("\n🔍 Directory Check:")
    all_ok = True
    for name, path in checks:
        exists = path.exists()
        status = "✅" if exists else "❌"
        print(f"   {status} {name}")
        if not exists:
            all_ok = False

    print("\n" + "=" * 60)
    if all_ok:
        print("✅ BOOT SUCCESS — Athena SDK is correctly installed")
    else:
        print("⚠️  PARTIAL BOOT — Some paths missing (may be normal)")
    print("=" * 60)

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
