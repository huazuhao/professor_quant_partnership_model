"""
Strategy Class - Core strategy lifecycle management
Handles individual strategy behavior, decay, improvements, and returns
"""

import random
from scipy.stats import t, uniform
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from .strategy_parameters import StrategyParameters as SP


@dataclass
class Strategy:
    """Individual trading strategy with lifecycle management"""

    strategy_id: str
    authors: List  # List of Author objects
    ownership_splits: Dict  # {author: ownership_percentage}
    quarter_created: int

    # Return characteristics
    distribution_type: str  # 't' or 'uniform'
    distribution_loc: float
    distribution_scale: float

    # Capacity
    max_capacity: float

    # Risk profile
    beta: float

    # Fields with defaults (must come after non-default fields)
    active_capacity: float = 0.0
    is_active: bool = True
    quarters_since_creation: int = 0
    last_improvement_quarter: int = -1
    total_improvements: int = 0
    cumulative_returns: float = 0.0
    quarterly_returns: List[float] = field(default_factory=list)
    distribution: Optional[object] = field(default=None, init=False)

    def __post_init__(self):
        """Initialize the distribution after dataclass initialization"""
        self._create_distribution()

    def _create_distribution(self):
        """Create the return distribution based on type and parameters"""
        if self.distribution_type == 't':
            self.distribution = t(
                loc=self.distribution_loc,
                scale=self.distribution_scale,
                df=SP.T_DISTRIBUTION_DEGREES_OF_FREEDOM
            )
        elif self.distribution_type == 'uniform':
            self.distribution = uniform(
                loc=self.distribution_loc,
                scale=self.distribution_scale
            )

    def apply_natural_decay(self):
        """
        Apply quarterly natural performance decay with dynamic decay rate.

        Decay rate varies linearly with expected return:
        - Expected return >= 5%: decay_rate = 10% (max)
        - Expected return = 0%: decay_rate = 0% (min)
        - In between: linear interpolation

        Formula: decay_rate = MAX_DECAY_RATE × (expected_return / MAX_EXPECTED_RETURN)
        """
        if not self.is_active:
            return

        # Calculate current expected return
        expected_return = self.get_expected_return()
        if expected_return > 0:
            # Calculate dynamic decay rate (linear interpolation)
            # Good strategies (high return) decay faster
            # Bad strategies (low return) decay slower
            dynamic_decay_rate = SP.STRATEGY_RETURN_DECAY_RATE * (
                min(expected_return, SP.STRATEGY_MAX_EXPECTED_RETURN) / SP.STRATEGY_MAX_EXPECTED_RETURN
            )

            decay_amount = expected_return * dynamic_decay_rate
            self.distribution_loc -= decay_amount

            # Recreate distribution with new parameters
            self._create_distribution()

            # Check if strategy should become inactive
            if self.get_expected_return() < SP.STRATEGY_MIN_ACTIVE_RETURN:
                self.is_active = False

    def can_improve_returns(self) -> bool:
        """
        Check if strategy returns can be improved.

        Returns:
            bool: True if strategy is active and below max expected return cap
        """
        if not self.is_active:
            return False

        expected_return = self.get_expected_return()
        return expected_return < SP.STRATEGY_MAX_EXPECTED_RETURN

    def improve_returns(self, quarter: int) -> bool:
        """
        Improve strategy returns
        Returns True if improvement successful, False if at cap
        """
        if not self.is_active:
            return False

        expected_return = self.get_expected_return()

        # Check if already at maximum
        if expected_return >= SP.STRATEGY_MAX_EXPECTED_RETURN:
            return False

        # Calculate improvement amount
        improvement_amount = abs(expected_return) * SP.STRATEGY_RETURN_IMPROVEMENT_FACTOR
        self.distribution_loc += improvement_amount

        # Cap at maximum
        if self.get_expected_return() > SP.STRATEGY_MAX_EXPECTED_RETURN:
            # Adjust to exactly hit the cap
            excess = self.get_expected_return() - SP.STRATEGY_MAX_EXPECTED_RETURN
            self.distribution_loc -= excess

        # Recreate distribution and update tracking
        self._create_distribution()
        self.last_improvement_quarter = quarter
        self.total_improvements += 1

        return True

    def can_improve_capacity(self) -> bool:
        """
        Check if strategy capacity can be improved.

        Returns:
            bool: True if strategy is active and below max capacity cap
        """
        if not self.is_active:
            return False

        return self.max_capacity < SP.STRATEGY_MAX_CAPACITY_ABSOLUTE

    def improve_capacity(self, quarter: int) -> bool:
        """
        Improve strategy capacity
        Returns True if improvement successful, False if at cap
        """
        if not self.is_active:
            return False

        # Check if already at maximum
        if self.max_capacity >= SP.STRATEGY_MAX_CAPACITY_ABSOLUTE:
            return False

        # Calculate improvement multiplier (inverse to current capacity)
        improvement_factor = random.uniform(
            SP.STRATEGY_CAPACITY_IMPROVEMENT_FACTOR_MIN,
            SP.STRATEGY_CAPACITY_IMPROVEMENT_FACTOR_MAX
        )
        capacity_multiplier = 1 + (improvement_factor / self.max_capacity)

        # Apply improvement with cap
        new_capacity = min(
            self.max_capacity * capacity_multiplier,
            SP.STRATEGY_MAX_CAPACITY_ABSOLUTE
        )

        self.max_capacity = new_capacity
        self.last_improvement_quarter = quarter
        self.total_improvements += 1

        return True

    def generate_quarterly_return(self, allocated_capital: float) -> float:
        """
        Generate return for the quarter based on allocated capital
        Returns dollar amount of profit/loss
        """
        if not self.is_active or allocated_capital <= 0:
            return 0.0

        # Sample return percentage from distribution
        return_percentage = self.distribution.rvs() / 100.0  # Convert to decimal

        # Calculate dollar return
        dollar_return = allocated_capital * return_percentage

        # Track performance
        self.quarterly_returns.append(return_percentage)
        self.cumulative_returns += dollar_return

        return dollar_return

    def apply_crisis_drawdown(self, base_drawdown: float) -> float:
        """
        Apply crisis impact scaled by beta
        Returns the actual loss amount
        """
        if not self.is_active or self.active_capacity <= 0:
            return 0.0

        # Scale drawdown by beta
        strategy_drawdown = base_drawdown * self.beta

        # Calculate dollar loss
        dollar_loss = self.active_capacity * (strategy_drawdown / 100.0)

        # Track the loss
        self.cumulative_returns -= dollar_loss

        return dollar_loss

    def get_expected_return(self) -> float:
        """Get the expected return percentage"""
        if self.distribution:
            return self.distribution.mean()
        return 0.0

    def get_return_volatility(self) -> float:
        """Get the return volatility (standard deviation)"""
        if self.distribution:
            return self.distribution.std()
        return 0.0

    def advance_quarter(self):
        """Update quarter-based tracking"""
        self.quarters_since_creation += 1

    def set_active_capacity(self, capacity: float):
        """Set the actively deployed capital for this strategy"""
        self.active_capacity = min(capacity, self.max_capacity)

    def __repr__(self):
        return (
            f"Strategy(id={self.strategy_id}, "
            f"type={self.distribution_type}, "
            f"expected_return={self.get_expected_return():.2f}%, "
            f"capacity={self.max_capacity:.1f}M, "
            f"beta={self.beta:.2f}, "
            f"active={self.is_active})"
        )