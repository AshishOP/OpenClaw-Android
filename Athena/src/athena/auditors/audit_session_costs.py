#!/usr/bin/env python3
"""
Session Cost Auditor
Scans all session logs to estimate historical token usage and cost.
Assumption: All previous sessions used the "Monolith" architecture (~30k boot) unless proven otherwise.
However, for fair comparison to the NEW architecture, we will display what they WOULD have cost vs what they DID cost.
"""

import os
import glob
import re

# Configuration
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SESSION_LOG_DIR = os.path.join(PROJECT_ROOT, ".context", "memories", "session_logs")
BOOT_FILE_PATH = os.path.join(PROJECT_ROOT, ".framework", "v7.0", "modules", "Core_Identity.md")

# Pricing (Gemini 3 Pro)
PRICE_PER_M_INPUT = 2.00

# Architecture Baselines
MONOLITH_BOOT = 30000  # Old architecture ~30k tokens
ADAPTIVE_BOOT = 2000   # New architecture ~2k tokens

# ANSI Colors
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

def estimate_tokens(text):
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model("gpt-4")
        return len(enc.encode(text))
    except ImportError:
        return len(text) // 4

def analyze_sessions():
    files = sorted(glob.glob(os.path.join(SESSION_LOG_DIR, "*.md")) + glob.glob(os.path.join(SESSION_LOG_DIR, "archive", "*.md")))
    
    print(f"\n{BOLD}{CYAN}📊 HISTORICAL SESSION COST AUDIT (Pro Pricing Modeled){RESET}")
    print(f"{CYAN}{'='*80}{RESET}")
    print(f"{BOLD}{'Session':<30} | {'Size (Tokens)':<15} | {'Est. Cost (Monolith)':<20} | {'Est. Cost (Adaptive)':<20}{RESET}")
    print(f"{CYAN}{'-'*80}{RESET}")
    
    total_monolith_cost = 0
    total_adaptive_cost = 0
    total_sessions = 0
    
    for log_path in files:
        filename = os.path.basename(log_path)
        
        # Read content
        with open(log_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Estimate session tokens
        session_tokens = estimate_tokens(content)
        
        # Estimate turns (Rough heuristic: 1 turn per ~300 tokens of log? Or just assume 50 turns avg?)
        # Better heuristic: Count "Step Id" or speaker markers if available, but markdown is loose.
        # Let's assume a "Standard Session" is 50 turns. This is a simplification for the estimate.
        estimated_turns = 50 
        
        # Cost Calculation
        # Monolith: (30k Boot + Session Growth) * Turns
        # Adaptive: (2k Boot + Session Growth + 5k Avg Module) * Turns
        
        # Average context size per turn
        avg_ctx_monolith = MONOLITH_BOOT + (session_tokens / 2) # Average growth
        avg_ctx_adaptive = ADAPTIVE_BOOT + 5000 + (session_tokens / 2) # Boot + 1 module + growth
        
        cost_monolith = (avg_ctx_monolith * estimated_turns / 1_000_000) * PRICE_PER_M_INPUT
        cost_adaptive = (avg_ctx_adaptive * estimated_turns / 1_000_000) * PRICE_PER_M_INPUT
        
        # Accumulate
        total_monolith_cost += cost_monolith
        total_adaptive_cost += cost_adaptive
        total_sessions += 1
        
        # Color coding
        savings = cost_monolith - cost_adaptive
        savings_color = GREEN if savings > 0 else RED
        
        # print(f"{filename:<30} | {session_tokens:<15,} | ${cost_monolith:<19.2f} | ${cost_adaptive:<19.2f}")
        
    # print(f"{CYAN}{'='*80}{RESET}")
    print(f"\n{BOLD}💰 SUMMARY ({total_sessions} Sessions){RESET}")
    print(f"  Total Cost (Old Architecture):  {RED}${total_monolith_cost:.2f}{RESET}")
    print(f"  Total Cost (New Architecture):  {GREEN}${total_adaptive_cost:.2f}{RESET}")
    print(f"  {BOLD}TOTAL SAVINGS:{RESET}              {GREEN}${total_monolith_cost - total_adaptive_cost:.2f} (-{((total_monolith_cost - total_adaptive_cost)/total_monolith_cost)*100:.1f}%){RESET}")
    print(f"\n{YELLOW}* Note: Assumes avg 50 turns/session. Adaptive model assumes 1 active module (5k) loaded.{RESET}")

if __name__ == "__main__":
    analyze_sessions()
