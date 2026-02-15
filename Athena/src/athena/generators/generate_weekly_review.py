#!/usr/bin/env python3
"""
Weekly Outcome Review (The Pulse)
=================================
Generates a summary of all SHIP/MERGE/DECIDE actions in the last 7 days.
Calculates the definitive 'Weekly Slope'.

Usage:
  python3 generate_weekly_review.py
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONTEXT_DIR = PROJECT_ROOT / ".context"
OUTCOME_DB = CONTEXT_DIR / "outcomes.jsonl"

def main():
    if not OUTCOME_DB.exists():
        print("No outcomes logged yet.")
        return

    now = datetime.now()
    cutoff = now - timedelta(days=7)
    
    events = []
    total_score = 0
    ship_count = 0
    meta_count = 0
    
    with open(OUTCOME_DB, "r") as f:
        for line in f:
            try:
                entry = json.loads(line)
                ts = datetime.fromisoformat(entry["timestamp"])
                if ts >= cutoff:
                    events.append(entry)
                    total_score += entry["score"]
                    
                    if entry["type"] == "SHIP":
                        ship_count += 1
                    elif entry["type"] == "META":
                        meta_count += 1
            except:
                continue

    # Analysis
    if not events:
        print("⚠️  No activity in last 7 days. Slope: 0.0")
        return

    # Sort high impact first
    events.sort(key=lambda x: x["score"], reverse=True)
    
    print(f"📊 WEEKLY OUTCOME REVIEW ({cutoff.strftime('%Y-%m-%d')} - {now.strftime('%Y-%m-%d')})")
    print(f"============================================================")
    print(f"🔥 Velocity Score: {round(total_score, 1)} points")
    print(f"📈 Daily Slope:    {round(total_score/7, 2)}")
    print(f"🚢 Total Ships:    {ship_count}")
    print(f"🔧 Meta Ratio:     {round(meta_count / len(events), 2) if events else 0}")
    print(f"============================================================")
    print("\n🏆 HIGHLIGHT REEL (Top Impacts):")
    
    for e in events[:5]: # Top 5
        print(f"   • [{e['type']}] (+{e['score']}) {e['description']}")
        
    print("\n📉 The Grind (Recent):")
    for e in events[-3:]: # Last 3 checks
        print(f"   • {e['timestamp'][:16]} [{e['type']}] {e['description']}")

if __name__ == "__main__":
    main()
