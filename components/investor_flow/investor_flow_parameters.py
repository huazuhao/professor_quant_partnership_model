"""
Parameter configuration for Investor Flow Component.

Implements continuous linear Gaussian model with regime-dependent sign constraints:
- Linear mapping: flow_mean = α × trailing_return
- Gaussian noise: flow ~ N(mean, volatility × AUM)
- Regime constraints: positive returns → no outflows, negative returns → no inflows
- Hard caps: maximum ±10% AUM flows per quarter
"""


class InvestorFlowParameters:
    """
    Continuous linear Gaussian model with regime-dependent sign constraints.

    Flow Model:
        μ = clip(α × R_4Q, -MAX_MEAN, +MAX_MEAN) × AUM
        σ = VOLATILITY × AUM
        Flow ~ N(μ, σ) with regime sign constraint and magnitude caps
    """

    # ============================================
    # PERFORMANCE TRACKING
    # ============================================

    # Number of quarters for trailing performance calculation
    PERFORMANCE_LOOKBACK_QUARTERS = 4

    # ============================================
    # LINEAR FLOW MAPPING
    # ============================================

    # Flow sensitivity: how responsive flows are to performance
    # α = 0.5 means: +10% return → +5% AUM mean inflow (before caps)
    FLOW_SENSITIVITY_ALPHA = 0.5

    # Maximum mean flow as percentage of AUM (caps the linear function)
    # Prevents extreme mean flows from very high/low returns
    MAX_MEAN_FLOW_PCT = 0.05  # ±5% AUM max mean

    # ============================================
    # AUM-BASED SENSITIVITY SCALING
    # ============================================

    # Enable AUM-based multiplier for flow sensitivity
    # Smaller funds have higher flow volatility (as % of AUM)
    AUM_MULTIPLIER_ENABLED = True

    # AUM thresholds for multiplier scaling
    AUM_MULTIPLIER_MIN_AUM = 10.0      # $10M → high multiplier
    AUM_MULTIPLIER_MAX_AUM = 1000.0    # $1,000M (1B) → multiplier = 1

    # Multiplier values at thresholds
    AUM_MULTIPLIER_AT_MIN_AUM = 10.0   # 10x sensitivity for small funds
    AUM_MULTIPLIER_AT_MAX_AUM = 1.0    # 1x sensitivity for large funds

    # ============================================
    # GAUSSIAN DISTRIBUTION PARAMETERS
    # ============================================

    # Flow volatility: standard deviation as percentage of AUM
    # Represents noise and uncertainty in investor behavior
    FLOW_VOLATILITY_PCT = 0.10  # 10% of AUM

    # ============================================
    # HARD CAPS - LAYER 1: REGIME SIGN CONSTRAINT
    # ============================================

    # Force flow sign to match performance regime direction
    # If True: positive returns → only inflows, negative returns → only outflows
    ENFORCE_REGIME_SIGN = True

    # Tolerance for "zero" return (within this range, allow any sign)
    # Returns within ±0.1% are considered "neutral" and allow bidirectional flows
    ZERO_RETURN_TOLERANCE = 0.001  # ±0.1% considered "zero"

    # ============================================
    # HARD CAPS - LAYER 2: MAGNITUDE CONSTRAINTS
    # ============================================

    # Maximum inflow in any quarter (as % of AUM)
    MAX_INFLOW_PCT = 1.0  # No more than 100% AUM inflow (fund can double)

    # Maximum outflow in any quarter (as % of AUM)
    MAX_OUTFLOW_PCT = 0.5  # No more than 50% AUM outflow (fund can halve)

    # ============================================
    # VALIDATION
    # ============================================

    @classmethod
    def validate_parameters(cls):
        """
        Validate parameter ranges and consistency.

        Raises:
            AssertionError: If parameters are invalid
        """
        # Sensitivity must be non-negative
        assert cls.FLOW_SENSITIVITY_ALPHA >= 0, \
            "FLOW_SENSITIVITY_ALPHA must be >= 0"

        # Percentages must be in valid range
        assert 0 < cls.MAX_MEAN_FLOW_PCT <= 1.0, \
            "MAX_MEAN_FLOW_PCT must be in (0, 1]"
        assert 0 < cls.FLOW_VOLATILITY_PCT <= 1.0, \
            "FLOW_VOLATILITY_PCT must be in (0, 1]"
        assert 0 < cls.MAX_INFLOW_PCT <= 1.0, \
            "MAX_INFLOW_PCT must be in (0, 1]"
        assert 0 < cls.MAX_OUTFLOW_PCT <= 1.0, \
            "MAX_OUTFLOW_PCT must be in (0, 1]"

        # Lookback period must be positive
        assert cls.PERFORMANCE_LOOKBACK_QUARTERS >= 1, \
            "PERFORMANCE_LOOKBACK_QUARTERS must be >= 1"

        # Tolerance must be non-negative
        assert cls.ZERO_RETURN_TOLERANCE >= 0, \
            "ZERO_RETURN_TOLERANCE must be >= 0"

        # Mean cap (scaled by max multiplier) should be <= hard caps
        max_scaled_mean_cap = cls.MAX_MEAN_FLOW_PCT * cls.AUM_MULTIPLIER_AT_MIN_AUM
        assert max_scaled_mean_cap <= cls.MAX_INFLOW_PCT, \
            f"Scaled mean cap ({max_scaled_mean_cap}) should be <= MAX_INFLOW_PCT ({cls.MAX_INFLOW_PCT})"
        assert max_scaled_mean_cap <= cls.MAX_OUTFLOW_PCT, \
            f"Scaled mean cap ({max_scaled_mean_cap}) should be <= MAX_OUTFLOW_PCT ({cls.MAX_OUTFLOW_PCT})"

        # AUM multiplier validation
        assert cls.AUM_MULTIPLIER_MIN_AUM > 0, \
            "AUM_MULTIPLIER_MIN_AUM must be > 0"
        assert cls.AUM_MULTIPLIER_MAX_AUM > cls.AUM_MULTIPLIER_MIN_AUM, \
            "AUM_MULTIPLIER_MAX_AUM must be > AUM_MULTIPLIER_MIN_AUM"
        assert cls.AUM_MULTIPLIER_AT_MIN_AUM > 0, \
            "AUM_MULTIPLIER_AT_MIN_AUM must be > 0"
        assert cls.AUM_MULTIPLIER_AT_MAX_AUM > 0, \
            "AUM_MULTIPLIER_AT_MAX_AUM must be > 0"

    @classmethod
    def get_parameter_summary(cls) -> dict:
        """
        Get summary of all parameters for logging/debugging.

        Returns:
            dict: Parameter names and values
        """
        return {
            'lookback_quarters': cls.PERFORMANCE_LOOKBACK_QUARTERS,
            'sensitivity_alpha': cls.FLOW_SENSITIVITY_ALPHA,
            'max_mean_flow_pct': cls.MAX_MEAN_FLOW_PCT,
            'aum_multiplier_enabled': cls.AUM_MULTIPLIER_ENABLED,
            'aum_multiplier_min_aum': cls.AUM_MULTIPLIER_MIN_AUM,
            'aum_multiplier_max_aum': cls.AUM_MULTIPLIER_MAX_AUM,
            'aum_multiplier_at_min_aum': cls.AUM_MULTIPLIER_AT_MIN_AUM,
            'aum_multiplier_at_max_aum': cls.AUM_MULTIPLIER_AT_MAX_AUM,
            'flow_volatility_pct': cls.FLOW_VOLATILITY_PCT,
            'enforce_regime_sign': cls.ENFORCE_REGIME_SIGN,
            'zero_return_tolerance': cls.ZERO_RETURN_TOLERANCE,
            'max_inflow_pct': cls.MAX_INFLOW_PCT,
            'max_outflow_pct': cls.MAX_OUTFLOW_PCT
        }


# Validate parameters on module import
InvestorFlowParameters.validate_parameters()
