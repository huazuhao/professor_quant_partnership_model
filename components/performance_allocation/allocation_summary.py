"""
Allocation Summary data structure for Performance Allocation Component.

This module provides comprehensive tracking and reporting for quarterly
performance allocation outcomes, including profit distribution, author payments,
and safety net operations.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


@dataclass
class AllocationSummary:
    """
    Comprehensive data structure tracking quarterly performance allocation outcomes.

    Tracks the complete flow from strategy returns through high water mark accounting
    to final distribution among fund, authors, and safety net program.
    """

    # Quarter identification
    quarter: int

    # Input metrics
    total_strategy_returns: float
    fund_aum_start: float

    # Management fee calculation
    management_fee_charged: float

    # High water mark accounting
    cumulative_loss_account_start: float
    cumulative_loss_account_end: float
    distributable_profits: float  # After high water mark check
    high_water_mark_met: bool

    # Three-way profit distribution
    fund_retention: float           # ~80% of distributable profits
    author_performance_total: float # ~16% of distributable profits
    safety_net_total: float        # ~4% of distributable profits

    # Detailed allocation tracking
    allocation_by_author: Dict[str, float] = field(default_factory=dict)  # Performance allocations
    safety_net_by_author: Dict[str, float] = field(default_factory=dict)  # Safety net payments

    # Summary metrics
    total_authors_receiving_performance: int = 0
    total_authors_receiving_safety_net: int = 0
    average_performance_allocation: float = 0.0
    average_safety_net_payment: float = 0.0

    # Fund state after allocation
    fund_aum_end: float = 0.0

    def __post_init__(self):
        """Calculate derived metrics after initialization."""
        self._calculate_summary_metrics()

    def _calculate_summary_metrics(self):
        """Calculate summary statistics from detailed allocations."""
        # Performance allocation metrics
        self.total_authors_receiving_performance = len(self.allocation_by_author)
        if self.total_authors_receiving_performance > 0:
            self.average_performance_allocation = (
                self.author_performance_total / self.total_authors_receiving_performance
            )

        # Safety net metrics
        self.total_authors_receiving_safety_net = len(self.safety_net_by_author)
        if self.total_authors_receiving_safety_net > 0:
            self.average_safety_net_payment = (
                self.safety_net_total / self.total_authors_receiving_safety_net
            )

        # Fund AUM after allocation
        # Flow: Start AUM - Management Fee + Strategy Returns - Author Payments
        self.fund_aum_end = (
            self.fund_aum_start
            - self.management_fee_charged
            + self.total_strategy_returns
            - self.author_performance_total
            - self.safety_net_total
        )

    def get_allocation_efficiency(self) -> float:
        """Get allocation efficiency (distributable profits / total returns)."""
        if self.total_strategy_returns <= 0:
            return 0.0
        return self.distributable_profits / self.total_strategy_returns

    def get_total_author_payments(self) -> float:
        """Get total payments to all authors (performance + safety net)."""
        return self.author_performance_total + self.safety_net_total

    def get_fund_retention_rate(self) -> float:
        """Get actual fund retention rate from this quarter."""
        if self.distributable_profits <= 0:
            return 0.0
        return self.fund_retention / self.distributable_profits

    def get_summary(self) -> Dict[str, Any]:
        """Generate comprehensive allocation summary report."""
        return {
            'quarter': self.quarter,
            'fund_metrics': {
                'aum_start': self.fund_aum_start,
                'aum_end': self.fund_aum_end,
                'management_fee': self.management_fee_charged,
                'fund_retention': self.fund_retention,
                'retention_rate': self.get_fund_retention_rate()
            },
            'strategy_returns': {
                'total_returns': self.total_strategy_returns,
                'distributable_profits': self.distributable_profits,
                'allocation_efficiency': self.get_allocation_efficiency()
            },
            'high_water_mark': {
                'hwm_met': self.high_water_mark_met,
                'loss_account_start': self.cumulative_loss_account_start,
                'loss_account_end': self.cumulative_loss_account_end
            },
            'author_performance': {
                'total_allocated': self.author_performance_total,
                'authors_receiving': self.total_authors_receiving_performance,
                'average_payment': self.average_performance_allocation,
                'allocations': dict(self.allocation_by_author)
            },
            'safety_net': {
                'total_distributed': self.safety_net_total,
                'authors_receiving': self.total_authors_receiving_safety_net,
                'average_payment': self.average_safety_net_payment,
                'payments': dict(self.safety_net_by_author)
            },
            'total_author_payments': self.get_total_author_payments()
        }

    def get_top_performance_allocations(self, n: int = 5) -> Dict[str, float]:
        """Get top N performance allocations by amount."""
        sorted_allocations = sorted(
            self.allocation_by_author.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return dict(sorted_allocations[:n])

    def get_authors_by_payment_type(self) -> Dict[str, List[str]]:
        """Categorize authors by payment type received."""
        performance_only = set(self.allocation_by_author.keys()) - set(self.safety_net_by_author.keys())
        safety_net_only = set(self.safety_net_by_author.keys()) - set(self.allocation_by_author.keys())
        both_payments = set(self.allocation_by_author.keys()) & set(self.safety_net_by_author.keys())

        return {
            'performance_only': list(performance_only),
            'safety_net_only': list(safety_net_only),
            'both_payments': list(both_payments),
            'no_payments': []  # Will be populated by external tracking
        }

    def __repr__(self) -> str:
        """String representation of allocation summary."""
        return (
            f"AllocationSummary(quarter={self.quarter}, "
            f"returns=${self.total_strategy_returns:.1f}M, "
            f"hwm_met={self.high_water_mark_met}, "
            f"authors_paid={self.total_authors_receiving_performance + self.total_authors_receiving_safety_net})"
        )