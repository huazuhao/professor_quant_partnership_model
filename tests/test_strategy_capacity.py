import random
import unittest
from unittest.mock import patch

from components.strategy_lifecycle.strategy_factory import StrategyFactory
from components.strategy_lifecycle.strategy_parameters import StrategyParameters as SP


class StrategyCapacityTest(unittest.TestCase):
    def test_new_strategy_birth_capacity_uses_configured_range(self):
        random.seed(123)

        strategies = [
            StrategyFactory.create_new_strategy(["author_a"], quarter=i)
            for i in range(100)
        ]

        for strategy in strategies:
            self.assertGreaterEqual(
                strategy.max_capacity,
                SP.STRATEGY_INITIAL_CAPACITY_MIN,
            )
            self.assertLessEqual(
                strategy.max_capacity,
                SP.STRATEGY_INITIAL_CAPACITY_MAX,
            )

    def test_capacity_improvement_adds_configured_increment(self):
        strategy = StrategyFactory.create_strategy_with_params(
            authors=["author_a"],
            quarter=0,
            distribution_type="t",
            distribution_loc=2.0,
            distribution_scale=0.1,
            max_capacity=40.0,
            beta=1.0,
        )

        with patch("components.strategy_lifecycle.strategy.random.uniform", return_value=15.0):
            success = strategy.improve_capacity(quarter=1)

        self.assertTrue(success)
        self.assertEqual(strategy.max_capacity, 55.0)

    def test_capacity_improvement_respects_absolute_cap(self):
        strategy = StrategyFactory.create_strategy_with_params(
            authors=["author_a"],
            quarter=0,
            distribution_type="t",
            distribution_loc=2.0,
            distribution_scale=0.1,
            max_capacity=95.0,
            beta=1.0,
        )

        with patch("components.strategy_lifecycle.strategy.random.uniform", return_value=50.0):
            success = strategy.improve_capacity(quarter=1)

        self.assertTrue(success)
        self.assertEqual(strategy.max_capacity, SP.STRATEGY_MAX_CAPACITY_ABSOLUTE)


if __name__ == "__main__":
    unittest.main()
