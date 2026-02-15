#!/usr/bin/env python3
"""
athena.core.orchestration.gatekeeper
=====================================
Budget Gatekeeper - Runtime enforcement of manifest budget limits.

Tracks tool calls, tokens, and cost across a session.
Provides soft and hard limits with graceful degradation.

This fixes the "toothless budget" blind spot where budgets were
loaded but never enforced.
"""

from __future__ import annotations
from dataclasses import dataclass
from functools import wraps
from typing import Callable
import time

# Try to load manifest config
try:
    from athena.boot.config_loader import ManifestLoader

    MANIFEST_AVAILABLE = True
except ImportError:
    ManifestLoader = None
    MANIFEST_AVAILABLE = False


@dataclass
class BudgetState:
    """Current budget consumption state."""

    tool_calls_used: int = 0
    tokens_used: int = 0
    cost_usd_used: float = 0.0

    # Limits (loaded from manifest)
    tool_call_limit: int = 500
    token_limit: int = 2_000_000
    cost_limit_usd: float = 0.0  # 0 = unlimited (subscription)

    # Soft limit triggers (80% of hard limit)
    @property
    def tool_calls_remaining(self) -> int:
        return max(0, self.tool_call_limit - self.tool_calls_used)

    @property
    def tokens_remaining(self) -> int:
        return max(0, self.token_limit - self.tokens_used)

    @property
    def at_soft_limit(self) -> bool:
        """True if any resource is at 80% usage."""
        return (
            self.tool_calls_used >= self.tool_call_limit * 0.8
            or self.tokens_used >= self.token_limit * 0.8
        )

    @property
    def at_hard_limit(self) -> bool:
        """True if any resource exceeded limit."""
        return (
            self.tool_calls_used >= self.tool_call_limit
            or self.tokens_used >= self.token_limit
            or (self.cost_limit_usd > 0 and self.cost_usd_used >= self.cost_limit_usd)
        )


class BudgetGatekeeper:
    """
    Singleton gatekeeper for session budget enforcement.

    Usage:
        gatekeeper = BudgetGatekeeper()

        # Before tool call
        if gatekeeper.can_proceed():
            result = call_tool()
            gatekeeper.record_tool_call()
        else:
            raise BudgetExceededError("Tool call budget exceeded")

        # Or use as decorator
        @gatekeeper.guard
        def my_tool_function():
            ...
    """

    _instance: BudgetGatekeeper | None = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.state = BudgetState()
        self.session_start = time.time()
        self.warnings_issued = 0

        # Load limits from manifest
        if MANIFEST_AVAILABLE:
            try:
                budgets = ManifestLoader.get_budget_config()
                self.state.tool_call_limit = budgets.tool_call_budget
                self.state.token_limit = budgets.token_budget
                self.state.cost_limit_usd = budgets.cost_budget_usd
            except Exception:
                pass

    def can_proceed(self) -> bool:
        """Check if we can proceed with another tool call."""
        return not self.state.at_hard_limit

    def record_tool_call(self, tokens: int = 0, cost: float = 0.0):
        """Record a tool call and its resource usage."""
        self.state.tool_calls_used += 1
        self.state.tokens_used += tokens
        self.state.cost_usd_used += cost

        # Issue warning at soft limit (once)
        if self.state.at_soft_limit and self.warnings_issued == 0:
            self.warnings_issued += 1
            print(
                f"⚠️  Budget Warning: {self.state.tool_calls_used}/{self.state.tool_call_limit} tool calls used"
            )

    def record_tokens(self, tokens: int):
        """Record token usage (for non-tool-call contexts)."""
        self.state.tokens_used += tokens

    def get_status(self) -> dict:
        """Get current budget status."""
        elapsed = time.time() - self.session_start
        return {
            "tool_calls": f"{self.state.tool_calls_used}/{self.state.tool_call_limit}",
            "tokens": f"{self.state.tokens_used:,}/{self.state.token_limit:,}",
            "cost_usd": f"${self.state.cost_usd_used:.2f}/${self.state.cost_limit_usd:.2f}"
            if self.state.cost_limit_usd > 0
            else "unlimited",
            "session_minutes": f"{elapsed / 60:.1f}",
            "at_soft_limit": self.state.at_soft_limit,
            "at_hard_limit": self.state.at_hard_limit,
        }

    def guard(self, func: Callable) -> Callable:
        """Decorator to guard a function with budget checks."""

        @wraps(func)
        def wrapper(*args, **kwargs):
            if not self.can_proceed():
                raise BudgetExceededError(
                    f"Budget exceeded: {self.state.tool_calls_used} tool calls used"
                )
            result = func(*args, **kwargs)
            self.record_tool_call()
            return result

        return wrapper

    def reset(self):
        """Reset budget for new session."""
        self.state = BudgetState(
            tool_call_limit=self.state.tool_call_limit,
            token_limit=self.state.token_limit,
            cost_limit_usd=self.state.cost_limit_usd,
        )
        self.session_start = time.time()
        self.warnings_issued = 0


class BudgetExceededError(Exception):
    """Raised when budget limits are exceeded."""

    pass


# Singleton accessor
def get_gatekeeper() -> BudgetGatekeeper:
    """Get the singleton gatekeeper instance."""
    return BudgetGatekeeper()


# Convenience decorator
def budget_guard(func: Callable) -> Callable:
    """Convenience decorator using the singleton gatekeeper."""
    return get_gatekeeper().guard(func)


if __name__ == "__main__":
    print("Testing Budget Gatekeeper...\n")

    gk = BudgetGatekeeper()
    print(f"Initial status: {gk.get_status()}\n")

    # Simulate some tool calls
    for i in range(5):
        if gk.can_proceed():
            gk.record_tool_call(tokens=1000)
            print(f"Tool call {i + 1}: OK")
        else:
            print(f"Tool call {i + 1}: BLOCKED")

    print(f"\nFinal status: {gk.get_status()}")
