# Performance Allocation Component

## Overview

The Performance Allocation Component implements the fund's quarterly profit-sharing system, distributing returns among the fund, strategy authors, and the safety net program. This component serves as the critical economic engine that incentivizes author contributions while ensuring sustainable fund operations and author income security.

The component processes strategy returns from Capital Allocation, applies high water mark accounting, and distributes profits through a three-way split: fund retention, author performance allocation, and safety net program funding.

---

## Files

- `performance_allocation_manager.py`: Main orchestrator for quarterly performance allocation with high water mark implementation.
- `allocation_summary.py`: Data structures for tracking allocation outcomes, efficiency metrics, and detailed reporting.
- `performance_allocation_parameters.py`: Configuration parameters matching iteration_one exactly.
- `__init__.py`: Component interface and version information.

---

## Business Logic Overview

### Performance Allocation Flow

The component operates in quarterly cycles following this sequence:

1. **Management Fee Collection**: 0.25% quarterly fee collected from fund AUM
2. **High Water Mark Calculation**: Determine if fund has net positive performance since last high
3. **Profit Attribution**: Link strategy returns to their contributing authors via ownership splits
4. **Performance Distribution**: Allocate 16% of profits proportionally to strategy authors
5. **Safety Net Assessment**: Identify enrolled authors below $4M guaranteed minimum
6. **Safety Net Distribution**: Distribute 4% of profits equally among eligible authors
7. **Fund Retention**: Add remaining 80% of profits to fund AUM

### Three-Tier Profit Distribution

```
Total Strategy Returns → High Water Mark Check
  ↓ (if profitable)
80% → Fund Retention
20% → Author Allocation Pool
  ├─ 80% (16% of total) → Performance payments to strategy authors
  └─ 20% (4% of total) → Safety Net Pool
```

### Safety Net Program

**Enrollment**: Authors automatically enrolled when they contribute to any strategy (invention or improvement).

**Eligibility**: Each quarter, enrolled authors with lifetime payments < $4M receive equal share of safety net pool.

**Distribution**: Safety net funds distributed equally among all eligible authors.

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
    # Step 1: Collect management fee (0.25% of AUM)
    management_fee = fund_aum * 0.0025
    fund_aum -= management_fee

    # Step 2: Apply high water mark
    cumulative_loss_account += sum(strategy_returns.values())
    if cumulative_loss_account > 0:
        distributable_profits = cumulative_loss_account
        cumulative_loss_account = 0
    else:
        return  # No distribution this quarter

    # Step 3: Calculate pools
    fund_retention = distributable_profits * 0.80
    performance_pool = distributable_profits * 0.16
    safety_net_pool = distributable_profits * 0.04

    # Step 4: Distribute performance allocation
    for strategy_id, returns in strategy_returns.items():
        strategy = get_strategy(strategy_id)
        strategy_share = (returns / total_returns) * performance_pool

        for author_id, ownership_pct in strategy.ownership_splits.items():
            payment = strategy_share * ownership_pct
            record_author_payment(author_id, payment)

    # Step 5: Distribute safety net
    eligible_authors = get_enrolled_authors_below_4M()
    if eligible_authors:
        payment_each = safety_net_pool / len(eligible_authors)
        for author_id in eligible_authors:
            record_safety_net_payment(author_id, payment_each)

    # Step 6: Add fund retention to AUM
    fund_aum += fund_retention
```

---

## Allocation Summary (`allocation_summary.py`)

Comprehensive data structure tracking quarterly performance allocation outcomes.

### Key Fields

- `quarter`, `total_strategy_returns`, `fund_aum_start`, `fund_aum_end`: Basic allocation metrics
- `management_fee_charged`: Quarterly management fee collected
- `high_water_mark_met`: Boolean indicating if profits were distributed
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
    FUND_INITIAL_AUM = 10.0  # $10M initial fund size

    # Management fees
    MANAGEMENT_FEE_RATE = 0.25  # 0.25% of AUM per quarter

    # Performance allocation
    PERFORMANCE_ALLOCATION = 0.2  # 20% of profits to authors
    AUTHOR_SAFETY_NET_RATIO = 0.2  # 20% of author allocation to safety net
    AUTHOR_GUARANTEED_RETURN = 4.0  # $4M lifetime minimum
```

**Derived Constants**:
- Fund Retention Rate: 80% of profits
- Author Performance Rate: 16% of profits (20% × 80%)
- Safety Net Rate: 4% of profits (20% × 20%)

---

## Testing

### Unit Tests (`test_performance_allocation.py`)

**Core Algorithm Testing**:
- **High water mark calculation**: Loss recovery scenarios and profit distribution
- **Performance attribution**: Correct author-strategy linking via ownership splits
- **Safety net eligibility**: Guaranteed minimum logic and equal distribution
- **Three-way profit split**: Exact percentage allocations and conservation

**Edge Cases**:
- **Zero profits**: No performance allocation, safety net still operates
- **Below high water mark**: No distributions during loss recovery
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

### Exact iteration_one Replication

All parameters and algorithms match iteration_one config.py exactly:
- Management fee: 0.25% quarterly
- Performance allocation: 20% to authors
- Safety net ratio: 20% of author allocation
- Guaranteed return: $4M lifetime minimum

### Author ID-Based Tracking

Strategy ownership uses `author_id` strings as keys, not Author objects, enabling:
- Clean separation between components
- Efficient ownership tracking
- Simple proportional distribution logic

### High Water Mark Implementation

Complete high water mark accounting ensures:
- No performance fees during loss recovery
- Proper tracking of cumulative losses
- Fair profit distribution only above previous highs

### Safety Net Eligibility

Only contributing authors (those who invented or improved strategies) are enrolled:
- Enrollment automatic upon successful strategy contribution
- Lifetime $4M guarantee for enrolled authors
- Equal distribution among eligible authors each quarter

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
    initial_aum=PAP.FUND_INITIAL_AUM  # $10M from parameters
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