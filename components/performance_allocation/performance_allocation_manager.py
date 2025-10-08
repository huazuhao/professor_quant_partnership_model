"""
Performance Allocation Manager for Performance Allocation Component.

This module provides the main orchestrator for quarterly performance allocation,
implementing high water mark accounting, author performance distribution, and
safety net program operations from iteration_one.
"""

from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
from .performance_allocation_parameters import PerformanceAllocationParameters as PAP
from .allocation_summary import AllocationSummary


class PerformanceAllocationManager:
    """
    Main component for managing quarterly performance allocation across authors.

    Implements the complete performance allocation system from iteration_one:
    1. Management fee collection
    2. High water mark accounting
    3. Three-way profit distribution (fund, performance, safety net)
    4. Author performance allocation based on strategy ownership
    5. Safety net distribution for authors below guaranteed minimum
    """

    def __init__(self, strategy_manager, author_manager=None, initial_aum: float = None):
        """
        Initialize the Performance Allocation Manager.

        Args:
            strategy_manager: StrategyManager instance for strategy-author linkage
            author_manager: AuthorCollaborationManager instance for lifetime payment tracking (optional)
            initial_aum: Initial fund AUM (defaults to parameter value)
        """
        self.strategy_manager = strategy_manager
        self.author_manager = author_manager
        self.fund_aum = initial_aum if initial_aum is not None else PAP.FUND_INITIAL_AUM
        self.cumulative_loss_account = 0.0
        self.allocation_history: Dict[int, AllocationSummary] = {}

    def process_quarterly_allocation(
        self,
        strategy_returns: Dict[str, float],
        quarter: int
    ) -> AllocationSummary:
        """
        Process complete quarterly performance allocation.

        Args:
            strategy_returns: Dict mapping strategy_id to dollar returns
            quarter: Current quarter number

        Returns:
            AllocationSummary: Comprehensive allocation results
        """
        # Step 1: Collect management fee
        management_fee = self._collect_management_fee()

        # Step 2: Calculate total strategy returns
        total_returns = sum(strategy_returns.values())

        # Step 3: Apply strategy returns to fund AUM immediately
        # This ensures losses reduce AUM and gains increase AUM, regardless of HWM status
        self.fund_aum += total_returns

        # Step 4: Apply high water mark accounting
        loss_account_start = self.cumulative_loss_account
        distributable_profits = self._calculate_high_water_mark(total_returns)
        high_water_mark_met = distributable_profits > 0

        # Step 5: Initialize allocation summary
        summary = AllocationSummary(
            quarter=quarter,
            total_strategy_returns=total_returns,
            fund_aum_start=self.fund_aum + management_fee - total_returns,  # AUM at quarter start (before fees and returns)
            management_fee_charged=management_fee,
            cumulative_loss_account_start=loss_account_start,
            cumulative_loss_account_end=self.cumulative_loss_account,
            distributable_profits=distributable_profits,
            high_water_mark_met=high_water_mark_met,
            fund_retention=0.0,
            author_performance_total=0.0,
            safety_net_total=0.0
        )

        if not high_water_mark_met:
            # No distribution this quarter
            summary.fund_retention = 0.0
            summary.author_performance_total = 0.0
            summary.safety_net_total = 0.0
        else:
            # Step 6: Calculate profit distribution pools
            fund_retention = distributable_profits * PAP.get_fund_retention_rate()
            author_pool = distributable_profits * PAP.PERFORMANCE_ALLOCATION
            performance_pool = author_pool * (1.0 - PAP.AUTHOR_SAFETY_NET_RATIO)
            safety_net_pool = author_pool * PAP.AUTHOR_SAFETY_NET_RATIO

            # Step 7: Distribute performance allocation to strategy authors
            performance_allocations = self._distribute_performance_allocation(
                strategy_returns, performance_pool, quarter
            )

            # Step 8: Distribute safety net payments
            safety_net_allocations = self._distribute_safety_net_payments(
                safety_net_pool, quarter
            )

            # Step 9: Pay authors (subtract from fund AUM)
            # Note: Strategy returns were already added to AUM in Step 3
            # Fund's 80% retention stays in AUM; we only subtract the 20% paid to authors
            total_author_payments = sum(performance_allocations.values()) + sum(safety_net_allocations.values())
            self.fund_aum -= total_author_payments

            # Step 10: Update summary
            summary.fund_retention = fund_retention
            summary.author_performance_total = sum(performance_allocations.values())
            summary.safety_net_total = sum(safety_net_allocations.values())
            summary.allocation_by_author = performance_allocations
            summary.safety_net_by_author = safety_net_allocations
            # Recalculate summary metrics now that we have the actual allocation data
            summary._calculate_summary_metrics()

        # Step 11: Store allocation history
        self.allocation_history[quarter] = summary

        return summary

    def _collect_management_fee(self) -> float:
        """
        Collect quarterly management fee from fund AUM.

        Returns:
            float: Management fee amount collected
        """
        fee = self.fund_aum * PAP.get_management_fee_decimal()
        self.fund_aum -= fee
        return fee

    def _calculate_high_water_mark(self, new_returns: float) -> float:
        """
        Update cumulative loss account and determine distributable profits.

        Based on iteration_one hedgedemia_fund.above_high_water_mark()

        Args:
            new_returns: Total strategy returns for this quarter

        Returns:
            float: Profits available for distribution (0 if below high water mark)
        """
        self.cumulative_loss_account += new_returns

        if self.cumulative_loss_account > 0:
            distributable_profits = self.cumulative_loss_account
            self.cumulative_loss_account = 0.0
            return distributable_profits
        else:
            return 0.0

    def _distribute_performance_allocation(
        self,
        strategy_returns: Dict[str, float],
        performance_pool: float,
        quarter: int
    ) -> Dict[str, float]:
        """
        Distribute performance allocation among strategy authors.

        Based on iteration_one performance allocation logic in simulation notebook.

        Args:
            strategy_returns: Strategy returns for attribution
            performance_pool: Total performance allocation available
            quarter: Current quarter

        Returns:
            Dict mapping author_id to performance allocation amount
        """
        author_allocations = defaultdict(float)
        total_profitable_returns = sum(r for r in strategy_returns.values() if r > 0)

        if total_profitable_returns <= 0:
            return dict(author_allocations)

        for strategy_id, strategy_return in strategy_returns.items():
            if strategy_return <= 0:
                continue

            strategy = self.strategy_manager.get_strategy_by_id(strategy_id)
            if not strategy or not strategy.ownership_splits:
                continue

            # Calculate this strategy's share of total performance pool
            strategy_share = (strategy_return / total_profitable_returns) * performance_pool

            # Distribute among authors based on ownership splits
            # Note: ownership_splits keys are author_ids (strings), not Author objects
            for author_id, ownership_percentage in strategy.ownership_splits.items():
                author_payment = strategy_share * ownership_percentage
                author_allocations[author_id] += author_payment

        # Record payments to Author objects (for lifetime payment tracking)
        if self.author_manager is not None:
            for author_id, payment in author_allocations.items():
                author = self.author_manager.get_author_by_id(author_id)
                if author is not None:
                    if quarter not in author.performance_payments:
                        author.performance_payments[quarter] = 0.0
                    author.performance_payments[quarter] += payment

        return dict(author_allocations)

    def _distribute_safety_net_payments(
        self,
        safety_net_pool: float,
        quarter: int
    ) -> Dict[str, float]:
        """
        Distribute safety net payments to eligible authors.

        Based on iteration_one safety net logic: equal distribution among
        authors below guaranteed minimum who are enrolled in safety net.

        Args:
            safety_net_pool: Total safety net funds available
            quarter: Current quarter

        Returns:
            Dict mapping author_id to safety net payment amount
        """
        if safety_net_pool <= 0:
            return {}

        # Get all enrolled authors who are below guaranteed minimum
        eligible_authors = self._get_safety_net_eligible_authors()

        if not eligible_authors:
            return {}

        # Distribute equally among eligible authors
        payment_per_author = safety_net_pool / len(eligible_authors)
        safety_net_payments = {}

        for author_id in eligible_authors:
            safety_net_payments[author_id] = payment_per_author

        # Record payments to Author objects (for lifetime payment tracking)
        if self.author_manager is not None:
            for author_id, payment in safety_net_payments.items():
                author = self.author_manager.get_author_by_id(author_id)
                if author is not None:
                    if quarter not in author.safety_net_payments:
                        author.safety_net_payments[quarter] = 0.0
                    author.safety_net_payments[quarter] += payment

        return safety_net_payments

    def _get_safety_net_eligible_authors(self) -> List[str]:
        """
        Get list of author_ids eligible for safety net payments.

        An author is eligible if:
        1. They are enrolled in safety net (contributed to a strategy)
        2. Their lifetime payments are below guaranteed minimum

        Returns:
            List of author_id strings eligible for safety net
        """
        eligible_author_ids = []

        # Get all enrolled author_ids from strategies
        enrolled_author_ids = set()
        for strategy in self.strategy_manager.get_all_strategies():
            if strategy.ownership_splits:
                enrolled_author_ids.update(strategy.ownership_splits.keys())

        # Filter by lifetime payments if author_manager is available
        if self.author_manager is not None:
            for author_id in enrolled_author_ids:
                author = self.author_manager.get_author_by_id(author_id)
                if author is not None:
                    # Check if author's lifetime payments are below guarantee
                    if author.get_lifetime_payments() < PAP.AUTHOR_GUARANTEED_RETURN:
                        eligible_author_ids.append(author_id)
        else:
            # Fallback: If no author_manager, assume all enrolled authors are eligible
            # This maintains backward compatibility with existing tests
            eligible_author_ids = list(enrolled_author_ids)

        return eligible_author_ids

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

    def get_fund_aum(self) -> float:
        """Get current fund AUM."""
        return self.fund_aum

    def get_cumulative_loss_account(self) -> float:
        """Get current cumulative loss account."""
        return self.cumulative_loss_account

    # ============================================
    # INVESTOR FLOW INTEGRATION METHODS
    # ============================================

    def get_quarterly_return_percentage(self, quarter: int) -> Optional[float]:
        """
        Get quarterly return percentage for a specific quarter.

        Used by Investor Flow Component to calculate trailing performance.

        Args:
            quarter: Quarter number

        Returns:
            Return percentage (decimal, e.g., 0.05 = 5%), or None if not found
        """
        if quarter not in self.allocation_history:
            return None

        summary = self.allocation_history[quarter]

        # Calculate return as (total_strategy_returns / fund_aum_start)
        if summary.fund_aum_start <= 0:
            return 0.0

        return summary.total_strategy_returns / summary.fund_aum_start

    def get_trailing_returns(
        self,
        current_quarter: int,
        quarters: int = 4
    ) -> List[float]:
        """
        Get trailing N quarters of returns.

        Used by Investor Flow Component for performance lookback.

        Args:
            current_quarter: Current quarter number
            quarters: Number of quarters to look back (default 4)

        Returns:
            List of quarterly returns (decimals), most recent last.
            May be shorter than requested if insufficient history.
        """
        returns = []
        start_quarter = current_quarter - quarters + 1

        for q in range(start_quarter, current_quarter + 1):
            ret = self.get_quarterly_return_percentage(q)
            if ret is not None:
                returns.append(ret)

        return returns

    def update_aum(self, net_flow: float) -> None:
        """
        Update fund AUM by adding net investor flows.

        Called by Investor Flow Component after processing quarterly flows.

        Args:
            net_flow: Net flow amount in millions
                     (positive = inflows, negative = outflows)
        """
        self.fund_aum += net_flow

    def get_allocation_efficiency_stats(self) -> Dict[str, Any]:
        """
        Get allocation efficiency statistics across all quarters.

        Returns:
            Dict: Historical efficiency statistics
        """
        if not self.allocation_history:
            return {
                'quarters_tracked': 0,
                'average_efficiency': 0.0,
                'min_efficiency': 0.0,
                'max_efficiency': 0.0,
                'quarters_above_hwm': 0,
                'total_profits_distributed': 0.0
            }

        efficiencies = [result.get_allocation_efficiency() for result in self.allocation_history.values()]
        quarters_above_hwm = sum(1 for result in self.allocation_history.values() if result.high_water_mark_met)
        total_distributed = sum(result.get_total_author_payments() for result in self.allocation_history.values())

        return {
            'quarters_tracked': len(self.allocation_history),
            'average_efficiency': sum(efficiencies) / len(efficiencies),
            'min_efficiency': min(efficiencies),
            'max_efficiency': max(efficiencies),
            'quarters_above_hwm': quarters_above_hwm,
            'total_profits_distributed': total_distributed
        }

    def clear_allocation_history(self):
        """Clear allocation history (useful for testing)."""
        self.allocation_history.clear()

    def __repr__(self) -> str:
        """String representation of the manager."""
        return (
            f"PerformanceAllocationManager("
            f"aum=${self.fund_aum:.1f}M, "
            f"loss_account=${self.cumulative_loss_account:.1f}M, "
            f"quarters_tracked={len(self.allocation_history)})"
        )