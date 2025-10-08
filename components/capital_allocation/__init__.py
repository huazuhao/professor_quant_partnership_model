"""
Capital Allocation Component

This component handles quarterly capital deployment across active strategies.
It implements the greedy allocation algorithm from iteration_one that sorts
strategies by expected return and allocates capital to maximize returns.

Main classes:
- CapitalAllocationManager: Main orchestrator for capital allocation
- AllocationResult: Data structure for tracking allocation outcomes
"""

from .capital_allocation_manager import CapitalAllocationManager
from .allocation_result import AllocationResult

__all__ = [
    'CapitalAllocationManager',
    'AllocationResult'
]

# Version information
__version__ = '1.0.0'
__author__ = 'Hedgedemia Business Model Team'