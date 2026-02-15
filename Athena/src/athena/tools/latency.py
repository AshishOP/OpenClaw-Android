"""
athena.tools.latency
====================

Network health monitoring and latency indicators.
"""
import time
import requests
import sys

def check_gemini_latency() -> float:
    """
    Measure latency to Google Gemini API endpoint.
    Returns seconds (float). Returns -1.0 on error.
    """
    url = "https://generativelanguage.googleapis.com"
    try:
        start = time.time()
        # Just a HEAD request or GET to root
        requests.get(url, timeout=5)
        return time.time() - start
    except Exception:
        return -1.0

def main():
    latency = check_gemini_latency()
    
    if latency < 0:
        status = "🔴 OFFLINE"
        color = "\033[91m"
    elif latency < 0.2:
        status = "🟢 ULTRA-FAST"
        color = "\033[92m"
    elif latency < 0.8:
        status = "🟢 FAST" 
        color = "\033[92m"
    elif latency < 2.0:
        status = "🟡 SLOW"
        color = "\033[93m"
    else:
        status = "🔴 LAG" 
        color = "\033[91m"
        
    reset = "\033[0m"
    print(f"Network Latency: {color}{status} ({latency*1000:.0f}ms){reset}")

if __name__ == "__main__":
    main()
