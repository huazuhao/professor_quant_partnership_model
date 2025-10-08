"""
Crisis Event Data Structure

Records complete information about a crisis event including timing,
severity, and impact on individual strategies.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class CrisisEvent:
    """
    Comprehensive record of a crisis event.

    Tracks whether a crisis occurred, its severity, and the resulting
    losses across all strategies.
    """

    # Event identification
    quarter: int                            # Quarter when checked
    occurred: bool                          # Whether crisis occurred this quarter

    # Crisis severity
    base_drawdown: float                    # Base drawdown percentage (before beta scaling)

    # Crisis impact
    losses_by_strategy: Dict[str, float]    # Dollar losses per strategy_id
    total_losses: float                     # Total dollar losses across all strategies

    # Derived metrics
    @property
    def num_strategies_affected(self) -> int:
        """Number of strategies that suffered losses."""
        return len(self.losses_by_strategy)

    @property
    def average_loss_per_strategy(self) -> float:
        """Average loss per affected strategy."""
        if self.num_strategies_affected == 0:
            return 0.0
        return self.total_losses / self.num_strategies_affected

    def get_summary(self) -> Dict:
        """
        Get complete summary of crisis event.

        Returns:
            Dict with all crisis details
        """
        return {
            'quarter': self.quarter,
            'occurred': self.occurred,
            'base_drawdown': self.base_drawdown,
            'total_losses': self.total_losses,
            'num_strategies_affected': self.num_strategies_affected,
            'average_loss_per_strategy': self.average_loss_per_strategy,
            'losses_by_strategy': self.losses_by_strategy.copy()
        }

    def __repr__(self) -> str:
        """String representation of crisis event."""
        if not self.occurred:
            return f"CrisisEvent(quarter={self.quarter}, occurred=False)"

        return (
            f"CrisisEvent(quarter={self.quarter}, "
            f"base_drawdown={self.base_drawdown:.1f}%, "
            f"total_losses=${self.total_losses:.1f}M, "
            f"strategies_affected={self.num_strategies_affected})"
        )
