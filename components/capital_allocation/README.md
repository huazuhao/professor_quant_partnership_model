# Capital Allocation Component

## Overview

The Capital Allocation Component implements quarterly capital deployment across active strategies using the greedy allocation algorithm. It acts as the bridge between strategy creation (Author Collaboration) and return generation (Strategy Lifecycle), ensuring fund capital flows to strategies with the highest expected returns while respecting capacity constraints.

---

## Files

- `capital_allocation_manager.py`: Main orchestrator for quarterly capital allocation with greedy algorithm implementation.
- `allocation_result.py`: Data structures for tracking allocation outcomes, efficiency metrics, and detailed reporting.
- `__init__.py`: Component interface and version information.

---

## Business Logic Overview

- **Capital deployment**: Every quarter, completely rebalances portfolio by resetting all `active_capacity` to 0 and reallocating based on current expected returns.
- **Greedy algorithm**: Sorts strategies by expected return (highest first) and allocates maximum possible capital to each until fund capital exhausted or all strategy capacities filled.
- **Capacity constraints**: Respects each strategy's `max_capacity` limit and only allocates to strategies with positive expected returns.
- **Allocation tracking**: Records detailed allocation history including deployment efficiency, strategy counts, and capital distribution for analysis and integration with other components.
- **Portfolio rebalancing**: Ensures optimal capital allocation each quarter independent of previous allocations through complete rebalancing approach.

---

## Capital Allocation Manager (`capital_allocation_manager.py`)

Main orchestrator class that implements the core allocation algorithm.

### Key Methods

- `allocate_capital(available_capital, quarter)`: Primary allocation method implementing greedy algorithm.
- `rebalance_portfolio(available_capital, quarter)`: Alias for `allocate_capital` maintaining clean interface for future enhancements.
- `get_allocation_summary(quarter)`: Detailed allocation report for specific quarter including efficiency metrics.
- `get_current_allocations()`: Current capital deployment across all strategies from StrategyManager.
- `get_allocation_efficiency_stats()`: Historical efficiency statistics across all tracked quarters.

### Algorithm Implementation

```python
# Greedy allocation algorithm:
1. Reset all strategy.active_capacity = 0
2. Get strategies with positive expected returns
3. Create candidates: [expected_return, max_capacity, strategy]
4. Sort candidates by expected_return (descending)
5. For each candidate:
   - Calculate max_allocation = min(strategy.max_capacity, remaining_capital)
   - If max_allocation > 0: strategy.set_active_capacity(max_allocation)
   - Update remaining_capital -= max_allocation
   - Stop if remaining_capital <= 0
```

---

## Allocation Result (`allocation_result.py`)

Data structure for comprehensive allocation outcome tracking.

### Key Fields

- `quarter`, `total_available_capital`, `total_deployed_capital`, `undeployed_capital`: Basic allocation metrics.
- `allocation_by_strategy`: Dictionary mapping strategy_id to allocated amount for detailed tracking.
- `strategy_count`: Number of strategies that received capital allocation.

### Computed Properties

- `allocation_efficiency`: Deployed capital ratio (deployed/available), key metric for fund performance analysis.
- `average_strategy_allocation`: Mean allocation per funded strategy for diversification analysis.

### Methods

- `get_summary()`: Complete allocation report including all metrics and strategy details.
- `get_top_allocations(n)`: Top N strategies by allocation amount for concentration analysis.

---

## Integration Points

### With Strategy Lifecycle Component

**Input interfaces:**
- `StrategyManager.get_active_strategies()`: Retrieves strategies with positive expected returns for allocation consideration.
- `Strategy.get_expected_return()`: Used for sorting strategies in greedy allocation algorithm.
- `Strategy.max_capacity`: Enforced as hard constraint during capital allocation.

**Output interfaces:**
- `Strategy.set_active_capacity(amount)`: Sets allocated capital amount, never exceeding max_capacity.
- Integration with `StrategyManager.generate_returns(allocations)`: Provides allocation dictionary for return calculation.

### With Author Collaboration Component

**Indirect coupling:** No direct interface, but Author Collaboration creates strategies that Capital Allocation then funds. The pipeline flows: Authors → Strategies → Capital Allocation → Returns.

### With Future Components

**Performance Allocation Component:** `get_allocation_summary()` provides detailed allocation data needed for performance fee calculations and profit attribution to strategy creators.

**Investor Flow Component:** Allocation efficiency metrics inform investor confidence and capital inflow decisions.

---

## Testing

### Unit Tests (`test_capital_allocation.py`)
- **AllocationResult validation:** Data structure integrity, efficiency calculations, summary generation.
- **CapitalAllocationManager core logic:** Greedy algorithm, capacity constraints, sorting behavior.
- **Integration with Strategy Lifecycle:** Real strategy creation, allocation tracking, history management.
- **Edge cases:** No strategies, zero capital, capacity limitations, negative return handling.

### Integration Tests (`test_capital_allocation_integration.py`)
- **Full simulation cycles:** Multi-quarter fund operation with Author Collaboration → Strategy creation → Capital allocation → Return generation.
- **Component coupling:** Strategy improvements affecting allocation priority, natural decay impact on capital deployment.
- **Portfolio rebalancing:** Complete reallocation each quarter, allocation efficiency tracking across time.
- **Mixed strategy states:** New, improved, and decayed strategies in same portfolio allocation cycle.

---

## Key Design Decisions

### Parameter-Free Design
The component has **no configuration parameters**. The allocation algorithm is purely deterministic based on strategy expected returns and capacity constraints.

### Complete Rebalancing
Every quarter completely resets portfolio allocations and reallocates optimally, ensuring capital always flows to current best opportunities regardless of historical allocations.

### Greedy Algorithm Implementation
Implements proven allocation logic: sort by expected return descending, allocate greedily respecting capacity constraints, stop when capital exhausted.

### Clean Component Interfaces
Maintains clear separation from other components while providing necessary integration points for Strategy Lifecycle and future Performance Allocation components.

---

## Usage Example

```python
from components.capital_allocation import CapitalAllocationManager
from components.strategy_lifecycle.strategy_manager import StrategyManager

# Initialize components
strategy_manager = StrategyManager()
capital_manager = CapitalAllocationManager(strategy_manager)

# Add strategies (typically created by Author Collaboration Component)
# strategy_manager.add_strategy(strategy1)
# strategy_manager.add_strategy(strategy2)

# Quarterly capital allocation
result = capital_manager.allocate_capital(
    available_capital=1000.0,  # $1B fund
    quarter=1
)

# Analyze allocation
print(f"Deployed: ${result.total_deployed_capital}M")
print(f"Efficiency: {result.allocation_efficiency:.1%}")
print(f"Strategies funded: {result.strategy_count}")

# Generate returns based on allocations
current_allocations = capital_manager.get_current_allocations()
strategy_returns = strategy_manager.generate_returns(current_allocations)
```

This component serves as the critical link between strategy creation and return generation, ensuring optimal capital deployment across the fund's strategy portfolio.