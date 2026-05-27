"""
Performance Allocation Component

This component handles quarterly NAV accounting and annual performance
allocation across authors and the safety net program. It implements
cohort-level high water mark accounting, management fee collection, and profit
distribution.

Main classes:
- PerformanceAllocationManager: Main orchestrator for performance allocation
- AllocationSummary: Data structure for tracking allocation outcomes
- PerformanceAllocationParameters: Configuration parameters

Key Features:
- Cohort-level high water mark accounting (new capital does not inherit old losses)
- Annual three-way profit split: 80% fund retention, 10% author performance, 10% safety net
- Author performance allocation based on strategy ownership splits
- Safety net program ensuring $1M lifetime minimum for contributing authors
- Management fee collection (0.25% quarterly)
"""

from .performance_allocation_manager import PerformanceAllocationManager
from .allocation_summary import AllocationSummary
from .performance_allocation_parameters import PerformanceAllocationParameters

__all__ = [
    'PerformanceAllocationManager',
    'AllocationSummary',
    'PerformanceAllocationParameters'
]

# Version information
__version__ = '1.0.0'
__author__ = 'Hedgedemia Business Model Team'
