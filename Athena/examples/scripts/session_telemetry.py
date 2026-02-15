#!/usr/bin/env python3
"""
Session Telemetry Tracker (v2.0 — Accurate Pricing)

Generates token usage statistics for the current session.
Uses Claude Opus 4.6 pricing as conservative baseline.

Pricing Source: https://docs.anthropic.com/en/docs/about-claude/pricing
- Claude Opus 4.6: $5/MTok input, $25/MTok output
- Claude Sonnet 4.5: $3/MTok input, $15/MTok output
- Claude Haiku 4.5: $1/MTok input, $5/MTok output

Note: Actual token counts require API access. This script estimates based on:
1. Session log file size (proxy for conversation length)
2. Typical input:output ratio (~4:1 for conversation flows)
3. Conservative multipliers for context window accumulation
"""

import os
import sys
import glob
import datetime

# Configuration
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SESSION_LOG_DIR = os.path.join(PROJECT_ROOT, ".context", "memories", "session_logs")
BOOT_FILE_PATH = os.path.join(PROJECT_ROOT, ".framework", "v7.0", "modules", "Core_Identity.md")

# ANSI Colors
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

# Pricing (USD per Million Tokens) — Claude Opus 4.6 as baseline
PRICING = {
    "opus_4.5": {"input": 5.00, "output": 25.00},
    "sonnet_4.5": {"input": 3.00, "output": 15.00},
    "haiku_4.5": {"input": 1.00, "output": 5.00},
    "gemini_2.5_pro": {"input": 1.25, "output": 10.00},  # For reference
}

# Default model for estimates
DEFAULT_MODEL = "opus_4.5"


def estimate_tokens(text):
    """
    Estimates token count.
    Uses tiktoken if available, otherwise ~4 chars per token approximation.
    """
    try:
        import tiktoken

        enc = tiktoken.encoding_for_model("gpt-4")
        return len(enc.encode(text))
    except ImportError:
        return len(text) // 4


def get_file_tokens(path):
    if not os.path.exists(path):
        return 0
    with open(path, "r", encoding="utf-8") as f:
        return estimate_tokens(f.read())


def get_latest_session_log():
    files = glob.glob(os.path.join(SESSION_LOG_DIR, "*.md"))
    if not files:
        return None
    return max(files, key=os.path.getctime)


def count_artifacts_created_today():
    """
    Count artifacts created today by checking file modification times.
    """
    today = datetime.date.today()
    artifact_dirs = [
        os.path.join(PROJECT_ROOT, ".context", "memories", "case_studies"),
        os.path.join(PROJECT_ROOT, ".context", "cases"),
        os.path.join(PROJECT_ROOT, ".agent", "skills", "protocols"),
        os.path.join(PROJECT_ROOT, ".context", "playbooks"),
        os.path.join(PROJECT_ROOT, ".context", "scenarios"),
    ]
    count = 0
    for dir_path in artifact_dirs:
        if os.path.exists(dir_path):
            for f in os.listdir(dir_path):
                fp = os.path.join(dir_path, f)
                if os.path.isfile(fp):
                    mtime = datetime.date.fromtimestamp(os.path.getmtime(fp))
                    if mtime == today:
                        count += 1
    return count


def detect_protocol_invocations(content):
    """
    Detect protocol invocations from session log content.
    """
    import re

    protocols = [
        "/ultrathink",
        "/think",
        "/needful",
        "/audit",
        "/search",
        "/research",
        "/graph",
        "/end",
        "/start",
    ]
    found = []
    for p in protocols:
        matches = re.findall(re.escape(p), content, re.IGNORECASE)
        if matches:
            found.append(f"{p} x{len(matches)}")
    return ", ".join(found) if found else "None"


def estimate_session_tokens(session_log_tokens, artifacts_created, protocols_invoked):
    """
    Estimate actual session token usage based on multiple signals.

    The session log is a COMPRESSED summary of the conversation.
    Actual conversation tokens are typically 10-50x larger because:
    - Full user messages (often include pasted articles, code, etc.)
    - Full AI responses (much longer than summary)
    - Context accumulation across turns

    Signals used:
    1. Session log size (base)
    2. Artifacts created (more artifacts = more complex session)
    3. Protocols invoked (deep work = more tokens)
    """
    # Base multiplier
    BASE_MULTIPLIER = 15

    # Adjust for session complexity
    if artifacts_created >= 3:
        complexity_bonus = 2.0  # Heavy session
    elif artifacts_created >= 1:
        complexity_bonus = 1.5  # Medium session
    else:
        complexity_bonus = 1.0  # Light session

    # Adjust for deep work protocols
    protocol_count = protocols_invoked.count("x") if protocols_invoked != "None" else 0
    if protocol_count >= 3:
        protocol_bonus = 1.5
    elif protocol_count >= 1:
        protocol_bonus = 1.2
    else:
        protocol_bonus = 1.0

    # Minimum floor based on typical session
    # User feedback: $1 is the MOST conservative for a real session
    # At Opus 4.6 ($5 in + $25 out), $1 = ~30K input + 7.5K output = ~$0.34
    # So we need ~80K input to hit ~$1 with output ratio
    MIN_INPUT_TOKENS = 80_000  # Produces ~$1 at Opus 4.6 rates

    # Calculate estimated input
    estimated_input = max(
        int(session_log_tokens * BASE_MULTIPLIER * complexity_bonus * protocol_bonus),
        MIN_INPUT_TOKENS,
    )

    # Output is typically 20-30% of input in a balanced conversation
    OUTPUT_RATIO = 0.25
    estimated_output = int(estimated_input * OUTPUT_RATIO)

    return estimated_input, estimated_output


def calculate_cost(input_tokens, output_tokens, model=DEFAULT_MODEL):
    """
    Calculate cost based on model pricing.
    """
    pricing = PRICING.get(model, PRICING[DEFAULT_MODEL])
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    return input_cost, output_cost, input_cost + output_cost


def main():
    # 1. Calculate Boot Load
    boot_tokens = get_file_tokens(BOOT_FILE_PATH)

    # 2. Get Current Session Log
    session_log_path = get_latest_session_log()
    if not session_log_path:
        print("No session log found.")
        sys.exit(1)

    session_filename = os.path.basename(session_log_path)
    session_log_tokens = get_file_tokens(session_log_path)

    # 3. Read session log for protocol detection
    with open(session_log_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 4. Count artifacts and protocols
    artifacts_created = count_artifacts_created_today()
    protocols_invoked = detect_protocol_invocations(content)

    # 5. Estimate actual session tokens (not just the log)
    estimated_input, estimated_output = estimate_session_tokens(
        session_log_tokens, artifacts_created, protocols_invoked
    )
    total_estimated = estimated_input + estimated_output

    # 6. Cost Estimation (Claude Opus 4.6 as baseline)
    input_cost, output_cost, total_cost = calculate_cost(
        estimated_input, estimated_output, DEFAULT_MODEL
    )

    # Calculate range (±30% for uncertainty)
    cost_low = total_cost * 0.7
    cost_high = total_cost * 1.5  # Heavy sessions can be 50% more

    # Also calculate for other models for comparison
    _, _, sonnet_cost = calculate_cost(estimated_input, estimated_output, "sonnet_4.5")
    _, _, haiku_cost = calculate_cost(estimated_input, estimated_output, "haiku_4.5")

    # Subscription ROI (Antigravity $20/month)
    subscription_cost = 20.00
    sessions_at_this_rate = int(subscription_cost / total_cost) if total_cost > 0 else 0

    markdown_block = f"""
## 📊 Session Telemetry (v2.0)

| Metric | Value | Note |
|:-------|------:|:-----|
| **Boot Load** | {boot_tokens:,} | Core Identity only |
| **Session Log Size** | {session_log_tokens:,} | Compressed summary |
| **Est. Input Tokens** | ~{estimated_input:,} | Full conversation context |
| **Est. Output Tokens** | ~{estimated_output:,} | AI responses (~25% of input) |
| **Total Est. Tokens** | ~{total_estimated:,} | Full session |
| **Artifacts Created** | {artifacts_created} | Files created today |
| **Protocols Invoked** | {protocols_invoked} | Deep work triggers |

### 💰 Cost Estimate (Opus 4.6 Baseline)

| Model | Estimate | Range |
|:------|:--------:|:-----:|
| **Claude Opus 4.6** | **${total_cost:.2f}** | ${cost_low:.2f} — ${cost_high:.2f} |
| Claude Sonnet 4.5 | ${sonnet_cost:.2f} | — |
| Claude Haiku 4.5 | ${haiku_cost:.2f} | — |

### 📈 Subscription ROI ($20/month Antigravity)

| Metric | Value |
|:-------|------:|
| **Sessions like this** | ~{sessions_at_this_rate} sessions/month |
| **Per-session target** | ${subscription_cost / 30:.2f}/session (to max 30 days) |

> ⚠️ Range accounts for session complexity variance. Heavy text dumps = higher end.
"""

    print(markdown_block)
    print(f"{GREEN}✓ Copy the block above and paste it into {session_filename}{RESET}")
    print(
        f"{YELLOW}Note: Estimates based on session complexity heuristics. Range = ±30-50%.{RESET}"
    )


if __name__ == "__main__":
    main()
