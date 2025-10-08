"""
Strategy Lifecycle Component - Configuration Parameters
All parameters for strategy creation, lifecycle, and risk management
"""

class StrategyParameters:
    """Central configuration for all strategy-related parameters"""

    # ============================================
    # RETURN DISTRIBUTION PARAMETERS
    # ============================================

    # Distribution type probabilities
    STRATEGY_T_DISTRIBUTION_PROB = 0.9  # Probability of t-distribution (fat tails)
    STRATEGY_UNIFORM_DISTRIBUTION_PROB = 0.1  # Probability of uniform distribution

    # T-distribution parameters (quarterly returns in %)
    T_DISTRIBUTION_LOC_MIN = 2.0  # Minimum expected return
    T_DISTRIBUTION_LOC_MAX = 5.0  # Maximum expected return
    T_DISTRIBUTION_SCALE_MIN = 0.1  # Minimum volatility
    T_DISTRIBUTION_SCALE_MAX = 0.5  # Maximum volatility
    T_DISTRIBUTION_DEGREES_OF_FREEDOM = 3  # Fat tail parameter

    # Uniform distribution parameters (quarterly returns in %)
    UNIFORM_DISTRIBUTION_LOC_MIN = -1.0  # Minimum return start
    UNIFORM_DISTRIBUTION_LOC_MAX = 0.0  # Maximum return start
    UNIFORM_DISTRIBUTION_SCALE_MIN = 3.0  # Minimum return range
    UNIFORM_DISTRIBUTION_SCALE_MAX = 6.0  # Maximum return range

    # ============================================
    # CAPACITY PARAMETERS
    # ============================================

    # Initial capacity (in millions)
    STRATEGY_INITIAL_CAPACITY_MIN = 20  # Minimum starting capacity
    STRATEGY_INITIAL_CAPACITY_MAX = 100  # Maximum starting capacity

    # Capacity limits
    STRATEGY_MAX_CAPACITY_ABSOLUTE = 100  # Hard cap on any strategy capacity

    # ============================================
    # LIFECYCLE PARAMETERS
    # ============================================

    # Natural decay (dynamic based on current return)
    # Decay rate = STRATEGY_RETURN_DECAY_RATE × (current_return / MAX_EXPECTED_RETURN)
    # - 5% return: 3% decay rate (max)
    # - 0% return: 0% decay rate (min)
    # - Linear interpolation in between
    STRATEGY_RETURN_DECAY_RATE = 0.03  # Maximum decay rate (for strategies at 5% return)
    STRATEGY_MIN_ACTIVE_RETURN = 0.0  # Strategy becomes inactive below this

    # Improvement factors
    STRATEGY_RETURN_IMPROVEMENT_FACTOR = 0.1  # Return boost from improvement
    STRATEGY_CAPACITY_IMPROVEMENT_FACTOR_MIN = 10  # Min absolute increase
    STRATEGY_CAPACITY_IMPROVEMENT_FACTOR_MAX = 100  # Max absolute increase

    # Improvement limits
    STRATEGY_MAX_EXPECTED_RETURN = 5.0  # Cap on return after improvements (%)

    # ============================================
    # RISK PROFILE PARAMETERS
    # ============================================

    # Beta (market sensitivity)
    STRATEGY_BETA_MIN = 0.5  # Defensive strategies
    STRATEGY_BETA_MAX = 2.0  # Aggressive strategies

