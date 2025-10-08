"""
Investor Flow Component

This component handles quarterly capital inflows and outflows based on fund
performance. It implements a continuous linear Gaussian model with regime-dependent
sign constraints.

Main classes:
- InvestorFlowManager: Main orchestrator for investor capital flows
- FlowEvent: Data structure for tracking flow outcomes
- InvestorFlowParameters: Configuration parameters

Key Features:
- Linear performance-to-flow mapping (good returns → inflows, poor → outflows)
- Gaussian distribution for realistic flow variability
- Regime-dependent sign constraints (no outflows during good performance)
- Two-layer hard caps (sign constraint + magnitude caps)
- Trailing 4-quarter performance tracking
"""

from .investor_flow_manager import InvestorFlowManager
from .flow_event import FlowEvent
from .investor_flow_parameters import InvestorFlowParameters

__all__ = [
    'InvestorFlowManager',
    'FlowEvent',
    'InvestorFlowParameters'
]

# Version information
__version__ = '1.0.0'
__author__ = 'Hedgedemia Business Model Team'
