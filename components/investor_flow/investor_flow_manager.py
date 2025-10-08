"""
Investor Flow Manager for Investor Flow Component.

Main orchestrator for quarterly capital inflows and outflows based on fund performance.
Implements continuous linear Gaussian model with regime-dependent two-layer clipping.

Algorithm:
    1. Track trailing 4Q performance
    2. Calculate linear flow mean: μ = α × R_4Q × AUM
    3. Sample from Gaussian: Flow ~ N(μ, σ)
    4. Apply Layer 1 (regime sign constraint)
    5. Apply Layer 2 (magnitude caps)
    6. Return FlowEvent with complete details
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
from .investor_flow_parameters import InvestorFlowParameters as IFP
from .flow_event import FlowEvent


class InvestorFlowManager:
    """
    Main component for managing quarterly investor capital flows.

    Implements performance-based flow logic with two-layer clipping:
    - Layer 1: Regime sign constraint (positive returns → no outflows)
    - Layer 2: Magnitude caps (max ±10% AUM)
    """

    def __init__(self):
        """Initialize the Investor Flow Manager."""
        self.flow_history: Dict[int, FlowEvent] = {}
        self.quarterly_returns_history: List[float] = []  # Decimal returns

    def process_quarterly_flows(
        self,
        current_aum: float,
        quarterly_return: float,
        quarter: int
    ) -> FlowEvent:
        """
        Process quarterly investor flows based on trailing performance.

        Args:
            current_aum: Current fund AUM before flows ($M)
            quarterly_return: This quarter's return (decimal, e.g., 0.05 = 5%)
            quarter: Current quarter number

        Returns:
            FlowEvent: Complete flow outcome with all stages tracked
        """
        # Step 1: Update return history
        self._update_return_history(quarterly_return)

        # Step 2: Get trailing performance
        trailing_returns = self._get_trailing_returns(IFP.PERFORMANCE_LOOKBACK_QUARTERS)
        trailing_total_return = self._calculate_trailing_performance(trailing_returns)

        # Step 3: Determine regime
        regime_type = self._determine_regime(trailing_total_return)

        # Step 4: Calculate Gaussian parameters
        mean_pct, mean_dollars, std_pct, std_dollars, aum_multiplier = self._calculate_distribution_parameters(
            trailing_total_return, current_aum
        )

        # Step 5: Sample from Gaussian
        net_flow_sampled = self._sample_from_gaussian(mean_dollars, std_dollars)

        # Step 6: Apply Layer 1 - Regime sign constraint
        net_flow_sign_constrained, regime_applied = self._apply_regime_sign_constraint(
            net_flow_sampled, trailing_total_return
        )

        # Step 7: Apply Layer 2 - Magnitude caps
        net_flow_final, magnitude_applied = self._apply_magnitude_caps(
            net_flow_sign_constrained, current_aum
        )

        # Step 8: Create flow event
        flow_event = FlowEvent(
            quarter=quarter,
            trailing_4q_returns=trailing_returns,
            trailing_4q_total_return=trailing_total_return,
            mean_flow_pct=mean_pct,
            mean_flow_dollars=mean_dollars,
            std_flow_pct=std_pct,
            std_flow_dollars=std_dollars,
            aum_multiplier=aum_multiplier,
            net_flow_sampled=net_flow_sampled,
            net_flow_after_sign_constraint=net_flow_sign_constrained,
            net_flow_final=net_flow_final,
            aum_before_flow=current_aum,
            aum_after_flow=current_aum + net_flow_final,
            regime_type=regime_type,
            regime_constraint_applied=regime_applied,
            magnitude_cap_applied=magnitude_applied
        )

        # Step 9: Store in history
        self.flow_history[quarter] = flow_event

        return flow_event

    # ============================================
    # HELPER METHODS - RETURN TRACKING
    # ============================================

    def _update_return_history(self, quarterly_return: float) -> None:
        """Add new quarterly return to history."""
        self.quarterly_returns_history.append(quarterly_return)

    def _get_trailing_returns(self, quarters: int) -> List[float]:
        """
        Get last N quarters of returns.

        Args:
            quarters: Number of quarters to look back

        Returns:
            List of returns (may be shorter than requested if insufficient history)
        """
        if len(self.quarterly_returns_history) < quarters:
            return self.quarterly_returns_history.copy()
        return self.quarterly_returns_history[-quarters:]

    def _calculate_trailing_performance(self, trailing_returns: List[float]) -> float:
        """
        Calculate compounded trailing return.

        Args:
            trailing_returns: List of quarterly returns (decimals)

        Returns:
            Compounded return over the period
        """
        if not trailing_returns:
            return 0.0

        # Compound returns: (1+r1)(1+r2)...(1+rn) - 1
        compounded = 1.0
        for r in trailing_returns:
            compounded *= (1.0 + r)

        return compounded - 1.0

    # ============================================
    # HELPER METHODS - REGIME DETERMINATION
    # ============================================

    def _determine_regime(self, trailing_return: float) -> str:
        """
        Determine performance regime based on trailing return.

        Args:
            trailing_return: Trailing compounded return

        Returns:
            "positive", "negative", or "zero"
        """
        tolerance = IFP.ZERO_RETURN_TOLERANCE

        if trailing_return > tolerance:
            return "positive"
        elif trailing_return < -tolerance:
            return "negative"
        else:
            return "zero"

    # ============================================
    # HELPER METHODS - AUM MULTIPLIER
    # ============================================

    def _calculate_aum_multiplier(self, current_aum: float) -> float:
        """
        Calculate AUM-based sensitivity multiplier.

        Smaller funds have higher flow sensitivity (as % of AUM).
        Linear interpolation between min and max AUM thresholds.

        Args:
            current_aum: Current fund AUM ($M)

        Returns:
            Multiplier value (1.0 for large funds, up to 10.0 for small funds)
        """
        if not IFP.AUM_MULTIPLIER_ENABLED:
            return 1.0

        # Above max threshold → use max multiplier (1.0 for large funds)
        if current_aum >= IFP.AUM_MULTIPLIER_MAX_AUM:
            return IFP.AUM_MULTIPLIER_AT_MAX_AUM

        # Below min threshold → use min multiplier (10.0 for small funds)
        if current_aum <= IFP.AUM_MULTIPLIER_MIN_AUM:
            return IFP.AUM_MULTIPLIER_AT_MIN_AUM

        # Linear interpolation between thresholds
        aum_range = IFP.AUM_MULTIPLIER_MAX_AUM - IFP.AUM_MULTIPLIER_MIN_AUM
        multiplier_range = IFP.AUM_MULTIPLIER_AT_MAX_AUM - IFP.AUM_MULTIPLIER_AT_MIN_AUM
        slope = multiplier_range / aum_range

        multiplier = IFP.AUM_MULTIPLIER_AT_MIN_AUM + slope * (current_aum - IFP.AUM_MULTIPLIER_MIN_AUM)

        return multiplier

    # ============================================
    # HELPER METHODS - DISTRIBUTION PARAMETERS
    # ============================================

    def _calculate_distribution_parameters(
        self,
        trailing_return: float,
        current_aum: float
    ) -> Tuple[float, float, float, float, float]:
        """
        Calculate Gaussian distribution parameters.

        Args:
            trailing_return: Trailing compounded return
            current_aum: Current AUM

        Returns:
            (mean_pct, mean_dollars, std_pct, std_dollars, aum_multiplier)
        """
        # Step 0: Calculate AUM-based sensitivity multiplier
        aum_multiplier = self._calculate_aum_multiplier(current_aum)

        # Step 1: Calculate uncapped mean flow percentage (with AUM multiplier)
        mean_pct_raw = IFP.FLOW_SENSITIVITY_ALPHA * trailing_return * aum_multiplier

        # Step 2: Apply scaled mean cap (cap scales with AUM multiplier)
        scaled_mean_cap = IFP.MAX_MEAN_FLOW_PCT * aum_multiplier
        mean_pct = np.clip(
            mean_pct_raw,
            -scaled_mean_cap,
            scaled_mean_cap
        )

        # Step 3: Convert to dollars
        mean_dollars = mean_pct * current_aum

        # Step 4: Standard deviation (constant as % of AUM)
        std_pct = IFP.FLOW_VOLATILITY_PCT
        std_dollars = std_pct * current_aum

        return mean_pct, mean_dollars, std_pct, std_dollars, aum_multiplier

    # ============================================
    # HELPER METHODS - FLOW SAMPLING
    # ============================================

    def _sample_from_gaussian(self, mean: float, std: float) -> float:
        """
        Sample flow amount from Gaussian distribution.

        Args:
            mean: Mean flow in dollars
            std: Standard deviation in dollars

        Returns:
            Sampled flow amount
        """
        return np.random.normal(mean, std)

    # ============================================
    # HELPER METHODS - LAYER 1: REGIME CONSTRAINT
    # ============================================

    def _apply_regime_sign_constraint(
        self,
        net_flow: float,
        trailing_return: float
    ) -> Tuple[float, bool]:
        """
        Apply regime-dependent sign constraint (Layer 1).

        Args:
            net_flow: Sampled flow from Gaussian
            trailing_return: Trailing compounded return

        Returns:
            (constrained_flow, was_applied)
        """
        if not IFP.ENFORCE_REGIME_SIGN:
            return net_flow, False

        tolerance = IFP.ZERO_RETURN_TOLERANCE

        # Positive regime: force non-negative
        if trailing_return > tolerance:
            constrained = max(net_flow, 0.0)
            return constrained, (constrained != net_flow)

        # Negative regime: force non-positive
        elif trailing_return < -tolerance:
            constrained = min(net_flow, 0.0)
            return constrained, (constrained != net_flow)

        # Zero regime: allow either sign
        else:
            return net_flow, False

    # ============================================
    # HELPER METHODS - LAYER 2: MAGNITUDE CAPS
    # ============================================

    def _apply_magnitude_caps(
        self,
        net_flow: float,
        current_aum: float
    ) -> Tuple[float, bool]:
        """
        Apply magnitude caps (Layer 2).

        Args:
            net_flow: Flow after sign constraint
            current_aum: Current AUM

        Returns:
            (capped_flow, was_applied)
        """
        max_inflow = IFP.MAX_INFLOW_PCT * current_aum
        max_outflow = IFP.MAX_OUTFLOW_PCT * current_aum

        capped = np.clip(net_flow, -max_outflow, max_inflow)

        return capped, (capped != net_flow)

    # ============================================
    # QUERY METHODS
    # ============================================

    def get_flow_event(self, quarter: int) -> Optional[FlowEvent]:
        """Get flow event for specific quarter."""
        return self.flow_history.get(quarter)

    def get_flow_summary(self, quarter: int) -> Optional[Dict]:
        """Get detailed flow summary for specific quarter."""
        event = self.flow_history.get(quarter)
        return event.get_summary() if event else None

    def get_all_flow_events(self) -> Dict[int, FlowEvent]:
        """Get all flow events."""
        return self.flow_history.copy()

    def get_flow_efficiency_stats(self) -> Dict:
        """
        Get flow efficiency statistics across all quarters.

        Returns:
            Dict with aggregate flow statistics
        """
        if not self.flow_history:
            return {
                'total_quarters': 0,
                'avg_flow_pct': 0.0,
                'total_net_flows': 0.0,
                'regime_constraint_count': 0,
                'magnitude_cap_count': 0
            }

        total_quarters = len(self.flow_history)
        total_flows = sum(event.net_flow_final for event in self.flow_history.values())
        regime_constraints = sum(
            1 for event in self.flow_history.values() if event.regime_constraint_applied
        )
        magnitude_caps = sum(
            1 for event in self.flow_history.values() if event.magnitude_cap_applied
        )

        # Calculate average flow as % of AUM
        flow_pcts = [
            event.flow_as_pct_of_aum for event in self.flow_history.values()
        ]
        avg_flow_pct = sum(flow_pcts) / len(flow_pcts) if flow_pcts else 0.0

        return {
            'total_quarters': total_quarters,
            'avg_flow_pct': avg_flow_pct,
            'total_net_flows': total_flows,
            'regime_constraint_count': regime_constraints,
            'regime_constraint_rate': regime_constraints / total_quarters,
            'magnitude_cap_count': magnitude_caps,
            'magnitude_cap_rate': magnitude_caps / total_quarters
        }
