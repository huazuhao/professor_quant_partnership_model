"""
Strategy Factory - Creates new strategies with randomized parameters
Handles the initialization of strategies with appropriate distributions and risk profiles
"""

import random
import uuid
from typing import List, Dict
from .strategy import Strategy
from .strategy_parameters import StrategyParameters as SP


class StrategyFactory:
    """Factory class for creating new trading strategies"""

    @staticmethod
    def create_new_strategy(
        authors: List,
        quarter: int,
        strategy_id: str = None
    ) -> Strategy:
        """
        Create a new strategy with randomized parameters

        Args:
            authors: List of Author objects creating this strategy
            quarter: Quarter when strategy is created
            strategy_id: Optional custom ID, otherwise generates UUID

        Returns:
            Strategy: Newly created strategy instance
        """

        # Generate ID if not provided
        if strategy_id is None:
            strategy_id = f"strategy_{uuid.uuid4().hex[:8]}"

        # Determine ownership splits (equal split for now)
        ownership_splits = {}
        share = 1.0 / len(authors) if authors else 1.0
        for author in authors:
            # Use author_id as key if author has that attribute, otherwise use author itself
            author_key = author.author_id if hasattr(author, 'author_id') else author
            ownership_splits[author_key] = share

        # Choose distribution type
        distribution_type = StrategyFactory._choose_distribution_type()

        # Generate return distribution parameters
        if distribution_type == 't':
            distribution_loc = random.uniform(
                SP.T_DISTRIBUTION_LOC_MIN,
                SP.T_DISTRIBUTION_LOC_MAX
            )
            distribution_scale = random.uniform(
                SP.T_DISTRIBUTION_SCALE_MIN,
                SP.T_DISTRIBUTION_SCALE_MAX
            )
        else:  # uniform
            distribution_loc = random.uniform(
                SP.UNIFORM_DISTRIBUTION_LOC_MIN,
                SP.UNIFORM_DISTRIBUTION_LOC_MAX
            )
            distribution_scale = random.uniform(
                SP.UNIFORM_DISTRIBUTION_SCALE_MIN,
                SP.UNIFORM_DISTRIBUTION_SCALE_MAX
            )

        # Generate capacity
        max_capacity = random.uniform(
            SP.STRATEGY_INITIAL_CAPACITY_MIN,
            SP.STRATEGY_INITIAL_CAPACITY_MAX
        )

        # Generate risk profile
        beta = random.uniform(SP.STRATEGY_BETA_MIN, SP.STRATEGY_BETA_MAX)

        # Create and return strategy
        strategy = Strategy(
            strategy_id=strategy_id,
            authors=authors,
            ownership_splits=ownership_splits,
            quarter_created=quarter,
            distribution_type=distribution_type,
            distribution_loc=distribution_loc,
            distribution_scale=distribution_scale,
            max_capacity=max_capacity,
            beta=beta
        )

        # Only keep strategies with positive expected returns initially
        # (This is a design choice - could be changed)
        if strategy.get_expected_return() > 0:
            return strategy
        else:
            # Retry creation with new parameters
            return StrategyFactory.create_new_strategy(authors, quarter, strategy_id)

    @staticmethod
    def _choose_distribution_type() -> str:
        """Choose distribution type based on configured probabilities"""
        rand = random.random()
        if rand < SP.STRATEGY_T_DISTRIBUTION_PROB:
            return 't'
        else:
            return 'uniform'

    @staticmethod
    def create_strategy_with_params(
        authors: List,
        quarter: int,
        distribution_type: str,
        distribution_loc: float,
        distribution_scale: float,
        max_capacity: float,
        beta: float,
        strategy_id: str = None
    ) -> Strategy:
        """
        Create a strategy with specific parameters (for testing or special cases)

        Args:
            authors: List of Author objects
            quarter: Creation quarter
            distribution_type: 't' or 'uniform'
            distribution_loc: Location parameter
            distribution_scale: Scale parameter
            max_capacity: Maximum capacity in millions
            beta: Market sensitivity
            strategy_id: Optional custom ID

        Returns:
            Strategy: Strategy with specified parameters
        """

        if strategy_id is None:
            strategy_id = f"strategy_{uuid.uuid4().hex[:8]}"

        # Equal ownership split
        ownership_splits = {}
        share = 1.0 / len(authors) if authors else 1.0
        for author in authors:
            # Use author_id as key if author has that attribute, otherwise use author itself
            author_key = author.author_id if hasattr(author, 'author_id') else author
            ownership_splits[author_key] = share


        return Strategy(
            strategy_id=strategy_id,
            authors=authors,
            ownership_splits=ownership_splits,
            quarter_created=quarter,
            distribution_type=distribution_type,
            distribution_loc=distribution_loc,
            distribution_scale=distribution_scale,
            max_capacity=max_capacity,
            beta=beta
        )