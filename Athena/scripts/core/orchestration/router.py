#!/usr/bin/env python3
"""
athena.core.orchestration.router
=================================
Cognitive Router - Runtime decision layer for dynamic orchestration.

Routes queries to appropriate processing modes based on:
- Query complexity signals
- Manifest escalation triggers
- Session state and history

This is the missing link between STATIC manifest config and DYNAMIC execution.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import re

# Try to load manifest config
try:
    from athena.boot.config_loader import ManifestLoader

    MANIFEST_AVAILABLE = True
except ImportError:
    ManifestLoader = None
    MANIFEST_AVAILABLE = False


class ProcessingMode(Enum):
    """Available processing modes, ordered by compute cost."""

    INSTANT = "instant"  # Calculator, simple lookups
    FAST = "fast"  # Single-shot LLM, no search
    STANDARD = "standard"  # ReAct loop with retrieval
    DEEP = "deep"  # GoT + full retrieval
    ULTRADEEP = "ultradeep"  # GoT + Trilateral + all sources


class EscalationSignal(Enum):
    """Signals that trigger escalation to higher processing modes."""

    HIGH_BRANCHING = "high_branching_decision"
    CONTRADICTORY = "contradictory_evidence"
    FAILED_ATTEMPTS = "two_failed_attempts"
    LONG_HORIZON = "long_horizon"
    EXPLICIT_COMMAND = "explicit_command"  # /think, /ultrathink


@dataclass
class RoutingDecision:
    """Result of routing a query."""

    mode: ProcessingMode
    signals: list[EscalationSignal] = field(default_factory=list)
    retrieval_sources: dict[str, bool] = field(default_factory=dict)
    reasoning: str = ""


class CognitiveRouter:
    """
    Runtime router that decides HOW to process each query.

    Unlike the static manifest load, this runs on EVERY query
    and adapts based on content, signals, and history.

    Example:
        router = CognitiveRouter()
        decision = router.route("What is 2+2?")
        # decision.mode = ProcessingMode.INSTANT

        decision = router.route("Synthesize the evolution of Athena V1 to V3")
        # decision.mode = ProcessingMode.DEEP
    """

    def __init__(self):
        # Load manifest escalation config
        self.escalation_signals = [
            "high_branching_decision",
            "contradictory_evidence",
            "two_failed_attempts",
            "long_horizon",
        ]

        if MANIFEST_AVAILABLE:
            try:
                manifest = ManifestLoader.load()
                orch = manifest.get("orchestration", {})
                esc = orch.get("escalation", {})
                self.escalation_signals = esc.get("signals", self.escalation_signals)
            except Exception:
                pass

        # Session state tracking
        self.failed_attempts = 0
        self.query_history: list[str] = []

        # Complexity patterns
        self.deep_patterns = [
            r"synthesize",
            r"compare.*and.*contrast",
            r"trace.*evolution",
            r"root cause",
            r"why did",
            r"how does.*work",
            r"design.*architecture",
            r"implement.*system",
            r"refactor",
            r"debug.*complex",
        ]

        self.instant_patterns = [
            r"what is \d+\s*[\+\-\*\/]\s*\d+",  # arithmetic
            r"^(hi|hello|hey|thanks|ok|yes|no)$",  # greetings
            r"what time",
            r"what date",
        ]

        self.explicit_commands = {
            "/think": ProcessingMode.DEEP,
            "/ultrathink": ProcessingMode.ULTRADEEP,
            "/research": ProcessingMode.DEEP,
            "/fast": ProcessingMode.FAST,
        }

    def route(self, query: str, context: dict | None = None) -> RoutingDecision:
        """
        Route a query to the appropriate processing mode.

        Args:
            query: The user's input query
            context: Optional context (e.g., current file, recent errors)

        Returns:
            RoutingDecision with mode, signals, and source configuration
        """
        context = context or {}
        signals = []
        query_lower = query.lower().strip()

        # 1. Check explicit commands first
        for cmd, mode in self.explicit_commands.items():
            if query_lower.startswith(cmd):
                signals.append(EscalationSignal.EXPLICIT_COMMAND)
                return RoutingDecision(
                    mode=mode,
                    signals=signals,
                    retrieval_sources=self._sources_for_mode(mode),
                    reasoning=f"Explicit command: {cmd}",
                )

        # 2. Check instant patterns (calculator, greetings)
        for pattern in self.instant_patterns:
            if re.search(pattern, query_lower):
                return RoutingDecision(
                    mode=ProcessingMode.INSTANT,
                    signals=[],
                    retrieval_sources={},
                    reasoning=f"Matched instant pattern: {pattern}",
                )

        # 3. Check deep patterns (synthesis, analysis)
        for pattern in self.deep_patterns:
            if re.search(pattern, query_lower):
                signals.append(EscalationSignal.LONG_HORIZON)
                return RoutingDecision(
                    mode=ProcessingMode.DEEP,
                    signals=signals,
                    retrieval_sources=self._sources_for_mode(ProcessingMode.DEEP),
                    reasoning=f"Matched deep pattern: {pattern}",
                )

        # 4. Check failed attempts (escalation trigger)
        if self.failed_attempts >= 2:
            signals.append(EscalationSignal.FAILED_ATTEMPTS)
            return RoutingDecision(
                mode=ProcessingMode.DEEP,
                signals=signals,
                retrieval_sources=self._sources_for_mode(ProcessingMode.DEEP),
                reasoning=f"Escalated after {self.failed_attempts} failed attempts",
            )

        # 5. Check for contradictory context
        if context.get("contradictory_evidence"):
            signals.append(EscalationSignal.CONTRADICTORY)
            return RoutingDecision(
                mode=ProcessingMode.DEEP,
                signals=signals,
                retrieval_sources=self._sources_for_mode(ProcessingMode.DEEP),
                reasoning="Contradictory evidence detected",
            )

        # 6. Default to STANDARD
        return RoutingDecision(
            mode=ProcessingMode.STANDARD,
            signals=[],
            retrieval_sources=self._sources_for_mode(ProcessingMode.STANDARD),
            reasoning="Default processing mode",
        )

    def _sources_for_mode(self, mode: ProcessingMode) -> dict[str, bool]:
        """Get retrieval sources to enable for a given mode."""
        if mode == ProcessingMode.INSTANT:
            return {}

        if mode == ProcessingMode.FAST:
            return {"vector_memory": True}

        if mode == ProcessingMode.STANDARD:
            return {
                "vector_memory": True,
                "canonical_markdown": True,
                "tags_index": True,
                "filenames": True,
                "graph_rag": False,
            }

        if mode in (ProcessingMode.DEEP, ProcessingMode.ULTRADEEP):
            return {
                "vector_memory": True,
                "canonical_markdown": True,
                "tags_index": True,
                "filenames": True,
                "graph_rag": True,  # Enable for deep modes
            }

        return {}

    def record_failure(self):
        """Record a failed attempt for escalation tracking."""
        self.failed_attempts += 1

    def reset_failures(self):
        """Reset failure counter on success."""
        self.failed_attempts = 0

    def record_query(self, query: str):
        """Track query history for pattern detection."""
        self.query_history.append(query)
        if len(self.query_history) > 20:
            self.query_history.pop(0)


# Singleton instance
_router_instance: CognitiveRouter | None = None


def get_router() -> CognitiveRouter:
    """Get or create the singleton router instance."""
    global _router_instance
    if _router_instance is None:
        _router_instance = CognitiveRouter()
    return _router_instance


def route(query: str, context: dict | None = None) -> RoutingDecision:
    """Convenience function for routing queries."""
    return get_router().route(query, context)


if __name__ == "__main__":
    print("Testing Cognitive Router...\n")

    router = CognitiveRouter()

    test_queries = [
        "What is 2+2?",
        "hello",
        "Synthesize the evolution of Athena from V1 to V8",
        "How does the RRF pipeline work?",
        "/think about this problem deeply",
        "List all protocols",
        "Debug the complex memory leak issue",
    ]

    for q in test_queries:
        decision = router.route(q)
        print(f"Query: {q[:50]}...")
        print(f"  Mode: {decision.mode.value}")
        print(f"  Signals: {[s.value for s in decision.signals]}")
        print(
            f"  Sources: {list(k for k, v in decision.retrieval_sources.items() if v)}"
        )
        print(f"  Reason: {decision.reasoning}\n")
