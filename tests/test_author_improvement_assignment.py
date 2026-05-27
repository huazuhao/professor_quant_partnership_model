import unittest
from unittest.mock import patch

from components.author_collaboration.author_collaboration_manager import (
    AuthorCollaborationManager,
)
from components.author_collaboration.author import Author
from components.author_collaboration.author_collaboration_parameters import (
    AuthorCollaborationParameters as ACP,
)
from components.strategy_lifecycle.strategy_factory import StrategyFactory
from components.strategy_lifecycle.strategy_manager import StrategyManager
from components.strategy_lifecycle.strategy_parameters import StrategyParameters as SP


def make_strategy(strategy_id, expected_return, capacity):
    return StrategyFactory.create_strategy_with_params(
        authors=["author_a"],
        quarter=0,
        distribution_type="t",
        distribution_loc=expected_return,
        distribution_scale=0.1,
        max_capacity=capacity,
        beta=1.0,
        strategy_id=strategy_id,
    )


def make_author(author_id, remaining_quarters, improvement_probability=1.0):
    return Author(
        author_id=author_id,
        name=author_id,
        hire_quarter=0,
        remaining_research_quarters=remaining_quarters,
        invention_probability=1.0,
        improvement_probability=improvement_probability,
    )


class AuthorImprovementAssignmentTest(unittest.TestCase):
    def test_assignment_limits_strategy_to_two_groups_per_quarter(self):
        manager = AuthorCollaborationManager()
        strategy_manager = StrategyManager()
        strategy_manager.add_strategy(make_strategy("strategy_a", 3.0, 30.0))

        groups = [["a"], ["b"], ["c"], ["d"], ["e"]]

        with patch.object(ACP, "MAX_IMPROVEMENT_GROUPS_PER_STRATEGY_PER_QUARTER", 2):
            assigned = manager._assign_strategies_to_groups(groups, strategy_manager)

        assigned_to_strategy = [
            group for group in assigned
            if group["target_strategy"] is not None
        ]
        unassigned = [
            group for group in assigned
            if group["target_strategy"] is None
        ]

        self.assertEqual(len(assigned_to_strategy), 2)
        self.assertEqual(len(unassigned), 3)

    def test_last_quarter_authors_get_first_improvement_slot_priority(self):
        manager = AuthorCollaborationManager()
        strategy_manager = StrategyManager()
        strategy_manager.add_strategy(make_strategy("strategy_a", 3.0, 30.0))

        last_quarter = make_author("last_quarter", 1)
        flexible = make_author("flexible", 2)

        with patch(
            "components.author_collaboration.author_collaboration_manager.random.randint",
            return_value=1,
        ):
            groups, last_count, flexible_count = (
                manager._form_prioritized_improvement_groups([
                    flexible,
                    last_quarter,
                ])
            )

        self.assertEqual(last_count, 1)
        self.assertEqual(flexible_count, 1)
        self.assertEqual(groups[0], [last_quarter])
        self.assertEqual(groups[1], [flexible])

        with patch.object(ACP, "MAX_IMPROVEMENT_GROUPS_PER_STRATEGY_PER_QUARTER", 1):
            assigned = manager._assign_strategies_to_groups(
                groups,
                strategy_manager,
            )

        self.assertEqual(assigned[0]["authors"], [last_quarter])
        self.assertIsNotNone(assigned[0]["target_strategy"])
        self.assertEqual(assigned[1]["authors"], [flexible])
        self.assertIsNone(assigned[1]["target_strategy"])

    def test_capacity_weight_favors_high_return_low_capacity_strategy(self):
        manager = AuthorCollaborationManager()

        attractive = make_strategy("attractive", 4.0, 20.0)
        lower_return = make_strategy("lower_return", 2.0, 20.0)
        near_capacity_cap = make_strategy(
            "near_capacity_cap",
            4.0,
            SP.STRATEGY_MAX_CAPACITY_ABSOLUTE * 0.95,
        )

        self.assertGreater(
            manager._capacity_improvement_weight(attractive),
            manager._capacity_improvement_weight(lower_return),
        )
        self.assertGreater(
            manager._capacity_improvement_weight(attractive),
            manager._capacity_improvement_weight(near_capacity_cap),
        )

    def test_return_weight_favors_positive_strategy_with_room_below_return_cap(self):
        manager = AuthorCollaborationManager()

        attractive = make_strategy("attractive", 2.5, 50.0)
        low_return = make_strategy("low_return", 0.5, 50.0)
        near_return_cap = make_strategy(
            "near_return_cap",
            SP.STRATEGY_MAX_EXPECTED_RETURN * 0.98,
            50.0,
        )

        self.assertGreater(
            manager._return_improvement_weight(attractive),
            manager._return_improvement_weight(low_return),
        )
        self.assertGreater(
            manager._return_improvement_weight(attractive),
            manager._return_improvement_weight(near_return_cap),
        )

    def test_no_target_improvement_authors_redirect_to_invention(self):
        manager = AuthorCollaborationManager()
        inventable_a = make_author("inventable_a", 2)
        inventable_b = make_author("inventable_b", 3)

        executable, redirected, redirected_group_count, overflow_group_count = (
            manager._redirect_no_target_improvements_to_invention([
                {
                    "authors": [inventable_a, inventable_b],
                    "target_strategy": None,
                    "improvement_type": None,
                }
            ])
        )

        self.assertEqual(executable, [])
        self.assertEqual(redirected, [inventable_a, inventable_b])
        self.assertEqual(redirected_group_count, 1)
        self.assertEqual(overflow_group_count, 0)

    def test_no_target_improvement_keeps_authors_who_cannot_invent(self):
        manager = AuthorCollaborationManager()
        inventable = make_author("inventable", 2)
        too_late = make_author("too_late", 1)

        executable, redirected, redirected_group_count, overflow_group_count = (
            manager._redirect_no_target_improvements_to_invention([
                {
                    "authors": [inventable, too_late],
                    "target_strategy": None,
                    "improvement_type": None,
                }
            ])
        )

        self.assertEqual(redirected, [inventable])
        self.assertEqual(redirected_group_count, 1)
        self.assertEqual(overflow_group_count, 0)
        self.assertEqual(len(executable), 1)
        self.assertEqual(executable[0]["authors"], [too_late])
        self.assertIsNone(executable[0]["target_strategy"])

    def test_no_target_last_quarter_author_gets_overflow_assignment(self):
        manager = AuthorCollaborationManager()
        strategy_manager = StrategyManager()
        strategy_manager.add_strategy(make_strategy("strategy_a", 3.0, 30.0))
        too_late = make_author("too_late", 1)

        executable, redirected, redirected_group_count, overflow_group_count = (
            manager._redirect_no_target_improvements_to_invention(
                [
                    {
                        "authors": [too_late],
                        "target_strategy": None,
                        "improvement_type": None,
                    }
                ],
                strategy_manager,
            )
        )

        self.assertEqual(redirected, [])
        self.assertEqual(redirected_group_count, 0)
        self.assertEqual(overflow_group_count, 1)
        self.assertEqual(len(executable), 1)
        self.assertEqual(executable[0]["authors"], [too_late])
        self.assertIsNotNone(executable[0]["target_strategy"])
        self.assertIsNotNone(executable[0]["improvement_type"])

    def test_failed_improvement_still_records_assigned_target(self):
        manager = AuthorCollaborationManager()
        strategy_manager = StrategyManager()
        strategy = make_strategy("strategy_a", 3.0, 30.0)
        strategy_manager.add_strategy(strategy)
        author = make_author(
            "author_a",
            remaining_quarters=1,
            improvement_probability=0.0,
        )

        activities, capacity_count, return_count = manager._execute_improvement_groups(
            [
                {
                    "authors": [author],
                    "target_strategy": strategy,
                    "improvement_type": "return",
                }
            ],
            quarter=1,
            strategy_manager=strategy_manager,
        )

        self.assertEqual(capacity_count, 0)
        self.assertEqual(return_count, 0)
        self.assertEqual(len(activities), 1)
        self.assertFalse(activities[0].success)
        self.assertEqual(activities[0].target_strategy_id, "strategy_a")
        self.assertEqual(activities[0].improvement_type, "return")


if __name__ == "__main__":
    unittest.main()
