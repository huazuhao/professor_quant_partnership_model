"""
Performance Allocation Component Parameters

This module contains all tunable parameters for the Performance Allocation Component.
These parameters control management fees, performance allocation, and safety net operations.
All values match iteration_one config.py exactly.
"""


class PerformanceAllocationParameters:
    """
    Central configuration for Performance Allocation Component.
    All values match iteration_one config.py exactly.
    """

    # ============================================
    # FUND INITIALIZATION
    # ============================================
    FUND_INITIAL_AUM = 10.0  # $10M initial fund size (millions)

    # ============================================
    # MANAGEMENT FEE PARAMETERS
    # ============================================
    MANAGEMENT_FEE_RATE = 0.25  # 0.25% of AUM per quarter

    # ============================================
    # PERFORMANCE ALLOCATION PARAMETERS
    # ============================================
    PERFORMANCE_ALLOCATION = 0.2  # 20% of profits to authors
    AUTHOR_SAFETY_NET_RATIO = 0.2  # 20% of author allocation to safety net
    AUTHOR_GUARANTEED_RETURN = 1.0  # $1M lifetime minimum (millions)

    # ============================================
    # DERIVED CONSTANTS (computed from above)
    # ============================================

    @classmethod
    def get_fund_retention_rate(cls) -> float:
        """Get fund retention rate (1 - performance allocation)"""
        return 1.0 - cls.PERFORMANCE_ALLOCATION

    @classmethod
    def get_author_performance_rate(cls) -> float:
        """Get author performance rate (performance allocation * (1 - safety net ratio))"""
        return cls.PERFORMANCE_ALLOCATION * (1.0 - cls.AUTHOR_SAFETY_NET_RATIO)

    @classmethod
    def get_safety_net_rate(cls) -> float:
        """Get safety net rate (performance allocation * safety net ratio)"""
        return cls.PERFORMANCE_ALLOCATION * cls.AUTHOR_SAFETY_NET_RATIO

    @classmethod
    def get_management_fee_decimal(cls) -> float:
        """Get management fee as decimal (rate / 100)"""
        return cls.MANAGEMENT_FEE_RATE / 100.0