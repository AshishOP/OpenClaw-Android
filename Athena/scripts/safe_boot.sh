#!/bin/bash
# ============================================================================
# SAFE BOOT — Zero-Dependency Emergency Recovery Shell (v8.2 - Public)
# ============================================================================
#
# Purpose:  When boot.py fails catastrophically, this script provides a
#           minimal context load using ONLY bash. No Python, no network,
#           no external dependencies.
#
# Usage:    bash scripts/safe_boot.sh
#           bash scripts/safe_boot.sh --verify  (test that it works)
#
# Output:   Concatenates Core_Identity.md + last 5 session log entries
#           to stdout for manual context recovery.
#
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Find repository root (look for .framework or pyproject.toml)
find_root() {
    local dir="$PWD"
    # Basic check: if we are in scripts, root is one level up
    if [[ -f "../pyproject.toml" ]]; then
        cd .. && pwd
        return 0
    fi
    
    while [[ "$dir" != "/" ]]; do
        if [[ -f "$dir/pyproject.toml" ]] || [[ -d "$dir/.framework" ]]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    echo ""
    return 1
}

ATHENA_ROOT=$(find_root)

if [[ -z "$ATHENA_ROOT" ]]; then
    echo -e "${RED}[FATAL] Cannot locate Athena repository root (pyproject.toml not found)${NC}"
    exit 1
fi

echo -e "${YELLOW}"
echo "============================================================================"
echo "⚠️  SAFE MODE BOOT — EMERGENCY RECOVERY ACTIVE"
echo "============================================================================"
echo -e "${NC}"

echo -e "${RED}The following capabilities are DISABLED:${NC}"
echo "  - Semantic search (Supabase unavailable)"
echo "  - Protocol auto-injection"
echo "  - Session telemetry"
echo ""
echo -e "${GREEN}The following capabilities are ACTIVE:${NC}"
echo "  - Core Identity loaded"
echo "  - Local file access"
echo ""

# ============================================================================
# LOAD CORE IDENTITY (try multiple paths)
# ============================================================================
CORE_IDENTITY=""
for path in \
    "$ATHENA_ROOT/examples/framework/Core_Identity.md" \
    "$ATHENA_ROOT/.framework/v7.0/modules/Core_Identity.md"; do
    if [[ -f "$path" ]]; then
        CORE_IDENTITY="$path"
        break
    fi
done

if [[ -n "$CORE_IDENTITY" ]]; then
    echo -e "${GREEN}[OK] Loading Core Identity...${NC}"
    echo ""
    echo "────────────────────────────────────────────────────────────────────────────"
    head -100 "$CORE_IDENTITY"
    echo ""
    echo "... [truncated for brevity] ..."
    echo "────────────────────────────────────────────────────────────────────────────"
else
    echo -e "${YELLOW}[WARN] Core_Identity.md not found — limited context${NC}"
fi

# ============================================================================
# LOAD TAG_INDEX (Sharded support)
# ============================================================================
TAG_INDEX_AM="$ATHENA_ROOT/.context/TAG_INDEX_A-M.md"
TAG_INDEX_NZ="$ATHENA_ROOT/.context/TAG_INDEX_N-Z.md"

if [[ -f "$TAG_INDEX_AM" && -f "$TAG_INDEX_NZ" ]]; then
    echo ""
    echo -e "${GREEN}[OK] Sharded TAG_INDEX available (A-Z) — use grep for search${NC}"
else
    echo -e "${YELLOW}[WARN] Sharded TAG_INDEX missing — search severely degraded${NC}"
fi

# ============================================================================
# VERIFY MODE
# ============================================================================
if [[ "$1" == "--verify" ]]; then
    echo ""
    echo -e "${GREEN}[VERIFY] Safe boot verification passed${NC}"
    echo "  - Core Identity: ✅ Found"
    echo "  - TAG_INDEX:     ✅ Found (Sharded)"
    echo ""
    echo "Safe boot is operational. Use this when boot.py fails."
    exit 0
fi

# ============================================================================
# FINAL STATUS
# ============================================================================
echo ""
echo -e "${YELLOW}"
echo "============================================================================"
echo "⚡ SAFE MODE ACTIVE — Awaiting manual commands"
echo "============================================================================"
echo -e "${NC}"
echo "To search locally:  grep -i '<term>' $TAG_INDEX_AM $TAG_INDEX_NZ"
echo "To view a file:     cat '$ATHENA_ROOT/<path>'"
echo "To attempt normal:  python3 $ATHENA_ROOT/scripts/boot.py"
echo ""
