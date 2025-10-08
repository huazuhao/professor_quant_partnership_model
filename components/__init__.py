"""
Hedgedemia Business Model Components
Version 2025 September
"""

# Import all component interfaces
from .author_collaboration import (
    AuthorFactory,
    AuthorCollaborationManager,
    Author,
    GroupActivity,
    AuthorCollaborationParameters
)

from .strategy_lifecycle import (
    StrategyFactory,
    StrategyManager,
    Strategy,
    StrategyParameters
)

from .capital_allocation import (
    CapitalAllocationManager,
    AllocationResult
)

from .performance_allocation import (
    PerformanceAllocationManager,
    AllocationSummary,
    PerformanceAllocationParameters
)

from .investor_flow import (
    InvestorFlowManager,
    FlowEvent,
    InvestorFlowParameters
)

from .external_shock import (
    ExternalShockManager,
    CrisisEvent,
    ExternalShockParameters
)

__all__ = [
    # Author Collaboration
    'AuthorFactory',
    'AuthorCollaborationManager',
    'Author',
    'GroupActivity',
    'AuthorCollaborationParameters',

    # Strategy Lifecycle
    'StrategyFactory',
    'StrategyManager',
    'Strategy',
    'StrategyParameters',

    # Capital Allocation
    'CapitalAllocationManager',
    'AllocationResult',

    # Performance Allocation
    'PerformanceAllocationManager',
    'AllocationSummary',
    'PerformanceAllocationParameters',

    # Investor Flow
    'InvestorFlowManager',
    'FlowEvent',
    'InvestorFlowParameters',

    # External Shock
    'ExternalShockManager',
    'CrisisEvent',
    'ExternalShockParameters',
]