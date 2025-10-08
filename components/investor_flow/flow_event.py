"""
Flow Event data structure for Investor Flow Component.

Tracks capital flow outcomes with detailed stage-by-stage information including
Gaussian sampling, regime constraints, and magnitude caps.
"""

from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class FlowEvent:
    """
    Data structure tracking quarterly investor flow outcomes.

    Provides complete transparency into the flow calculation process including:
    - Performance context (trailing returns)
    - Gaussian distribution parameters
    - Stage-by-stage flow values (sampled → sign constrained → magnitude capped)
    - AUM before/after flows
    - Constraint application flags
    """

    # ============================================
    # QUARTER AND PERFORMANCE CONTEXT
    # ============================================

    quarter: int
    trailing_4q_returns: List[float]  # Last 4 quarterly returns (decimals)
    trailing_4q_total_return: float   # Compounded 4Q return

    # ============================================
    # GAUSSIAN DISTRIBUTION PARAMETERS
    # ============================================

    mean_flow_pct: float       # μ as % of AUM (after mean cap)
    mean_flow_dollars: float   # μ in dollars
    std_flow_pct: float        # σ as % of AUM
    std_flow_dollars: float    # σ in dollars
    aum_multiplier: float      # AUM-based sensitivity multiplier

    # ============================================
    # FLOW CALCULATION STAGES
    # ============================================

    # Stage 1: Raw Gaussian sample
    net_flow_sampled: float

    # Stage 2: After regime sign constraint (Layer 1)
    net_flow_after_sign_constraint: float

    # Stage 3: After magnitude caps (Layer 2) - FINAL
    net_flow_final: float

    # ============================================
    # AUM TRACKING
    # ============================================

    aum_before_flow: float
    aum_after_flow: float

    # ============================================
    # REGIME AND CONSTRAINT TRACKING
    # ============================================

    regime_type: str  # "positive", "negative", "zero"
    regime_constraint_applied: bool  # True if Layer 1 modified the flow
    magnitude_cap_applied: bool      # True if Layer 2 modified the flow

    def __post_init__(self):
        """Calculate derived metrics after initialization."""
        # Ensure AUM after flow is consistent
        self.aum_after_flow = self.aum_before_flow + self.net_flow_final

        # Validate regime type
        assert self.regime_type in ["positive", "negative", "zero"], \
            f"Invalid regime_type: {self.regime_type}"

    @property
    def flow_as_pct_of_aum(self) -> float:
        """Calculate final flow as percentage of AUM."""
        if self.aum_before_flow <= 0:
            return 0.0
        return self.net_flow_final / self.aum_before_flow

    @property
    def aum_growth_rate(self) -> float:
        """Calculate AUM growth rate from flows."""
        if self.aum_before_flow <= 0:
            return 0.0
        return (self.aum_after_flow - self.aum_before_flow) / self.aum_before_flow

    @property
    def any_constraint_applied(self) -> bool:
        """Check if any constraint was applied."""
        return self.regime_constraint_applied or self.magnitude_cap_applied

    def get_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive flow summary for reporting.

        Returns:
            dict: Complete flow event details
        """
        return {
            # Identification
            'quarter': self.quarter,

            # Performance
            'trailing_4q_return': self.trailing_4q_total_return,
            'trailing_returns': self.trailing_4q_returns,

            # Distribution
            'mean_flow_pct': self.mean_flow_pct,
            'std_flow_pct': self.std_flow_pct,
            'mean_flow_dollars': self.mean_flow_dollars,
            'std_flow_dollars': self.std_flow_dollars,
            'aum_multiplier': self.aum_multiplier,

            # Flow stages
            'flow_sampled': self.net_flow_sampled,
            'flow_after_sign_constraint': self.net_flow_after_sign_constraint,
            'flow_final': self.net_flow_final,

            # AUM
            'aum_before': self.aum_before_flow,
            'aum_after': self.aum_after_flow,
            'aum_growth_rate': self.aum_growth_rate,
            'flow_pct_of_aum': self.flow_as_pct_of_aum,

            # Constraints
            'regime_type': self.regime_type,
            'regime_constraint_applied': self.regime_constraint_applied,
            'magnitude_cap_applied': self.magnitude_cap_applied,
            'any_constraint_applied': self.any_constraint_applied
        }

    def get_constraint_summary(self) -> str:
        """
        Get human-readable constraint summary.

        Returns:
            str: Description of constraints applied
        """
        if not self.any_constraint_applied:
            return "No constraints applied"

        messages = []
        if self.regime_constraint_applied:
            messages.append(f"Regime constraint ({self.regime_type})")
        if self.magnitude_cap_applied:
            messages.append("Magnitude cap")

        return " + ".join(messages)
