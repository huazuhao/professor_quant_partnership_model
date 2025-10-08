"""
Allocation Result data structures for Capital Allocation Component.

This module defines data structures for tracking capital allocation outcomes
and providing detailed reporting for analysis and integration with other components.
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class AllocationResult:
    """
    Data structure to track capital allocation outcomes for a quarter.

    Provides detailed information about capital deployment including
    efficiency metrics, strategy counts, and allocation breakdowns.
    """

    quarter: int
    total_available_capital: float
    total_deployed_capital: float
    undeployed_capital: float
    allocation_by_strategy: Dict[str, float]  # strategy_id -> allocated_amount
    strategy_count: int

    def __post_init__(self):
        """Calculate derived metrics after initialization."""
        # Ensure undeployed capital is consistent
        self.undeployed_capital = self.total_available_capital - self.total_deployed_capital

        # Validate allocations sum correctly
        allocated_sum = sum(self.allocation_by_strategy.values())
        if abs(allocated_sum - self.total_deployed_capital) > 0.01:  # Allow small floating point errors
            raise ValueError(
                f"Allocation sum ({allocated_sum}) doesn't match total deployed ({self.total_deployed_capital})"
            )

    @property
    def allocation_efficiency(self) -> float:
        """Calculate allocation efficiency as deployed/available capital ratio."""
        if self.total_available_capital <= 0:
            return 0.0
        return self.total_deployed_capital / self.total_available_capital

    @property
    def average_strategy_allocation(self) -> float:
        """Calculate average allocation per strategy."""
        if self.strategy_count == 0:
            return 0.0
        return self.total_deployed_capital / self.strategy_count

    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive allocation summary for reporting."""
        return {
            'quarter': self.quarter,
            'total_available_capital': self.total_available_capital,
            'total_deployed_capital': self.total_deployed_capital,
            'undeployed_capital': self.undeployed_capital,
            'allocation_efficiency': self.allocation_efficiency,
            'strategy_count': self.strategy_count,
            'average_strategy_allocation': self.average_strategy_allocation,
            'strategies_funded': list(self.allocation_by_strategy.keys()),
            'allocation_by_strategy': self.allocation_by_strategy.copy()
        }

    def get_top_allocations(self, n: int = 5) -> Dict[str, float]:
        """Get top N strategy allocations by amount."""
        sorted_allocations = sorted(
            self.allocation_by_strategy.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return dict(sorted_allocations[:n])

    def __str__(self) -> str:
        """Human-readable string representation."""
        return (
            f"AllocationResult(Q{self.quarter}: "
            f"{self.total_deployed_capital:.1f}M/{self.total_available_capital:.1f}M "
            f"({self.allocation_efficiency:.1%}) across {self.strategy_count} strategies)"
        )