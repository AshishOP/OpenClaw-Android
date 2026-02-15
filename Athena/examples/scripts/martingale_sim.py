#!/usr/bin/env python3
"""
Martingale Strategy Simulation (Blackjack Approximation)
======================================================
Parameters:
- Initial Bankroll: $100
- Base Bet: $0.10
- Strategy: 5-step Martingale (0.10 -> 0.20 -> 0.40 -> 0.80 -> 1.60 -> Reset)
- Win Probability: 49.5% (approximate even-money win rate excluding ties)
- Volume: 3000 hands (1 month @ 100 hands/day)
- Simulations: 100,000
"""

import random
import statistics
import sys
import time


def run_simulation(num_runs=10000, max_hands=3000, start_bankroll=100.0):
    # Configuration
    base_bet = 0.10
    multipliers = [1, 2, 4, 8, 16]  # 0.10, 0.20, 0.40, 0.80, 1.60
    bets = [base_bet * m for m in multipliers]
    max_step = len(bets) - 1
    win_prob = 0.495

    # Statistics storage
    end_bankrolls = []
    ruin_count = 0
    min_bankrolls = []

    start_time = time.time()

    print(f"Running {num_runs} simulations...")
    print(f"Parameters: Bankroll=${start_bankroll}, Hands={max_hands}, WinRate={win_prob:.1%}")
    print("-" * 50)

    for i in range(num_runs):
        bankroll = start_bankroll
        current_step = 0
        min_b = bankroll
        ruined = False

        for _ in range(max_hands):
            # Check if we can afford the current bet
            current_bet = bets[current_step]
            if bankroll < current_bet:
                ruined = True
                break

            # Simulate hand
            # simplified: ignores Blackjack payouts and splits/doubles variance
            # treats it as a binary outcome 1:1 bet
            if random.random() < win_prob:
                bankroll += current_bet
                current_step = 0  # Reset on win
            else:
                bankroll -= current_bet
                if current_step < max_step:
                    current_step += 1
                else:
                    current_step = 0  # Reset after hitting max step loss (Stop Loss)

            if bankroll < min_b:
                min_b = bankroll

            if bankroll <= 0:
                ruined = True
                break

        if ruined:
            ruin_count += 1
            # If ruined, we record 0 or actual remaining dust
            end_bankrolls.append(max(0, bankroll))
        else:
            end_bankrolls.append(bankroll)

        min_bankrolls.append(min_b)

        if (i + 1) % 20000 == 0:
            print(f"Completed {i + 1} runs...")

    duration = time.time() - start_time

    # Analysis
    avg_end = statistics.mean(end_bankrolls)
    median_end = statistics.median(end_bankrolls)
    ror = (ruin_count / num_runs) * 100

    # Sort for percentiles
    sorted_ends = sorted(end_bankrolls)
    worst_1_percent = sorted_ends[int(num_runs * 0.01)]
    worst_5_percent = sorted_ends[int(num_runs * 0.05)]
    best_1_percent = sorted_ends[int(num_runs * 0.99)]

    print("=" * 50)
    print("SIMULATION RESULTS")
    print("=" * 50)
    print(f"Risk of Ruin (RoR): {ror:.2f}%")
    print(f"Survival Rate:      {100 - ror:.2f}%")
    print("-" * 50)
    print(f"Expected Value (Mean):   ${avg_end:.2f} ({avg_end - start_bankroll:+.2f})")
    print(f"Median Result:           ${median_end:.2f} ({median_end - start_bankroll:+.2f})")
    print("-" * 50)
    print("Outcomes Distribution:")
    print(f"Worst 1% Case:    ${worst_1_percent:.2f}")
    print(f"Worst 5% Case:    ${worst_5_percent:.2f}")
    print(f"Best 1% Case:     ${best_1_percent:.2f}")
    print(f"Max Drawdown (Avg): ${start_bankroll - statistics.mean(min_bankrolls):.2f}")
    print("=" * 50)
    print(f"Time taken: {duration:.2f}s")


if __name__ == "__main__":
    run_simulation()
