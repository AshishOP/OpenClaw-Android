#!/usr/bin/env python3
"""
audit_velocity.py — The "Boredom Killswitch".
Tracks 'Outcome Velocity' aka THE SLOPE.

Logic:
    Slope = (Sum of Outcome Scores in last 7 days) / 7
    Target > 1.0 (At least 1 minor ship per day)
    
Usage:
    python3 audit_velocity.py
"""

import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONTEXT_DIR = PROJECT_ROOT / ".context"
OUTCOME_DB = CONTEXT_DIR / "outcomes.jsonl"

SCORES = {
    "SHIP": 5,
    "MERGE": 3,
    "DECIDE": 2,
    "META": 0.5
}

def calculate_slope(days=7):
    """Calculate average daily score velocity."""
    if not OUTCOME_DB.exists():
        return 0.0
        
    cutoff = datetime.now() - timedelta(days=days)
    total_score = 0.0
    
    try:
        with open(OUTCOME_DB, "r") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    ts = datetime.fromisoformat(entry["timestamp"])
                    if ts > cutoff:
                        total_score += entry["score"]
                except (ValueError, KeyError):
                    continue
    except Exception:
        return 0.0
        
    # Slope = Daily Average Score
    # e.g., if you shipped 2 big things (10pts) in 7 days = 1.4 slope
    slope = total_score / days
    return round(slope, 2)

def main():
    slope = calculate_slope(7)
    
    print(f"📊 Velocity Audit: 7-Day Outcome Slope")
    print(f"   Outcome Slope: {slope} points/day")
    
    if slope == 0.0:
        print("\n⚠️  WARNING: FLATLINE DETECTED (Slope 0.0)")
        print("   No shipping events in 7 days.")
        print("   ACTION: Immediate Execution Lock. You must SHIP or DECIDE today.")
    elif slope < 0.5:
        print("\n⚠️  WARNING: DIMINISHING RETURNS")
        print("   Slope is low (< 0.5). You are spinning.")
    else:
        print("\n✅ System Metabolic Status: HEALTHY")
        print("   You are shipping.")

if __name__ == "__main__":
    main()
