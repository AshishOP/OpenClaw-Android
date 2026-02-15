#!/usr/bin/env python3
"""
athena.core.reasoning.got
==========================
Graph of Thoughts (GoT) implementation.

Based on: "Graph of Thoughts: Solving Elaborate Problems with Large Language Models"
         (Besta et al., ETH Zurich, 2023)

GoT extends Chain-of-Thought (CoT) and Tree-of-Thoughts (ToT) by modeling
thoughts as arbitrary Directed Acyclic Graphs (DAGs), enabling:
- Aggregation: N thoughts → 1 (consensus/synthesis)
- Refinement: Self-loops for iterative improvement
- Branching: 1 thought → N (exploration)

Key Insight: ToT is a special case of GoT (tree ⊂ DAG).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Any
from enum import Enum
from collections import defaultdict
import uuid


class ThoughtState(Enum):
    """Lifecycle state of a thought node."""

    PENDING = "pending"  # Not yet evaluated
    ACTIVE = "active"  # Currently being processed
    COMPLETED = "completed"  # Evaluation finished
    PRUNED = "pruned"  # Discarded (low score or dead end)


class TransformationType(Enum):
    """Types of thought transformations in GoT."""

    GENERATE = "generate"  # Create new thoughts from scratch or prompt
    AGGREGATE = "aggregate"  # Combine N thoughts → 1
    REFINE = "refine"  # Improve existing thought iteratively
    SCORE = "score"  # Evaluate thought quality


@dataclass
class Thought:
    """A single thought node in the graph."""

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    content: str = ""
    state: ThoughtState = ThoughtState.PENDING
    score: float = 0.0
    depth: int = 0
    metadata: dict = field(default_factory=dict)

    # Graph edges
    parents: list[str] = field(default_factory=list)  # Incoming edges
    children: list[str] = field(default_factory=list)  # Outgoing edges

    def __hash__(self):
        return hash(self.id)


@dataclass
class TransformResult:
    """Result of applying a transformation."""

    new_thoughts: list[Thought]
    aggregated_thought: Thought | None = None
    refined_thought: Thought | None = None


class GraphOfThoughts:
    """
    Graph of Thoughts orchestrator.

    The graph maintains thoughts as nodes and their dependencies as edges.
    Transformations modify the graph structure.

    Example Usage:
        got = GraphOfThoughts()

        # Generate initial thoughts
        initial = got.generate("What are the key components of a REST API?", n=3)

        # Aggregate into synthesis
        synthesis = got.aggregate([t.id for t in initial])

        # Refine the synthesis
        refined = got.refine(synthesis.id, iterations=2)
    """

    def __init__(
        self,
        generator: Callable[[str, int], list[str]] | None = None,
        aggregator: Callable[[list[str]], str] | None = None,
        refiner: Callable[[str], str] | None = None,
        scorer: Callable[[str], float] | None = None,
        max_depth: int = 10,
        min_score_threshold: float = 0.3,
    ):
        """
        Initialize GoT with optional custom transformation functions.

        Args:
            generator: (prompt, n) -> [n thoughts as strings]
            aggregator: ([thoughts]) -> aggregated string
            refiner: (thought) -> refined thought
            scorer: (thought) -> score 0.0-1.0
            max_depth: Maximum graph depth before forced termination
            min_score_threshold: Thoughts below this score are pruned
        """
        self.thoughts: dict[str, Thought] = {}
        self.root_ids: list[str] = []

        # Transformation functions (pluggable)
        self._generator = generator or self._default_generator
        self._aggregator = aggregator or self._default_aggregator
        self._refiner = refiner or self._default_refiner
        self._scorer = scorer or self._default_scorer

        # Config
        self.max_depth = max_depth
        self.min_score_threshold = min_score_threshold

        # Execution stats
        self.stats = {
            "thoughts_generated": 0,
            "thoughts_aggregated": 0,
            "thoughts_refined": 0,
            "thoughts_pruned": 0,
        }

    # ─────────────────────────────────────────────────────────────────────
    # Core Transformations
    # ─────────────────────────────────────────────────────────────────────

    def generate(
        self, prompt: str, n: int = 3, parent_id: str | None = None
    ) -> list[Thought]:
        """
        Generate n new thoughts from a prompt.

        This is the "branching" operation: 1 prompt → N thoughts.
        """
        parent_depth = self.thoughts[parent_id].depth if parent_id else -1
        new_depth = parent_depth + 1

        if new_depth > self.max_depth:
            return []  # Depth limit reached

        # Call generator
        raw_thoughts = self._generator(prompt, n)

        thoughts = []
        for content in raw_thoughts:
            thought = Thought(
                content=content,
                state=ThoughtState.COMPLETED,
                depth=new_depth,
                parents=[parent_id] if parent_id else [],
                metadata={"source": "generate", "prompt": prompt[:100]},
            )

            # Score the thought
            thought.score = self._scorer(content)

            # Prune if below threshold
            if thought.score < self.min_score_threshold:
                thought.state = ThoughtState.PRUNED
                self.stats["thoughts_pruned"] += 1

            self.thoughts[thought.id] = thought

            if parent_id:
                self.thoughts[parent_id].children.append(thought.id)
            else:
                self.root_ids.append(thought.id)

            thoughts.append(thought)

        self.stats["thoughts_generated"] += len(thoughts)
        return thoughts

    def aggregate(
        self, thought_ids: list[str], aggregation_prompt: str | None = None
    ) -> Thought:
        """
        Aggregate multiple thoughts into one.

        This is the N → 1 operation unique to GoT (not possible in ToT).
        Critical for synthesis tasks like: "Given these 5 research papers,
        what is the consensus finding?"
        """
        # Gather contents
        contents = [
            self.thoughts[tid].content for tid in thought_ids if tid in self.thoughts
        ]

        if not contents:
            return Thought(content="[Empty aggregation]", state=ThoughtState.PRUNED)

        # Determine depth (max of parents + 1)
        max_parent_depth = max(
            self.thoughts[tid].depth for tid in thought_ids if tid in self.thoughts
        )

        # Call aggregator
        aggregated_content = self._aggregator(contents)

        thought = Thought(
            content=aggregated_content,
            state=ThoughtState.COMPLETED,
            depth=max_parent_depth + 1,
            parents=thought_ids,
            metadata={"source": "aggregate", "input_count": len(contents)},
        )

        # Score
        thought.score = self._scorer(aggregated_content)

        # Link children
        for tid in thought_ids:
            if tid in self.thoughts:
                self.thoughts[tid].children.append(thought.id)

        self.thoughts[thought.id] = thought
        self.stats["thoughts_aggregated"] += 1

        return thought

    def refine(self, thought_id: str, iterations: int = 1) -> Thought:
        """
        Iteratively refine a thought.

        This creates a self-loop in the DAG: the refined thought
        replaces the original while maintaining lineage.
        """
        if thought_id not in self.thoughts:
            raise ValueError(f"Thought {thought_id} not found")

        current = self.thoughts[thought_id]

        for i in range(iterations):
            refined_content = self._refiner(current.content)

            refined = Thought(
                content=refined_content,
                state=ThoughtState.COMPLETED,
                depth=current.depth,  # Same depth (refinement, not branching)
                parents=[current.id],
                metadata={
                    "source": "refine",
                    "iteration": i + 1,
                    "original_id": thought_id,
                },
            )

            refined.score = self._scorer(refined_content)

            current.children.append(refined.id)
            self.thoughts[refined.id] = refined
            current = refined

        self.stats["thoughts_refined"] += iterations
        return current

    # ─────────────────────────────────────────────────────────────────────
    # Graph Operations
    # ─────────────────────────────────────────────────────────────────────

    def get_best_thought(self) -> Thought | None:
        """Return the highest-scoring non-pruned thought."""
        candidates = [
            t for t in self.thoughts.values() if t.state == ThoughtState.COMPLETED
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda t: t.score)

    def get_leaf_thoughts(self) -> list[Thought]:
        """Return all thoughts with no children (frontier)."""
        return [
            t
            for t in self.thoughts.values()
            if not t.children and t.state == ThoughtState.COMPLETED
        ]

    def get_lineage(self, thought_id: str) -> list[Thought]:
        """Trace back from thought to roots."""
        if thought_id not in self.thoughts:
            return []

        lineage = []
        current = self.thoughts[thought_id]
        visited = set()

        queue = [current]
        while queue:
            node = queue.pop(0)
            if node.id in visited:
                continue
            visited.add(node.id)
            lineage.append(node)
            for parent_id in node.parents:
                if parent_id in self.thoughts:
                    queue.append(self.thoughts[parent_id])

        return lineage

    def prune_below_threshold(self, threshold: float | None = None) -> int:
        """Prune thoughts below score threshold. Returns count pruned."""
        threshold = threshold or self.min_score_threshold
        count = 0
        for thought in self.thoughts.values():
            if thought.score < threshold and thought.state == ThoughtState.COMPLETED:
                thought.state = ThoughtState.PRUNED
                count += 1
        self.stats["thoughts_pruned"] += count
        return count

    def to_mermaid(self) -> str:
        """Export graph as Mermaid diagram for visualization."""
        lines = ["graph TD"]

        for thought in self.thoughts.values():
            # Node label
            label = thought.content[:30].replace('"', "'") + "..."
            score = f"{thought.score:.2f}"
            state_icon = "✓" if thought.state == ThoughtState.COMPLETED else "✗"
            lines.append(f'    {thought.id}["{state_icon} {label}<br/>score: {score}"]')

            # Edges
            for child_id in thought.children:
                lines.append(f"    {thought.id} --> {child_id}")

        return "\n".join(lines)

    # ─────────────────────────────────────────────────────────────────────
    # Default Transformation Functions (Placeholders)
    # ─────────────────────────────────────────────────────────────────────

    def _default_generator(self, prompt: str, n: int) -> list[str]:
        """Placeholder generator. In production, call LLM."""
        return [f"[Generated thought {i + 1} for: {prompt[:50]}...]" for i in range(n)]

    def _default_aggregator(self, contents: list[str]) -> str:
        """Placeholder aggregator. In production, call LLM."""
        return f"[Aggregated {len(contents)} thoughts]:\n" + "\n---\n".join(
            contents[:3]
        )

    def _default_refiner(self, content: str) -> str:
        """Placeholder refiner. In production, call LLM."""
        return f"[Refined]: {content}"

    def _default_scorer(self, content: str) -> float:
        """Placeholder scorer. In production, call evaluation model."""
        # Simple heuristic: longer = better (placeholder logic)
        return min(1.0, len(content) / 500)


# ─────────────────────────────────────────────────────────────────────────────
# Convenience Functions
# ─────────────────────────────────────────────────────────────────────────────


def synthesize(
    prompts: list[str],
    generator: Callable | None = None,
    aggregator: Callable | None = None,
) -> str:
    """
    Quick multi-source synthesis using GoT.

    Example:
        result = synthesize([
            "What are the benefits of microservices?",
            "What are the drawbacks of microservices?",
            "When should you NOT use microservices?"
        ])
    """
    got = GraphOfThoughts(generator=generator, aggregator=aggregator)

    # Generate thoughts for each prompt
    all_thought_ids = []
    for prompt in prompts:
        thoughts = got.generate(prompt, n=1)
        all_thought_ids.extend([t.id for t in thoughts])

    # Aggregate
    synthesis = got.aggregate(all_thought_ids)

    return synthesis.content


if __name__ == "__main__":
    print("Testing Graph of Thoughts...")

    got = GraphOfThoughts()

    # Generate initial thoughts
    thoughts = got.generate("What makes a good API design?", n=3)
    print(f"Generated {len(thoughts)} thoughts")

    # Aggregate
    synthesis = got.aggregate([t.id for t in thoughts])
    print(f"Aggregated to: {synthesis.content[:100]}...")

    # Refine
    refined = got.refine(synthesis.id, iterations=2)
    print(f"Refined {2}x: {refined.content[:100]}...")

    # Stats
    print(f"\nStats: {got.stats}")

    # Export Mermaid
    print(f"\nMermaid Diagram:\n{got.to_mermaid()}")
