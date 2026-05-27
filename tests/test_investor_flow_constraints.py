import unittest
from unittest.mock import patch

from components.investor_flow import InvestorFlowManager


class InvestorFlowAcceptanceConstraintTest(unittest.TestCase):
    def test_positive_inflow_is_capped_by_strategy_capacity(self):
        manager = InvestorFlowManager()

        with patch.object(manager, "_sample_from_gaussian", return_value=50.0):
            event = manager.process_quarterly_flows(
                current_aum=100.0,
                quarterly_return=0.10,
                quarter=1,
                strategy_capacity=120.0,
                previous_quarter_aum=100.0,
            )

        self.assertEqual(event.net_flow_after_magnitude_cap, 50.0)
        self.assertEqual(event.net_flow_final, 20.0)
        self.assertEqual(event.aum_after_flow, 120.0)
        self.assertEqual(event.rejected_inflow_due_to_aum_constraints, 30.0)
        self.assertTrue(event.aum_acceptance_constraint_applied)

    def test_positive_inflow_is_capped_by_quarterly_growth_limit(self):
        manager = InvestorFlowManager()

        with patch.object(manager, "_sample_from_gaussian", return_value=50.0):
            event = manager.process_quarterly_flows(
                current_aum=110.0,
                quarterly_return=0.10,
                quarter=1,
                strategy_capacity=200.0,
                previous_quarter_aum=100.0,
            )

        self.assertEqual(event.net_flow_after_magnitude_cap, 50.0)
        self.assertEqual(event.net_flow_final, 15.0)
        self.assertEqual(event.aum_after_flow, 125.0)
        self.assertEqual(event.rejected_inflow_due_to_aum_constraints, 35.0)
        self.assertTrue(event.aum_acceptance_constraint_applied)

    def test_positive_inflow_is_zero_when_aum_already_exceeds_capacity(self):
        manager = InvestorFlowManager()

        with patch.object(manager, "_sample_from_gaussian", return_value=50.0):
            event = manager.process_quarterly_flows(
                current_aum=130.0,
                quarterly_return=0.10,
                quarter=1,
                strategy_capacity=120.0,
                previous_quarter_aum=130.0,
            )

        self.assertEqual(event.net_flow_final, 0.0)
        self.assertEqual(event.aum_after_flow, 130.0)
        self.assertEqual(event.rejected_inflow_due_to_aum_constraints, 50.0)
        self.assertTrue(event.aum_acceptance_constraint_applied)

    def test_negative_outflow_is_not_limited_by_aum_acceptance_constraints(self):
        manager = InvestorFlowManager()

        with patch.object(manager, "_sample_from_gaussian", return_value=-20.0):
            event = manager.process_quarterly_flows(
                current_aum=100.0,
                quarterly_return=-0.10,
                quarter=1,
                strategy_capacity=50.0,
                previous_quarter_aum=100.0,
            )

        self.assertEqual(event.net_flow_after_magnitude_cap, -20.0)
        self.assertEqual(event.net_flow_final, -20.0)
        self.assertEqual(event.aum_after_flow, 80.0)
        self.assertEqual(event.rejected_inflow_due_to_aum_constraints, 0.0)
        self.assertFalse(event.aum_acceptance_constraint_applied)


if __name__ == "__main__":
    unittest.main()
