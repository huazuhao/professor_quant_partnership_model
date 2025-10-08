"""
External Shock Manager for External Shock Component.

Main orchestrator for crisis event generation and application.
Uses exponential distribution for crisis timing and normal distribution
for crisis severity.
"""

from typing import Dict, Optional
import numpy as np
from scipy.stats import expon
from .external_shock_parameters import ExternalShockParameters as ESP
from .crisis_event import CrisisEvent


class ExternalShockManager:
    """
    Main component for managing financial crisis events.

    Implements crisis generation using:
    - Exponential distribution for crisis arrival times
    - Normal distribution for crisis severity
    - Beta-scaled impact via Strategy Lifecycle component
    """

    def __init__(self):
        """Initialize the External Shock Manager."""
        # Initialize exponential distribution for crisis timing
        self.crisis_rv = expon(loc=0, scale=1/ESP.CRISIS_LAMBDA)

        # Sample initial countdown to first crisis
        self.crisis_countdown = self.crisis_rv.rvs(size=1)[0]

        # Track crisis history
        self.crisis_history: Dict[int, CrisisEvent] = {}

    def check_and_apply_crisis(self, quarter: int, strategy_manager) -> CrisisEvent:
        """
        Check for crisis occurrence and apply to strategies if triggered.

        This is the main coupling method called each quarter from the simulation loop.

        Args:
            quarter: Current quarter number
            strategy_manager: StrategyManager instance to apply crisis to

        Returns:
            CrisisEvent: Crisis event record (occurred=True if crisis, False otherwise)
        """
        # Decrement crisis countdown
        self.crisis_countdown -= 1

        if self.crisis_countdown <= 0:
            # CRISIS TRIGGERED
            crisis_event = self._execute_crisis(quarter, strategy_manager)

            # Reset countdown to next crisis
            self.crisis_countdown = self.crisis_rv.rvs(size=1)[0]
        else:
            # NO CRISIS THIS QUARTER
            crisis_event = CrisisEvent(
                quarter=quarter,
                occurred=False,
                base_drawdown=0.0,
                losses_by_strategy={},
                total_losses=0.0
            )

        # Store in history
        self.crisis_history[quarter] = crisis_event

        return crisis_event

    def _execute_crisis(self, quarter: int, strategy_manager) -> CrisisEvent:
        """
        Execute crisis by sampling severity and applying to strategies.

        Args:
            quarter: Current quarter number
            strategy_manager: StrategyManager instance

        Returns:
            CrisisEvent with crisis details and losses
        """
        # Sample base drawdown from normal distribution
        base_drawdown = np.random.normal(
            ESP.CRISIS_DRAWDOWN_MEAN,
            ESP.CRISIS_DRAWDOWN_STD
        )

        # Clip to reasonable bounds
        base_drawdown = np.clip(
            base_drawdown,
            ESP.CRISIS_DRAWDOWN_MIN,
            ESP.CRISIS_DRAWDOWN_MAX
        )

        # Apply crisis to all active strategies via Strategy Lifecycle
        # This calls the existing apply_crisis_all() method
        losses_by_strategy = strategy_manager.apply_crisis_all(base_drawdown)

        # Calculate total losses
        total_losses = sum(losses_by_strategy.values())

        # Create crisis event record
        crisis_event = CrisisEvent(
            quarter=quarter,
            occurred=True,
            base_drawdown=base_drawdown,
            losses_by_strategy=losses_by_strategy,
            total_losses=total_losses
        )

        return crisis_event

    def get_crisis_event(self, quarter: int) -> Optional[CrisisEvent]:
        """Get crisis event for a specific quarter."""
        return self.crisis_history.get(quarter)

    def get_crisis_summary(self, quarter: int) -> Optional[Dict]:
        """Get crisis summary for a specific quarter."""
        event = self.crisis_history.get(quarter)
        return event.get_summary() if event else None

    def get_all_crises(self) -> Dict[int, CrisisEvent]:
        """Get all crisis events that occurred."""
        return {
            q: event for q, event in self.crisis_history.items()
            if event.occurred
        }

    def get_crisis_statistics(self) -> Dict:
        """
        Get aggregate statistics across all crises.

        Returns:
            Dict with crisis statistics
        """
        crises = self.get_all_crises()

        if not crises:
            return {
                'total_crises': 0,
                'total_quarters_tracked': len(self.crisis_history),
                'crisis_frequency': 0.0,
                'total_losses': 0.0,
                'average_base_drawdown': 0.0,
                'min_base_drawdown': 0.0,
                'max_base_drawdown': 0.0,
                'average_total_loss': 0.0
            }

        base_drawdowns = [c.base_drawdown for c in crises.values()]
        total_losses_list = [c.total_losses for c in crises.values()]

        return {
            'total_crises': len(crises),
            'total_quarters_tracked': len(self.crisis_history),
            'crisis_frequency': len(crises) / len(self.crisis_history) if self.crisis_history else 0.0,
            'total_losses': sum(total_losses_list),
            'average_base_drawdown': np.mean(base_drawdowns),
            'min_base_drawdown': min(base_drawdowns),
            'max_base_drawdown': max(base_drawdowns),
            'average_total_loss': np.mean(total_losses_list)
        }

    def get_quarters_until_next_crisis(self) -> float:
        """Get estimated quarters until next crisis."""
        return max(0, self.crisis_countdown)

    def clear_crisis_history(self):
        """Clear crisis history (useful for testing)."""
        self.crisis_history.clear()

    def __repr__(self) -> str:
        """String representation of the manager."""
        crises = self.get_all_crises()
        return (
            f"ExternalShockManager("
            f"crises={len(crises)}, "
            f"quarters_tracked={len(self.crisis_history)}, "
            f"next_crisis_in={self.crisis_countdown:.1f}Q)"
        )
