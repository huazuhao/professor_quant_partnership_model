# Performance Allocation Component

## Overview

The Performance Allocation Component implements the fund's quarterly NAV accounting and annual performance allocation system. It tracks investor capital cohorts, applies high-water-mark accounting, and distributes annual performance profits among the fund, strategy authors, and the safety net program.

The component treats strategy returns as net trading P&L, charges the quarterly management fee, tracks cohort-level drawdown recovery, and only crystallizes performance allocation at annual year-end quarters.

---

## Files

- `performance_allocation_manager.py`: Main orchestrator for quarterly NAV accounting, cohort-level high water marks, and annual performance allocation.
- `allocation_summary.py`: Data structures for tracking allocation outcomes, efficiency metrics, and detailed reporting.
- `performance_allocation_parameters.py`: Configuration parameters for the quarterly economic simulation.
- `__init__.py`: Component interface and version information.

---

## Business Logic Overview

### Performance Allocation Flow

The component operates in quarterly cycles following this sequence:

1. **Management Fee Collection**: 0.25% quarterly fee collected from fund AUM
2. **Net P&L Allocation**: Allocate net strategy P&L across investor cohorts pro rata
3. **Cohort HWM Tracking**: Track each cohort's annual net profit and cumulative loss account
4. **Annual Crystallization**: At every fourth quarter, calculate profits above each cohort's high water mark
5. **Performance Distribution**: Allocate 10% of annual above-HWM profits proportionally to strategy authors
6. **Safety Net Assessment**: Identify enrolled authors below $1M guaranteed minimum
7. **Safety Net Distribution**: Distribute up to 10% of annual above-HWM profits equally among eligible authors, capped at each author's remaining guarantee gap
8. **Fund Retention**: Keep all non-distributed annual profit in investor capital

### Three-Tier Profit Distribution

```
Annual Net Profit Above Cohort HWM
  ↓
80% → Investor/Fund Retention
20% → Author Allocation Pool
  ├─ 50% (10% of total) → Performance payments to strategy authors
  └─ 50% (10% of total) → Safety Net Pool
```

### Safety Net Program

**Enrollment**: Authors automatically enrolled when they contribute to any strategy (invention or improvement).

**Eligibility**: At annual performance crystallization, enrolled authors with lifetime payments < $1M receive an equal share of the safety net pool.

**Distribution**: Safety net funds are distributed equally among all eligible authors, capped at each author's remaining gap to the $1M lifetime guarantee. Any amount that cannot be paid because all eligible authors reached the cap remains in the fund.

---

## Performance Allocation Manager (`performance_allocation_manager.py`)

Main orchestrator class implementing the complete allocation workflow.

### Key Methods

- `process_quarterly_allocation(strategy_returns, quarter)`: Main allocation workflow entry point
- `get_fund_aum()`: Current fund AUM after all transactions
- `get_cumulative_loss_account()`: Current high water mark loss tracking
- `get_allocation_summary(quarter)`: Detailed allocation report for specific quarter
- `get_allocation_efficiency_stats()`: Historical efficiency statistics across quarters

### Algorithm Implementation

```python
def process_quarterly_allocation(strategy_returns, quarter):
    collect_management_fee_from_each_capital_cohort()
    allocate_net_strategy_pnl_to_each_capital_cohort(strategy_returns)
    track_strategy_returns_for_year_end_author_attribution(strategy_returns)

    if quarter % 4 != 0:
        return  # NAV updated, but no performance allocation crystallized

    distributable_profits = calculate_cohort_profits_above_hwm()
    if distributable_profits <= 0:
        reset_annual_profit_trackers()
        return

    performance_pool = distributable_profits * 0.10
    safety_net_pool = distributable_profits * 0.10
    distribute_performance_pool_by_annual_strategy_attribution()
    distribute_capped_safety_net_pool()
    deduct_actual_author_payments_from_profitable_cohorts()
    reset_annual_profit_trackers()
```

---

## Allocation Summary (`allocation_summary.py`)

Comprehensive data structure tracking quarterly accounting and annual allocation outcomes.

### Key Fields

- `quarter`, `total_strategy_returns`, `fund_aum_start`, `fund_aum_end`: Basic allocation metrics
- `management_fee_charged`: Quarterly management fee collected
- `high_water_mark_met`: Boolean indicating if annual above-HWM profits were distributed
- `fund_retention`, `author_performance_total`, `safety_net_total`: Three-way profit split
- `allocation_by_author`, `safety_net_by_author`: Detailed payment tracking

### Computed Properties

- `allocation_efficiency`: Profit distribution ratio (distributable/total returns)
- `total_author_payments`: Combined performance and safety net payments
- `average_performance_allocation`: Mean payment per author receiving performance allocation

### Methods

- `get_summary()`: Complete allocation report including all metrics and breakdowns
- `get_top_performance_allocations(n)`: Top N performance allocations by amount
- `get_authors_by_payment_type()`: Categorize authors by payment type received

---

## Integration Points

### With Capital Allocation Component

**Input Interface**:
```python
# Capital Allocation provides current allocations
current_allocations = capital_manager.get_current_allocations()
strategy_returns = strategy_manager.generate_returns(current_allocations)

# Performance Allocation processes returns
allocation_summary = performance_manager.process_quarterly_allocation(
    strategy_returns=strategy_returns,
    quarter=current_quarter
)
```

### With Strategy Lifecycle Component

**Required Integration Points**:
- `Strategy.ownership_splits`: Dictionary mapping author_id to ownership percentage
- `StrategyManager.get_strategy_by_id()`: Strategy lookup for ownership attribution
- `StrategyManager.get_all_strategies()`: All strategies for safety net author identification

**Usage Pattern**:
```python
for strategy_id, returns in strategy_returns.items():
    strategy = strategy_manager.get_strategy_by_id(strategy_id)
    for author_id, ownership_pct in strategy.ownership_splits.items():
        # Distribute proportional performance allocation
```

### With Author Collaboration Component

**Required Author Class Extensions**:
```python
@dataclass
class Author:
    # Safety net enrollment tracking
    safety_net_enrolled: bool = False
    safety_net_enrollment_quarter: Optional[int] = None

    # Payment history tracking
    performance_payments: Dict[int, float] = field(default_factory=dict)
    safety_net_payments: Dict[int, float] = field(default_factory=dict)

    def enroll_in_safety_net(self, quarter: int):
        """Enroll in safety net program when contributing to any strategy"""

    def record_performance_payment(self, amount: float, quarter: int):
        """Record performance allocation payment"""

    def record_safety_net_payment(self, amount: float, quarter: int):
        """Record safety net payment"""

    def get_lifetime_payments(self) -> float:
        """Get total lifetime payments for safety net eligibility"""
```

---

## Parameters Configuration

All parameters stored in `performance_allocation_parameters.py`:

```python
class PerformanceAllocationParameters:
    # Fund initialization
    FUND_INITIAL_AUM = 20.0  # $20M initial fund size

    # Management fees
    MANAGEMENT_FEE_RATE = 0.25  # 0.25% of AUM per quarter

    # Performance allocation
    PERFORMANCE_ALLOCATION = 0.2  # 20% of profits to authors
    AUTHOR_SAFETY_NET_RATIO = 0.5  # 50% of author allocation to safety net
    AUTHOR_GUARANTEED_RETURN = 1.0  # $1M lifetime minimum
    PERFORMANCE_CRYSTALLIZATION_QUARTERS = 4  # Annual crystallization
```

**Derived Constants**:
- Base Fund Retention Rate: 80% of profits
- Author Performance Rate: 10% of profits (20% × 50%)
- Safety Net Rate: up to 10% of profits (20% × 50%), subject to author guarantee caps

---

## Testing

### Unit Tests (`test_performance_allocation.py`)

**Core Algorithm Testing**:
- **High water mark calculation**: Loss recovery scenarios and profit distribution
- **Performance attribution**: Correct author-strategy linking via ownership splits
- **Safety net eligibility**: Guaranteed minimum cap and equal redistribution
- **Capital cohorts**: New investor flows receive separate high-water-mark treatment
- **Withdrawal crystallization**: Redeemed capital pays performance allocation on above-HWM profits before leaving
- **Three-way profit split**: Exact percentage allocations and conservation

**Edge Cases**:
- **Zero profits**: No performance allocation and no safety-net payment
- **Below high water mark**: No distributions during loss recovery
- **Non-year-end quarters**: NAV updates but performance allocation does not crystallize
- **Multiple authors per strategy**: Proportional ownership split validation
- **Management fee collection**: Accurate quarterly fee calculation

### Integration Tests (`test_performance_allocation_integration.py`)

**Component Coupling**:
- **Full quarterly cycle**: Author Collaboration → Strategy Creation → Capital Allocation → Performance Allocation
- **Multi-quarter simulation**: High water mark tracking and fund growth over time
- **Strategy lifecycle integration**: Author enrollment through strategy contribution
- **Mixed strategy performance**: Profitable and unprofitable strategies in same quarter

**Realistic Scenarios**:
- **Crisis recovery**: High water mark reset after financial losses
- **Author collaboration**: Multiple authors on single profitable strategy
- **Portfolio evolution**: New strategies added, old strategies decay naturally
- **Safety net graduation**: Authors moving above guaranteed minimum over time

---

## Key Design Decisions

### Fund Accounting Alignment

The simulation keeps the existing quarterly step size while aligning fee and HWM logic to fund accounting:
- Management fee: 0.25% quarterly
- Performance allocation: 20% to authors, crystallized annually
- Safety net ratio: 50% of author allocation
- Guaranteed return: $1M lifetime minimum
- Investor flows create separate capital cohorts so new investors do not inherit old losses
- Investor withdrawals crystallize the redeemed share of year-to-date profit above that cohort's HWM/loss account

### Author ID-Based Tracking

Strategy ownership uses `author_id` strings as keys, not Author objects, enabling:
- Clean separation between components
- Efficient ownership tracking
- Simple proportional distribution logic

### High Water Mark Implementation

Complete high water mark accounting ensures:
- No performance fees during loss recovery
- Proper tracking of cohort-level cumulative losses
- Fair profit distribution only above each cohort's previous high
- No double counting after redemptions, because remaining cohort profits and strategy attribution are scaled after withdrawal crystallization

### Safety Net Eligibility

Only contributing authors (those who invented or improved strategies) are enrolled:
- Enrollment automatic upon successful strategy contribution
- Lifetime $1M guarantee for enrolled authors
- Equal distribution among eligible authors at annual crystallization
- Safety-net payments are capped at the remaining gap to the $1M guarantee

---

## Usage Example

```python
from components.performance_allocation import PerformanceAllocationManager
from components.performance_allocation.performance_allocation_parameters import PerformanceAllocationParameters as PAP
from components.capital_allocation import CapitalAllocationManager
from components.strategy_lifecycle.strategy_manager import StrategyManager

# Initialize components
strategy_manager = StrategyManager()
capital_manager = CapitalAllocationManager(strategy_manager)
performance_manager = PerformanceAllocationManager(
    strategy_manager=strategy_manager,
    initial_aum=PAP.FUND_INITIAL_AUM  # $20M from parameters
)

# Quarterly cycle: Capital Allocation → Performance Allocation
allocation_result = capital_manager.allocate_capital(
    available_capital=performance_manager.get_fund_aum(),
    quarter=1
)

# Generate strategy returns
current_allocations = capital_manager.get_current_allocations()
strategy_returns = strategy_manager.generate_returns(current_allocations)

# Process performance allocation
performance_result = performance_manager.process_quarterly_allocation(
    strategy_returns=strategy_returns,
    quarter=1
)

# Analyze results
print(f"High water mark met: {performance_result.high_water_mark_met}")
print(f"Management fee: ${performance_result.management_fee_charged:.2f}M")
print(f"Fund retention: ${performance_result.fund_retention:.1f}M")
print(f"Author payments: ${performance_result.get_total_author_payments():.1f}M")
print(f"Authors receiving performance: {performance_result.total_authors_receiving_performance}")
print(f"Authors receiving safety net: {performance_result.total_authors_receiving_safety_net}")
print(f"Final fund AUM: ${performance_result.fund_aum_end:.1f}M")
```

This component completes the core economic engine of the hedge fund simulation, providing the critical link between strategy performance and author compensation while maintaining fund sustainability through proper profit retention and risk management.
