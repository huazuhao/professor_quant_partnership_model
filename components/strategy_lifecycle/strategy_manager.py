"""
Strategy Manager - Manages the collection of all strategies
Handles portfolio-level operations and strategy lifecycle coordination
"""

from typing import List, Dict, Tuple, Optional
from .strategy import Strategy
from .strategy_parameters import StrategyParameters as SP


class StrategyManager:
    """Manages all strategies in the fund"""

    def __init__(self):
        """Initialize the strategy manager"""
        self.strategies: List[Strategy] = []
        self.strategies_by_id: Dict[str, Strategy] = {}

    def add_strategy(self, strategy: Strategy):
        """Add a new strategy to the portfolio"""
        self.strategies.append(strategy)
        self.strategies_by_id[strategy.strategy_id] = strategy

    def get_strategy_by_id(self, strategy_id: str) -> Optional[Strategy]:
        """Get a strategy by its ID"""
        return self.strategies_by_id.get(strategy_id)

    def get_active_strategies(self) -> List[Strategy]:
        """Get all active strategies with positive expected returns"""
        return [
            s for s in self.strategies
            if s.is_active and s.get_expected_return() > 0
        ]

    def get_all_strategies(self) -> List[Strategy]:
        """Get all strategies (active and inactive)"""
        return self.strategies

    def get_improvable_strategies(self) -> List[Strategy]:
        """
        Get all strategies that have room to improve (either returns or capacity).

        Returns:
            List[Strategy]: Strategies that can be improved in at least one dimension
        """
        return [
            s for s in self.strategies
            if s.is_active and (s.can_improve_returns() or s.can_improve_capacity())
        ]

    def apply_quarterly_decay_all(self):
        """Apply natural decay to all active strategies"""
        for strategy in self.strategies:
            if strategy.is_active:
                strategy.apply_natural_decay()
                strategy.advance_quarter()

    def process_improvements(
        self,
        improvements_list: List[Tuple[str, str, int]]
    ) -> Dict[str, bool]:
        """
        Process a list of strategy improvements

        Args:
            improvements_list: List of tuples (strategy_id, improvement_type, quarter)
                improvement_type: 'return' or 'capacity'

        Returns:
            Dict mapping strategy_id to success status
        """
        results = {}

        for strategy_id, improvement_type, quarter in improvements_list:
            strategy = self.get_strategy_by_id(strategy_id)
            if strategy is None:
                results[strategy_id] = False
                continue

            if improvement_type == 'return':
                success = strategy.improve_returns(quarter)
            elif improvement_type == 'capacity':
                success = strategy.improve_capacity(quarter)
            else:
                success = False

            results[strategy_id] = success

        return results

    def generate_returns(
        self,
        capital_allocations: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Generate returns for all strategies based on capital allocations

        Args:
            capital_allocations: Dict mapping strategy_id to allocated capital

        Returns:
            Dict mapping strategy_id to dollar returns
        """
        returns = {}

        for strategy_id, allocated_capital in capital_allocations.items():
            strategy = self.get_strategy_by_id(strategy_id)
            if strategy:
                returns[strategy_id] = strategy.generate_quarterly_return(
                    allocated_capital
                )
            else:
                returns[strategy_id] = 0.0

        return returns

    def apply_crisis_all(self, base_drawdown: float) -> Dict[str, float]:
        """
        Apply crisis drawdown to all active strategies

        Args:
            base_drawdown: Base crisis drawdown percentage

        Returns:
            Dict mapping strategy_id to dollar losses
        """
        losses = {}

        for strategy in self.strategies:
            if strategy.is_active and strategy.active_capacity > 0:
                loss = strategy.apply_crisis_drawdown(base_drawdown)
                losses[strategy.strategy_id] = loss

        return losses

    def get_portfolio_metrics(self) -> Dict:
        """
        Calculate portfolio-level metrics

        Returns:
            Dict with portfolio statistics
        """
        active_strategies = self.get_active_strategies()

        if not active_strategies:
            return {
                'num_active_strategies': 0,
                'total_capacity': 0,
                'total_active_capacity': 0,
                'avg_expected_return': 0,
                'avg_beta': 0,
                'capacity_utilization': 0
            }

        total_capacity = sum(s.max_capacity for s in active_strategies)
        total_active_capacity = sum(s.active_capacity for s in active_strategies)

        returns = [s.get_expected_return() for s in active_strategies]
        betas = [s.beta for s in active_strategies]
        avg_return = sum(returns) / len(returns) if returns else 0
        avg_beta = sum(betas) / len(betas) if betas else 0

        return {
            'num_active_strategies': len(active_strategies),
            'total_capacity': total_capacity,
            'total_active_capacity': total_active_capacity,
            'avg_expected_return': avg_return,
            'avg_beta': avg_beta,
            'capacity_utilization': (
                total_active_capacity / total_capacity if total_capacity > 0 else 0
            )
        }

    def __repr__(self):
        metrics = self.get_portfolio_metrics()
        return (
            f"StrategyManager("
            f"total_strategies={len(self.strategies)}, "
            f"active={metrics['num_active_strategies']}, "
            f"avg_return={metrics['avg_expected_return']:.2f}%, "
            f"avg_beta={metrics['avg_beta']:.2f})"
        )