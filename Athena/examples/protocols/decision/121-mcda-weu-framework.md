---
created: 2026-02-08
last_updated: 2026-02-08
graphrag_extracted: true
---

# Protocol 121: Decision Frameworks (MCDA / WEU / Pairwise)

> **Source**: Zero-Point Codex v3.0 / Few-shot v29
> **Domain**: Decision / Multi-Criteria Optimization
> **Priority**: ⭐⭐⭐ Critical

---

## 1. MCDA (Multi-Criteria Decision Analysis)

> **Definition**: A systematic process for evaluating multiple conflicting criteria in decision making. Used for "Exoskeleton" selection (IDEs), hardware purchases, or arena selection.

### The MCDA Process

1. **Define Goal**: "What is the single most important outcome?"
2. **Identify Options**: List at least 3 distinct paths.
3. **Define Criteria**: (e.g., Sovereignty, Intelligence, Speed, Cost).
4. **Weighting**: Assign importance to each criterion (Total = 100%).
5. **Scoring**: Rank options 1-10 for each criterion.
6. **Calculate**: `Weighted Score = Score * (Weight / 100)`.

---

## 2. Pairwise Comparison

> **Definition**: A method of comparing entities in pairs to judge which of each entity is preferred, or has a greater amount of some quantitative property.

### Use Case

When criteria are qualitative and difficult to weight linearly (e.g., "Aesthetics vs. Security").

**Mechanism**:

- Compare A vs B, B vs C, A vs C.
- Assign a winner to each.
- The option with the most "wins" is the prioritized choice.
- **Goal**: Resolves "Inconsistency" in complex weighting models.

---

## 3. WEU (Weighted Expected Utility)

> **Definition**: An extension of Expected Utility theory that accounts for subjective probability weighting and outcome utility.

### The Formula

`WEU = ∑ [ w(p_i) * u(x_i) ]`

- **w(p_i)**: Probability weighting function (accounts for human tendency to overweight low probabilities).
- **u(x_i)**: Utility of the outcome (accounts for Law #1: Risk of Ruin).

**Operational Implementation**:

- If any single `u(x_i) = -∞` (Ruin), the total `WEU` defaults to **-∞** regardless of probability.
- This is the mathematical enforcement of **Law #1**.

---

## 4. Decision Rule (The Solver)

1. **Run MCDA** to find the "Rational Best".
2. **Run Pairwise** to check for "Gut/Value" alignment.
3. **Run WEU** to ensure no outcome violates **Law #1**.
4. **Verdict**: The option that clears the WEU safety gate and leads the MCDA/Pairwise ranking.

---

## Tags

**Tags**: #protocol #decision #mcda #weu #pairwise #optimization #zero-point-codex
