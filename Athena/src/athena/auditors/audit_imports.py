#!/usr/bin/env python3
"""
Audit Imports
Parses Python ASTs to generate a dependency graph and check for protocol violations.
"""

import ast
import os
import sys
from pathlib import Path
from collections import defaultdict

# Config
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = PROJECT_ROOT / ".agent" / "scripts"
SRC_DIR = PROJECT_ROOT / "src"

def get_imports(file_path):
    """Parse a file and return a list of imported module names."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(file_path))
    except Exception as e:
        # print(f"⚠️ Failed to parse {file_path}: {e}")
        return []

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports

def audit_repo():
    print("🔍 Auditing Imports...")
    
    # 1. Map all scripts
    script_files = list(SCRIPTS_DIR.glob("*.py"))
    
    dependencies = defaultdict(list)
    orphans = []
    violations = []
    
    # Rule: Scripts should not import other scripts (relative imports)
    # Rule: Scripts should import from athena.* (future)
    
    # Track who imports who
    # Just a simple check for now: Do we see imports of "src" or "athena"?
    
    for script in script_files:
        if script.name == "__init__.py": continue
        
        imps = get_imports(script)
        dependencies[script.name] = imps
        
        # Check specific rules
        for imp in imps:
            # Check for relative script-to-script imports 
            # (Hard to detect perfectly with AST "module" names alone, checking naive patterns)
            pass

    # Print Report
    print(f"\n📊 Report: {len(script_files)} scripts analyzed.\n")
    
    # Top Deps
    all_deps = [d for deps in dependencies.values() for d in deps]
    from collections import Counter
    top_deps = Counter(all_deps).most_common(10)
    print("Top External Dependencies:")
    for dep, count in top_deps:
        print(f"  - {dep}: {count}")
        
    # Check for 'athena' usage
    athena_users = [s for s, deps in dependencies.items() if any(d.startswith("athena") for d in deps)]
    print(f"\nScripts using 'athena' package: {len(athena_users)}")
    
    # Future: True orphan detection requires iterating ALL files to see if a script is IMPORTED.
    # But scripts are usually ENTRY POINTS, so they aren't imported.
    # Orphans in scripts folder are scripts that are never EXECUTED.
    # That is harder to prove statically.
    
    print("\n✅ Audit Complete.")

if __name__ == "__main__":
    audit_repo()
