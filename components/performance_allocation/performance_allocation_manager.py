"""
Performance Allocation Manager for Performance Allocation Component.

This module provides the main orchestrator for quarterly NAV accounting,
cohort-level high water mark tracking, annual author performance distribution,
and safety net program operations.
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from collections import defaultdict
from .performance_allocation_parameters import PerformanceAllocationParameters as PAP
from .allocation_summary import AllocationSummary


@dataclass
class CapitalCohort:
    """Investor capital cohort with its own high-water-mark accounting."""

    cohort_id: str
    capital: float
    quarter_created: int
    high_water_mark: float
    cumulative_loss_account: float = 0.0
    annual_net_profit: float = 0.0


class PerformanceAllocationManager:
    """
    Main component for managing NAV accounting and annual author allocations.

    Implements the complete performance allocation system:
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
        self.capital_cohorts: List[CapitalCohort] = [
            CapitalCohort(
                cohort_id="initial_capital",
                capital=self.fund_aum,
                quarter_created=0,
                high_water_mark=self.fund_aum
            )
        ]
        self.year_to_date_strategy_returns: Dict[str, float] = defaultdict(float)
        self.allocation_history: Dict[int, AllocationSummary] = {}
        self.withdrawal_crystallization_history: Dict[int, List[Dict[str, Any]]] = defaultdict(list)

    def process_quarterly_allocation(
        self,
        strategy_returns: Dict[str, float],
        quarter: int
    ) -> AllocationSummary:
        """
        Process quarterly NAV accounting and any annual performance allocation.

        Args:
            strategy_returns: Dict mapping strategy_id to dollar returns
            quarter: Current quarter number

        Returns:
            AllocationSummary: Comprehensive allocation results
        """
        fund_aum_start = self.get_fund_aum()
        loss_account_start = self.get_cumulative_loss_account()

        # Step 1: Collect management fee from each capital cohort
        management_fee = self._collect_management_fee()

        # Step 2: Calculate total strategy returns
        total_returns = sum(strategy_returns.values())

        # Step 3: Apply net strategy P&L to investor cohorts
        self._apply_strategy_returns_to_cohorts(total_returns)
        self._record_year_to_date_strategy_returns(strategy_returns)

        # Step 4: Crystallize performance allocation annually
        distributable_profits = 0.0
        high_water_mark_met = False
        fund_retention = 0.0
        performance_allocations = {}
        safety_net_allocations = {}

        if self._is_performance_crystallization_quarter(quarter):
            performance_profits_by_cohort = self._crystallize_annual_hwm_profits()
            distributable_profits = sum(performance_profits_by_cohort.values())
            high_water_mark_met = distributable_profits > 0

            if high_water_mark_met:
                author_pool = distributable_profits * PAP.PERFORMANCE_ALLOCATION
                performance_pool = author_pool * (1.0 - PAP.AUTHOR_SAFETY_NET_RATIO)
                safety_net_pool = author_pool * PAP.AUTHOR_SAFETY_NET_RATIO

                performance_allocations = self._distribute_performance_allocation(
                    self.year_to_date_strategy_returns, performance_pool, quarter
                )
                safety_net_allocations = self._distribute_safety_net_payments(
                    safety_net_pool, quarter
                )

                total_author_payments = (
                    sum(performance_allocations.values())
                    + sum(safety_net_allocations.values())
                )
                self._deduct_author_payments_from_profitable_cohorts(
                    total_author_payments,
                    performance_profits_by_cohort
                )
                fund_retention = distributable_profits - total_author_payments

            self._finalize_annual_period()

        # Step 5: Build allocation summary
        summary = AllocationSummary(
            quarter=quarter,
            total_strategy_returns=total_returns,
            fund_aum_start=fund_aum_start,
            management_fee_charged=management_fee,
            cumulative_loss_account_start=loss_account_start,
            cumulative_loss_account_end=self.get_cumulative_loss_account(),
            distributable_profits=distributable_profits,
            high_water_mark_met=high_water_mark_met,
            fund_retention=fund_retention,
            author_performance_total=sum(performance_allocations.values()),
            safety_net_total=sum(safety_net_allocations.values()),
            allocation_by_author=performance_allocations,
            safety_net_by_author=safety_net_allocations
        )

        # Step 6: Store allocation history
        self.allocation_history[quarter] = summary

        return summary

    def _collect_management_fee(self) -> float:
        """
        Collect quarterly management fee from fund AUM.

        Returns:
            float: Management fee amount collected
        """
        total_fee = 0.0
        fee_rate = PAP.get_management_fee_decimal()

        for cohort in self.capital_cohorts:
            fee = cohort.capital * fee_rate
            cohort.capital -= fee
            cohort.annual_net_profit -= fee
            total_fee += fee

        self._sync_fund_aum_from_cohorts()
        return total_fee

    def _apply_strategy_returns_to_cohorts(self, total_returns: float) -> None:
        """Allocate net quarterly strategy P&L across investor cohorts pro rata."""
        total_capital = self._get_total_cohort_capital()
        if total_returns == 0 or total_capital <= 0:
            self._sync_fund_aum_from_cohorts()
            return

        for cohort in self.capital_cohorts:
            cohort_return = total_returns * (cohort.capital / total_capital)
            cohort.capital += cohort_return
            cohort.annual_net_profit += cohort_return

        self._sync_fund_aum_from_cohorts()

    def _record_year_to_date_strategy_returns(
        self,
        strategy_returns: Dict[str, float]
    ) -> None:
        """Track annual strategy attribution for year-end author payouts."""
        for strategy_id, strategy_return in strategy_returns.items():
            self.year_to_date_strategy_returns[strategy_id] += strategy_return

    def _is_performance_crystallization_quarter(self, quarter: int) -> bool:
        """Performance allocation crystallizes annually in this quarterly model."""
        return (
            quarter > 0
            and quarter % PAP.PERFORMANCE_CRYSTALLIZATION_QUARTERS == 0
        )

    def _crystallize_annual_hwm_profits(self) -> Dict[str, float]:
        """
        Apply annual high-water-mark accounting by cohort.

        Returns only the net annual profits above each cohort's carried loss
        account. Losses and partial recoveries update each cohort's loss account
        without creating a performance allocation.
        """
        performance_profits = {}

        for cohort in self.capital_cohorts:
            annual_profit = cohort.annual_net_profit
            if annual_profit <= 0:
                cohort.cumulative_loss_account += abs(annual_profit)
                continue

            recoverable_loss = min(
                annual_profit,
                cohort.cumulative_loss_account
            )
            cohort.cumulative_loss_account -= recoverable_loss
            profit_above_hwm = annual_profit - recoverable_loss

            if profit_above_hwm > 0:
                performance_profits[cohort.cohort_id] = profit_above_hwm

        return performance_profits

    def _deduct_author_payments_from_profitable_cohorts(
        self,
        total_author_payments: float,
        performance_profits_by_cohort: Dict[str, float]
    ) -> None:
        """Charge actual author payouts to profitable cohorts pro rata."""
        if total_author_payments <= 0:
            return

        total_performance_profit = sum(performance_profits_by_cohort.values())
        if total_performance_profit <= 0:
            return

        for cohort in self.capital_cohorts:
            cohort_profit = performance_profits_by_cohort.get(cohort.cohort_id, 0.0)
            if cohort_profit <= 0:
                continue

            payment_share = cohort_profit / total_performance_profit
            cohort.capital -= total_author_payments * payment_share

        self._sync_fund_aum_from_cohorts()

    def _finalize_annual_period(self) -> None:
        """Reset annual trackers and update cohort high-water marks."""
        for cohort in self.capital_cohorts:
            if cohort.cumulative_loss_account <= 0 and cohort.capital > cohort.high_water_mark:
                cohort.high_water_mark = cohort.capital
            cohort.annual_net_profit = 0.0

        self.year_to_date_strategy_returns = defaultdict(float)
        self._sync_fund_aum_from_cohorts()

    def _distribute_performance_allocation(
        self,
        strategy_returns: Dict[str, float],
        performance_pool: float,
        quarter: int
    ) -> Dict[str, float]:
        """
        Distribute performance allocation among strategy authors.

        Distributes the author performance pool by annual profitable strategy attribution.

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

        Uses equal distribution among authors below the guaranteed minimum who
        are enrolled in the safety net.
        When author lifetime payment tracking is available, each author's
        payment is capped at their remaining guarantee gap and leftover pool
        is redistributed to other still-under-cap eligible authors.

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

        if self.author_manager is None:
            # Fallback for callers without lifetime payment tracking.
            payment_per_author = safety_net_pool / len(eligible_authors)
            safety_net_payments = {
                author_id: payment_per_author for author_id in eligible_authors
            }
        else:
            safety_net_payments = self._calculate_capped_safety_net_payments(
                safety_net_pool, eligible_authors
            )

        # Record payments to Author objects (for lifetime payment tracking)
        if self.author_manager is not None:
            for author_id, payment in safety_net_payments.items():
                author = self.author_manager.get_author_by_id(author_id)
                if author is not None:
                    if quarter not in author.safety_net_payments:
                        author.safety_net_payments[quarter] = 0.0
                    author.safety_net_payments[quarter] += payment

        return safety_net_payments

    def _calculate_capped_safety_net_payments(
        self,
        safety_net_pool: float,
        eligible_authors: List[str]
    ) -> Dict[str, float]:
        """
        Split safety-net funds equally while enforcing the lifetime guarantee cap.

        Authors near the guarantee receive only their remaining gap. Unused
        amounts from capped authors are redistributed equally among the remaining
        eligible authors who are still below the cap.
        """
        remaining_gaps = {}
        for author_id in eligible_authors:
            author = self.author_manager.get_author_by_id(author_id)
            if author is None:
                continue

            remaining_gap = (
                PAP.AUTHOR_GUARANTEED_RETURN
                - author.get_lifetime_payments()
            )
            if remaining_gap > 0:
                remaining_gaps[author_id] = remaining_gap

        payments = defaultdict(float)
        remaining_pool = safety_net_pool
        epsilon = 1e-12

        while remaining_pool > epsilon and remaining_gaps:
            equal_share = remaining_pool / len(remaining_gaps)
            paid_this_round = 0.0

            for author_id in list(remaining_gaps.keys()):
                payment = min(equal_share, remaining_gaps[author_id])
                if payment <= epsilon:
                    del remaining_gaps[author_id]
                    continue

                payments[author_id] += payment
                paid_this_round += payment
                remaining_gaps[author_id] -= payment

                if remaining_gaps[author_id] <= epsilon:
                    del remaining_gaps[author_id]

            if paid_this_round <= epsilon:
                break

            remaining_pool = max(0.0, remaining_pool - paid_this_round)

        return dict(payments)

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

    def _get_total_cohort_capital(self) -> float:
        """Return aggregate active cohort capital."""
        return sum(cohort.capital for cohort in self.capital_cohorts)

    def _sync_fund_aum_from_cohorts(self) -> None:
        """Keep the public fund AUM value aligned with cohort capital."""
        self.capital_cohorts = [
            cohort for cohort in self.capital_cohorts
            if abs(cohort.capital) > 1e-12
        ]
        self.fund_aum = self._get_total_cohort_capital()

    def _add_capital_cohort(self, net_flow: float, quarter: Optional[int]) -> None:
        """Add new investor capital as a clean high-water-mark cohort."""
        cohort_number = len(self.capital_cohorts) + 1
        cohort_id = f"flow_q{quarter}_cohort_{cohort_number}"
        self.capital_cohorts.append(
            CapitalCohort(
                cohort_id=cohort_id,
                capital=net_flow,
                quarter_created=quarter if quarter is not None else -1,
                high_water_mark=net_flow
            )
        )
        self._sync_fund_aum_from_cohorts()

    def _withdraw_capital_from_cohorts(
        self,
        withdrawal_amount: float,
        quarter: Optional[int]
    ) -> None:
        """
        Remove investor capital pro rata and crystallize redeemed gains.

        This avoids new and old capital sharing the same high-water mark while
        keeping the investor-flow model aggregated. For redemptions, the flow
        amount is treated as gross redeeming NAV: any crystallized author
        payments are funded from that amount, so the investor-flow AUM decrease
        remains exactly the requested withdrawal.
        """
        total_capital = self._get_total_cohort_capital()
        if withdrawal_amount <= 0 or total_capital <= 0:
            return

        withdrawal_amount = min(withdrawal_amount, total_capital)
        withdrawal_ratio_total = withdrawal_amount / total_capital
        performance_profits_by_cohort = {}

        for cohort in list(self.capital_cohorts):
            capital_before_withdrawal = cohort.capital
            cohort_withdrawal = (
                withdrawal_amount
                * capital_before_withdrawal
                / total_capital
            )
            if cohort_withdrawal <= 0:
                continue

            withdrawal_ratio = min(
                1.0,
                cohort_withdrawal / capital_before_withdrawal
            )
            remaining_ratio = 1.0 - withdrawal_ratio

            withdrawn_annual_profit = cohort.annual_net_profit * withdrawal_ratio
            withdrawn_loss_account = cohort.cumulative_loss_account * withdrawal_ratio
            if withdrawn_annual_profit > 0:
                profit_above_hwm = max(
                    0.0,
                    withdrawn_annual_profit - withdrawn_loss_account
                )
                if profit_above_hwm > 0:
                    performance_profits_by_cohort[cohort.cohort_id] = profit_above_hwm

            cohort.capital -= cohort_withdrawal
            cohort.high_water_mark *= remaining_ratio
            cohort.cumulative_loss_account *= remaining_ratio
            cohort.annual_net_profit *= remaining_ratio

        self._process_withdrawal_crystallization(
            performance_profits_by_cohort,
            withdrawal_amount,
            quarter
        )
        self._scale_year_to_date_strategy_returns(1.0 - withdrawal_ratio_total)
        self._sync_fund_aum_from_cohorts()

    def _scale_year_to_date_strategy_returns(self, remaining_ratio: float) -> None:
        """Remove the redeemed investors' pro-rata YTD strategy attribution."""
        if remaining_ratio >= 1.0:
            return

        if remaining_ratio <= 0:
            self.year_to_date_strategy_returns = defaultdict(float)
            return

        for strategy_id in list(self.year_to_date_strategy_returns.keys()):
            self.year_to_date_strategy_returns[strategy_id] *= remaining_ratio

    def _process_withdrawal_crystallization(
        self,
        performance_profits_by_cohort: Dict[str, float],
        withdrawal_amount: float,
        quarter: Optional[int]
    ) -> None:
        """Pay performance allocation on redeemed capital above its HWM."""
        distributable_profits = sum(performance_profits_by_cohort.values())
        if distributable_profits <= 0:
            return

        payment_quarter = quarter if quarter is not None else -1
        author_pool = distributable_profits * PAP.PERFORMANCE_ALLOCATION
        performance_pool = author_pool * (1.0 - PAP.AUTHOR_SAFETY_NET_RATIO)
        safety_net_pool = author_pool * PAP.AUTHOR_SAFETY_NET_RATIO

        performance_allocations = self._distribute_performance_allocation(
            self.year_to_date_strategy_returns,
            performance_pool,
            payment_quarter
        )
        safety_net_allocations = self._distribute_safety_net_payments(
            safety_net_pool,
            payment_quarter
        )

        author_payments = (
            sum(performance_allocations.values())
            + sum(safety_net_allocations.values())
        )
        history_quarter = payment_quarter
        self.withdrawal_crystallization_history[history_quarter].append({
            'withdrawal_amount': withdrawal_amount,
            'distributable_profits': distributable_profits,
            'author_pool': author_pool,
            'author_payments': author_payments,
            'author_performance_total': sum(performance_allocations.values()),
            'safety_net_total': sum(safety_net_allocations.values()),
            'allocation_by_author': performance_allocations,
            'safety_net_by_author': safety_net_allocations,
            'performance_profits_by_cohort': dict(performance_profits_by_cohort)
        })

    def get_capital_cohort_summary(self) -> List[Dict[str, float]]:
        """Return current cohort-level NAV/HWM state for diagnostics."""
        return [
            {
                'cohort_id': cohort.cohort_id,
                'capital': cohort.capital,
                'high_water_mark': cohort.high_water_mark,
                'cumulative_loss_account': cohort.cumulative_loss_account,
                'annual_net_profit': cohort.annual_net_profit,
                'quarter_created': cohort.quarter_created
            }
            for cohort in self.capital_cohorts
        ]

    def get_withdrawal_crystallization_summary(
        self,
        quarter: Optional[int] = None
    ) -> Any:
        """Return redemption-triggered crystallization history."""
        if quarter is not None:
            return list(self.withdrawal_crystallization_history.get(quarter, []))

        return {
            q: list(events)
            for q, events in self.withdrawal_crystallization_history.items()
        }

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
        """Get aggregate unrecovered net investor drawdown across cohorts."""
        return sum(
            max(cohort.cumulative_loss_account - cohort.annual_net_profit, 0.0)
            for cohort in self.capital_cohorts
        )

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

        # Investor-flow performance uses net NAV return before investor flows.
        if summary.fund_aum_start <= 0:
            return 0.0

        return (
            summary.fund_aum_end - summary.fund_aum_start
        ) / summary.fund_aum_start

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

    def update_aum(self, net_flow: float, quarter: Optional[int] = None) -> None:
        """
        Update fund AUM by adding net investor flows.

        Called by Investor Flow Component after processing quarterly flows.

        Args:
            net_flow: Net flow amount in millions
                     (positive = inflows, negative = outflows)
        """
        if net_flow > 0:
            self._add_capital_cohort(net_flow, quarter)
        elif net_flow < 0:
            self._withdraw_capital_from_cohorts(abs(net_flow), quarter)
        else:
            self._sync_fund_aum_from_cohorts()

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
        total_withdrawal_payments = sum(
            event['author_payments']
            for events in self.withdrawal_crystallization_history.values()
            for event in events
        )

        return {
            'quarters_tracked': len(self.allocation_history),
            'average_efficiency': sum(efficiencies) / len(efficiencies),
            'min_efficiency': min(efficiencies),
            'max_efficiency': max(efficiencies),
            'quarters_above_hwm': quarters_above_hwm,
            'total_profits_distributed': total_distributed + total_withdrawal_payments,
            'annual_author_payments': total_distributed,
            'withdrawal_crystallization_author_payments': total_withdrawal_payments
        }

    def clear_allocation_history(self):
        """Clear allocation history (useful for testing)."""
        self.allocation_history.clear()

    def __repr__(self) -> str:
        """String representation of the manager."""
        return (
            f"PerformanceAllocationManager("
            f"aum=${self.fund_aum:.1f}M, "
            f"loss_account=${self.get_cumulative_loss_account():.1f}M, "
            f"cohorts={len(self.capital_cohorts)}, "
            f"quarters_tracked={len(self.allocation_history)})"
        )
