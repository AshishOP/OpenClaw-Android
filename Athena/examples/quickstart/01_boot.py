#!/usr/bin/env python3
"""
Athena Quickstart: Boot Demo
============================

This script demonstrates the basic SDK import and configuration.
Run it to verify your installation is working.

Usage:
    python examples/quickstart/01_boot.py
"""

import sys
from pathlib import Path

# Add src to path for development mode
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from athena import __version__
from athena.core.config import PROJECT_ROOT, get_project_root


def main():
    print("=" * 60)
    print("🏛️  ATHENA SDK BOOT CHECK")
    print("=" * 60)
    
    # Version
    print(f"\n📦 SDK Version: {__version__}")
    
    # Project root discovery
    root = get_project_root()
    print(f"📂 Project Root: {root}")
    
    # Check for key directories
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
    
    # Summary
    print("\n" + "=" * 60)
    if all_ok:
        print("✅ BOOT SUCCESS — Athena SDK is correctly installed")
    else:
        print("⚠️  PARTIAL BOOT — Some paths missing (may be normal)")
    print("=" * 60)
    
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
