"""
External Shock Component

This component handles financial crisis events that impact strategy performance.
It models crisis timing using exponential distribution and severity using
normal distribution, with beta-scaled losses per strategy.

Main classes:
- ExternalShockManager: Main orchestrator for crisis generation and application
- CrisisEvent: Data structure for tracking crisis outcomes
- ExternalShockParameters: Configuration parameters

Key Features:
- Exponential crisis arrival (average 1 crisis per 40 quarters)
- Normal distribution for crisis severity (mean 20%, std 5%)
- Beta-scaled strategy losses (defensive strategies lose less)
- Complete crisis event tracking and statistics
"""

from .external_shock_manager import ExternalShockManager
from .crisis_event import CrisisEvent
from .external_shock_parameters import ExternalShockParameters

__all__ = [
    'ExternalShockManager',
    'CrisisEvent',
    'ExternalShockParameters'
]

# Version information
__version__ = '1.0.0'
__author__ = 'Hedgedemia Business Model Team'
