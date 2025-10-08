"""
External Shock Component Parameters

Configuration for crisis event generation and severity modeling.
"""


class ExternalShockParameters:
    """
    Centralized configuration for External Shock Component.

    Models financial crises using exponential arrival times and
    normal distribution for severity.
    """

    # =============================================================================
    # CRISIS FREQUENCY PARAMETERS
    # =============================================================================

    # Exponential distribution parameter for crisis timing
    CRISIS_LAMBDA = 1/40  # One crisis every 40 quarters (10 years) on average

    # =============================================================================
    # CRISIS SEVERITY PARAMETERS
    # =============================================================================

    # Base crisis drawdown (before beta scaling)
    # Sampled from normal distribution
    CRISIS_DRAWDOWN_MEAN = 20.0   # Average crisis: 20% base drawdown
    CRISIS_DRAWDOWN_STD = 5.0     # Standard deviation: 5%

    # Reasonable bounds for crisis severity (clip extreme outliers)
    CRISIS_DRAWDOWN_MIN = 5.0     # Minimum crisis severity (mild)
    CRISIS_DRAWDOWN_MAX = 40.0    # Maximum crisis severity (catastrophic)

    # Note: Actual strategy losses = base_drawdown * strategy_beta
    # Example: 20% base drawdown
    #   - Defensive strategy (beta=0.5): 10% loss
    #   - Neutral strategy (beta=1.0): 20% loss
    #   - Aggressive strategy (beta=2.0): 40% loss

    # =============================================================================
    # VALIDATION
    # =============================================================================

    @classmethod
    def validate_parameters(cls):
        """Validate parameter consistency."""
        # Crisis frequency validation
        assert cls.CRISIS_LAMBDA > 0, "Crisis lambda must be positive"
        assert cls.CRISIS_LAMBDA <= 1, "Crisis lambda should be <= 1 (at least 1 quarter between crises)"

        # Crisis severity validation
        assert cls.CRISIS_DRAWDOWN_MEAN > 0, "Crisis drawdown mean must be positive"
        assert cls.CRISIS_DRAWDOWN_STD > 0, "Crisis drawdown std must be positive"
        assert cls.CRISIS_DRAWDOWN_MIN >= 0, "Crisis drawdown min must be non-negative"
        assert cls.CRISIS_DRAWDOWN_MAX > cls.CRISIS_DRAWDOWN_MIN, "Max must be greater than min"
        assert cls.CRISIS_DRAWDOWN_MEAN >= cls.CRISIS_DRAWDOWN_MIN, "Mean should be >= min"
        assert cls.CRISIS_DRAWDOWN_MEAN <= cls.CRISIS_DRAWDOWN_MAX, "Mean should be <= max"

        return True


# Validate parameters on import
ExternalShockParameters.validate_parameters()
