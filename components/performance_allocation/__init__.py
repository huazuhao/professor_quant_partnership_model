"""
Performance Allocation Component

This component handles quarterly performance allocation across authors and the
safety net program. It implements high water mark accounting, management fee
collection, and profit distribution from iteration_one.

Main classes:
- PerformanceAllocationManager: Main orchestrator for performance allocation
- AllocationSummary: Data structure for tracking allocation outcomes
- PerformanceAllocationParameters: Configuration parameters

Key Features:
- High water mark accounting (no fees during loss recovery)
- Three-way profit split: 80% fund retention, 16% author performance, 4% safety net
- Author performance allocation based on strategy ownership splits
- Safety net program ensuring $4M lifetime minimum for contributing authors
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