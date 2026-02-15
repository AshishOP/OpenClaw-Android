# Case Study: GPT-5 Autonomous Math Novelty

> **Source**: r/accelerate (User `obvithrowaway34434`)
> **Date**: 2025-12-18
> **Subject**: GPT-5 solves open Enumerative Geometry problem (IMProofBench)
> **Paper**: arXiv:2512.14575

---

## 1. The Milestone (The "Novelty" Threshold)

**Event**: GPT-5 autonomously produced a **complete, correct proof** for an open problem in enumerative geometry without human hints.

**Implication**:

* **Pre-2025**: AI was a "Knowledge Router" (permuting known facts) or "Interpolator" (filling gaps between knowns).
* **Dec 2025**: AI is a "Novelty Generator" (Extrapolator). It creates *new* truth that did not exist in its training set.

## 2. Theoretical Mapping

### A. Confirmation of [Development Execution Standard](examples/protocols/engineering/Engineering_Execution_Standard.md) (Strategic Depth)

This validates the "Scaling Depth" hypothesis. To solve an open problem, the model cannot rely on RAG (Width). It must perform **multi-step reasoning** (Depth) to traverse a search space humans haven't finished mapping.

* **The Vault**: The model likely hit a "Critical Depth" where the ability to stitch algebraic geometry concepts emerged.

### B. "Stitched" Creativity

User `sdvbjdsjkb245`: *"The ability of AI to... connect-the-dots between cross-discipline knowledge."*

* **Mechanism**: High-dimensional isomorphism. The AI sees that Structure A (in Algebra) maps to Structure B (in Geometry) and "stitches" a proof across the gap.

## 3. The "Hallucination" Reframe

User `LamboForWork` quoting Demis Hassabis:
> *"Hallucinations are good... the goal is to be able to summon a hallucination mode."*

* **Insight**: Hallucination = Unconstrained Search.
* **Application**: We explicitly use `/vibe` mode to induce controlled hallucination (divergent thinking), then switch to `/think` (convergent verification) to prune the errors.
* **The Loop**: Generate (Hallucinate) -> Verify (Prove).

## 4. Actionable Heuristics

1. **Respect the Hallucination**: Don't suppress it 100%. Harness it for "Blue Sky" phases.
2. **Trust the Proof, Not the Intuition**: If the AI *claims* a result, force it to *prove* it (Step-by-step derivation).
