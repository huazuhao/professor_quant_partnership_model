import unittest

from components.author_collaboration.author import Author
from components.author_collaboration.author_collaboration_manager import (
    AuthorCollaborationManager,
)
from components.performance_allocation.performance_allocation_manager import (
    PerformanceAllocationManager,
)
from components.performance_allocation.performance_allocation_parameters import (
    PerformanceAllocationParameters as PAP,
)
from components.strategy_lifecycle.strategy_factory import StrategyFactory
from components.strategy_lifecycle.strategy_manager import StrategyManager


def make_author(author_id, lifetime_payments):
    author = Author(
        author_id=author_id,
        name=author_id,
        hire_quarter=0,
        remaining_research_quarters=1,
    )
    if lifetime_payments:
        author.performance_payments[-1] = lifetime_payments
    return author


def make_performance_manager(authors, initial_aum=None):
    author_manager = AuthorCollaborationManager()
    for author in authors:
        author_manager.add_author(author)

    strategy_manager = StrategyManager()
    strategy = StrategyFactory.create_strategy_with_params(
        authors=authors,
        quarter=0,
        distribution_type="t",
        distribution_loc=1.0,
        distribution_scale=0.1,
        max_capacity=10.0,
        beta=1.0,
        strategy_id="strategy_safety_net_test",
    )
    strategy_manager.add_strategy(strategy)

    return PerformanceAllocationManager(
        strategy_manager,
        author_manager,
        initial_aum=initial_aum,
    )


class PerformanceAllocationSafetyNetTest(unittest.TestCase):
    def test_safety_net_redistributes_near_cap_author_share(self):
        authors = [
            make_author("author_a", 0.99),
            make_author("author_b", 0.50),
            make_author("author_c", 0.20),
        ]
        manager = make_performance_manager(authors)

        payments = manager._distribute_safety_net_payments(0.60, quarter=1)

        self.assertAlmostEqual(payments["author_a"], 0.01)
        self.assertAlmostEqual(payments["author_b"], 0.295)
        self.assertAlmostEqual(payments["author_c"], 0.295)
        for author in authors:
            self.assertLessEqual(
                author.get_lifetime_payments(),
                PAP.AUTHOR_GUARANTEED_RETURN,
            )

    def test_safety_net_leaves_unused_pool_when_all_authors_reach_cap(self):
        authors = [
            make_author("author_a", 0.99),
            make_author("author_b", 0.98),
        ]
        manager = make_performance_manager(authors)

        payments = manager._distribute_safety_net_payments(0.60, quarter=1)

        self.assertAlmostEqual(payments["author_a"], 0.01)
        self.assertAlmostEqual(payments["author_b"], 0.02)
        self.assertAlmostEqual(sum(payments.values()), 0.03)
        for author in authors:
            self.assertAlmostEqual(
                author.get_lifetime_payments(),
                PAP.AUTHOR_GUARANTEED_RETURN,
            )


class PerformanceAllocationAccountingTest(unittest.TestCase):
    def test_net_drawdown_must_recover_fees_before_performance_allocation(self):
        authors = [make_author("author_a", 0.0)]
        manager = make_performance_manager(authors, initial_aum=100.0)

        results = [
            manager.process_quarterly_allocation(
                {"strategy_safety_net_test": -10.0},
                quarter=1,
            ),
            manager.process_quarterly_allocation(
                {"strategy_safety_net_test": 5.0},
                quarter=2,
            ),
            manager.process_quarterly_allocation(
                {"strategy_safety_net_test": 5.0},
                quarter=3,
            ),
            manager.process_quarterly_allocation(
                {"strategy_safety_net_test": 0.0},
                quarter=4,
            ),
        ]

        self.assertTrue(all(not result.high_water_mark_met for result in results))
        self.assertGreater(manager.get_cumulative_loss_account(), 0.0)
        self.assertEqual(authors[0].get_lifetime_payments(), 0.0)

    def test_performance_allocation_crystallizes_annually(self):
        authors = [make_author("author_a", 0.0)]
        manager = make_performance_manager(authors, initial_aum=100.0)

        q1 = manager.process_quarterly_allocation(
            {"strategy_safety_net_test": 10.0},
            quarter=1,
        )
        manager.process_quarterly_allocation(
            {"strategy_safety_net_test": 0.0},
            quarter=2,
        )
        manager.process_quarterly_allocation(
            {"strategy_safety_net_test": 0.0},
            quarter=3,
        )
        q4 = manager.process_quarterly_allocation(
            {"strategy_safety_net_test": 0.0},
            quarter=4,
        )

        self.assertFalse(q1.high_water_mark_met)
        self.assertEqual(q1.get_total_author_payments(), 0.0)
        self.assertTrue(q4.high_water_mark_met)
        self.assertGreater(q4.distributable_profits, 0.0)
        self.assertGreater(authors[0].performance_payments[4], 0.0)

    def test_new_flow_cohort_does_not_inherit_existing_drawdown(self):
        authors = [make_author("author_a", 0.0)]
        manager = make_performance_manager(authors, initial_aum=100.0)

        manager.process_quarterly_allocation(
            {"strategy_safety_net_test": -20.0},
            quarter=1,
        )
        manager.update_aum(100.0, quarter=1)
        manager.process_quarterly_allocation(
            {"strategy_safety_net_test": 10.0},
            quarter=2,
        )
        manager.process_quarterly_allocation(
            {"strategy_safety_net_test": 0.0},
            quarter=3,
        )
        q4 = manager.process_quarterly_allocation(
            {"strategy_safety_net_test": 0.0},
            quarter=4,
        )

        cohort_summary = {
            cohort["cohort_id"]: cohort
            for cohort in manager.get_capital_cohort_summary()
        }

        self.assertTrue(q4.high_water_mark_met)
        self.assertGreater(
            cohort_summary["initial_capital"]["cumulative_loss_account"],
            0.0,
        )
        flow_cohorts = [
            cohort for cohort_id, cohort in cohort_summary.items()
            if cohort_id != "initial_capital"
        ]
        self.assertEqual(len(flow_cohorts), 1)
        self.assertEqual(flow_cohorts[0]["cumulative_loss_account"], 0.0)

    def test_withdrawal_crystallizes_redeemed_profit_above_hwm(self):
        authors = [make_author("author_a", 0.0)]
        manager = make_performance_manager(authors, initial_aum=100.0)

        manager.process_quarterly_allocation(
            {"strategy_safety_net_test": 10.0},
            quarter=1,
        )
        aum_before_withdrawal = manager.get_fund_aum()
        annual_profit_before = manager.get_capital_cohort_summary()[0][
            "annual_net_profit"
        ]

        manager.update_aum(-(aum_before_withdrawal * 0.5), quarter=1)

        history = manager.get_withdrawal_crystallization_summary(1)
        remaining_cohort = manager.get_capital_cohort_summary()[0]
        expected_distributable = annual_profit_before * 0.5
        expected_author_payments = (
            expected_distributable * PAP.PERFORMANCE_ALLOCATION
        )

        self.assertEqual(len(history), 1)
        self.assertAlmostEqual(
            history[0]["distributable_profits"],
            expected_distributable,
        )
        self.assertAlmostEqual(
            history[0]["author_payments"],
            expected_author_payments,
        )
        self.assertAlmostEqual(
            authors[0].get_lifetime_payments(),
            expected_author_payments,
        )
        self.assertAlmostEqual(
            manager.get_fund_aum(),
            aum_before_withdrawal * 0.5,
        )
        self.assertAlmostEqual(
            remaining_cohort["annual_net_profit"],
            annual_profit_before * 0.5,
        )

    def test_withdrawal_below_hwm_does_not_crystallize_author_payment(self):
        authors = [make_author("author_a", 0.0)]
        manager = make_performance_manager(authors, initial_aum=100.0)

        manager.process_quarterly_allocation(
            {"strategy_safety_net_test": -10.0},
            quarter=1,
        )
        manager.process_quarterly_allocation(
            {"strategy_safety_net_test": 0.0},
            quarter=2,
        )
        manager.process_quarterly_allocation(
            {"strategy_safety_net_test": 0.0},
            quarter=3,
        )
        manager.process_quarterly_allocation(
            {"strategy_safety_net_test": 0.0},
            quarter=4,
        )
        self.assertGreater(manager.get_cumulative_loss_account(), 0.0)

        manager.process_quarterly_allocation(
            {"strategy_safety_net_test": 5.0},
            quarter=5,
        )
        manager.update_aum(-(manager.get_fund_aum() * 0.5), quarter=5)

        self.assertEqual(
            manager.get_withdrawal_crystallization_summary(5),
            [],
        )
        self.assertEqual(authors[0].get_lifetime_payments(), 0.0)


if __name__ == "__main__":
    unittest.main()
