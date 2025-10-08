"""
Capital Allocation Manager for Capital Allocation Component.

This module provides the main orchestrator for deploying fund capital across
active strategies each quarter using the greedy allocation algorithm from iteration_one.
"""

from typing import List, Dict, Optional, Any
from .allocation_result import AllocationResult


class CapitalAllocationManager:
    """
    Main component for managing quarterly capital allocation across strategies.

    Implements the greedy allocation algorithm from iteration_one:
    1. Reset all strategy active_capacity to 0
    2. Get strategies with positive expected returns
    3. Sort by expected return (highest first)
    4. Allocate maximum possible to each strategy in order
    5. Stop when fund capital exhausted or all strategies filled
    """

    def __init__(self, strategy_manager):
        """
        Initialize the Capital Allocation Manager.

        Args:
            strategy_manager: StrategyManager instance to allocate capital to
        """
        self.strategy_manager = strategy_manager
        self.allocation_history: Dict[int, AllocationResult] = {}

    def allocate_capital(self, available_capital: float, quarter: int) -> AllocationResult:
        """
        Allocate available capital across strategies using greedy algorithm.

        Based on iteration_one rebalance() method:
        - Resets all active capacities to 0
        - Gets strategies with positive expected returns
        - Sorts by expected return (descending)
        - Allocates greedily respecting capacity constraints

        Args:
            available_capital: Total capital available for deployment (millions)
            quarter: Current quarter number

        Returns:
            AllocationResult: Detailed allocation outcome and metrics
        """
        # Phase 1: Reset all active capacities to 0 (complete rebalancing)
        for strategy in self.strategy_manager.get_all_strategies():
            strategy.set_active_capacity(0.0)

        # Phase 2: Get strategies with positive expected returns
        active_strategies = self.strategy_manager.get_active_strategies()

        if not active_strategies:
            # No strategies to allocate to
            return AllocationResult(
                quarter=quarter,
                total_available_capital=available_capital,
                total_deployed_capital=0.0,
                undeployed_capital=available_capital,
                allocation_by_strategy={},
                strategy_count=0
            )

        # Phase 3: Create allocation candidates [expected_return, max_capacity, strategy]
        candidates = []
        for strategy in active_strategies:
            candidates.append([
                strategy.get_expected_return(),
                strategy.max_capacity,
                strategy
            ])

        # Phase 4: Sort by expected return (highest first)
        candidates.sort(key=lambda x: x[0], reverse=True)

        # Phase 5: Allocate capital greedily
        deployed_capital = 0.0
        allocations = {}

        for expected_return, max_capacity, strategy in candidates:
            # Calculate maximum we can allocate to this strategy
            remaining_capital = available_capital - deployed_capital

            if remaining_capital <= 0:
                break

            max_allocation = min(max_capacity, remaining_capital)

            if max_allocation > 0:
                # Allocate to strategy
                strategy.set_active_capacity(max_allocation)
                allocations[strategy.strategy_id] = max_allocation
                deployed_capital += max_allocation

                # Stop if we've deployed all capital
                if deployed_capital >= available_capital:
                    break

        # Phase 6: Create and store allocation result
        result = AllocationResult(
            quarter=quarter,
            total_available_capital=available_capital,
            total_deployed_capital=deployed_capital,
            undeployed_capital=available_capital - deployed_capital,
            allocation_by_strategy=allocations,
            strategy_count=len(allocations)
        )

        # Store in history
        self.allocation_history[quarter] = result

        return result

    def rebalance_portfolio(self, available_capital: float, quarter: int) -> AllocationResult:
        """
        Rebalance portfolio (alias for allocate_capital for clean interface).

        Args:
            available_capital: Total capital available for deployment
            quarter: Current quarter number

        Returns:
            AllocationResult: Allocation outcome
        """
        return self.allocate_capital(available_capital, quarter)

    def get_allocation_summary(self, quarter: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed allocation summary for a specific quarter.

        Args:
            quarter: Quarter to get summary for

        Returns:
            Optional[Dict]: Allocation summary or None if quarter not found
        """
        if quarter not in self.allocation_history:
            return None

        return self.allocation_history[quarter].get_summary()

    def get_undeployed_capital(self, quarter: int) -> float:
        """
        Get undeployed capital for a specific quarter.

        Args:
            quarter: Quarter to check

        Returns:
            float: Undeployed capital amount (0.0 if quarter not found)
        """
        if quarter not in self.allocation_history:
            return 0.0

        return self.allocation_history[quarter].undeployed_capital

    def get_current_allocations(self) -> Dict[str, float]:
        """
        Get current allocation amounts by strategy from the strategy manager.

        Returns:
            Dict[str, float]: Mapping of strategy_id to current active_capacity
        """
        allocations = {}
        for strategy in self.strategy_manager.get_all_strategies():
            if strategy.active_capacity > 0:
                allocations[strategy.strategy_id] = strategy.active_capacity

        return allocations

    def get_allocation_efficiency_stats(self) -> Dict[str, Any]:
        """
        Get allocation efficiency statistics across all quarters.

        Returns:
            Dict: Efficiency statistics including average, min, max deployment rates
        """
        if not self.allocation_history:
            return {
                'quarters_tracked': 0,
                'average_efficiency': 0.0,
                'min_efficiency': 0.0,
                'max_efficiency': 0.0,
                'total_capital_allocated': 0.0
            }

        efficiencies = [result.allocation_efficiency for result in self.allocation_history.values()]
        total_allocated = sum(result.total_deployed_capital for result in self.allocation_history.values())

        return {
            'quarters_tracked': len(self.allocation_history),
            'average_efficiency': sum(efficiencies) / len(efficiencies),
            'min_efficiency': min(efficiencies),
            'max_efficiency': max(efficiencies),
            'total_capital_allocated': total_allocated
        }

    def clear_allocation_history(self):
        """Clear allocation history (useful for testing)."""
        self.allocation_history.clear()

    def __repr__(self) -> str:
        """String representation of the manager."""
        return (
            f"CapitalAllocationManager("
            f"quarters_tracked={len(self.allocation_history)}, "
            f"strategies_managed={len(self.strategy_manager.get_all_strategies())})"
        )