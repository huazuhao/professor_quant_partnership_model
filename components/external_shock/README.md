# External Shock Component

This component handles financial crisis events that differentially impact strategies based on their beta (market sensitivity).

## Overview

The External Shock Component models market crises using:
- **Exponential distribution** for crisis timing (average 1 crisis per 40 quarters / 10 years)
- **Normal distribution** for crisis severity (mean 20%, std 5%)
- **Beta-scaled losses** per strategy (defensive strategies lose less than aggressive ones)

Unlike iteration_one (which applied uniform 20% losses to all strategies), this component provides **realistic differentiation** where high-beta strategies suffer more during crises.

---

## Business Logic

### Crisis Generation

**Exponential Timer**:
- Uses exponential distribution with λ = 1/40
- Countdown decrements each quarter
- When countdown ≤ 0: CRISIS TRIGGERED
- New countdown sampled for next crisis

**Crisis Severity**:
```
base_drawdown ~ N(μ=20%, σ=5%)
Clipped to [5%, 40%] to avoid extreme outliers
```

**Strategy-Specific Impact**:
```
strategy_loss = base_drawdown × strategy_beta × active_capacity

Example with base_drawdown = 20%:
- Defensive strategy (beta=0.5, $10M deployed): loses $1.0M (10% × $10M)
- Neutral strategy (beta=1.0, $10M deployed): loses $2.0M (20% × $10M)
- Aggressive strategy (beta=2.0, $10M deployed): loses $4.0M (40% × $10M)
```

---

## Modules

- `external_shock_manager.py`: Main crisis orchestrator
- `crisis_event.py`: Data structure for crisis records
- `external_shock_parameters.py`: Configuration parameters
- `__init__.py`: Component interface exports

---

## Files

### `external_shock_manager.py`

Main orchestrator class that manages crisis events.

**Key Methods**:
- `check_and_apply_crisis(quarter, strategy_manager)`: Main coupling method called each quarter
- `get_crisis_event(quarter)`: Retrieve specific quarter's crisis event
- `get_crisis_statistics()`: Aggregate statistics across all crises

**Algorithm**:
1. Decrement crisis countdown
2. If countdown ≤ 0:
   a. Sample base_drawdown from normal distribution
   b. Clip to reasonable bounds [5%, 40%]
   c. Call `strategy_manager.apply_crisis_all(base_drawdown)`
   d. Receive dollar losses per strategy
   e. Reset countdown for next crisis
3. Create CrisisEvent record
4. Return event

---

### `crisis_event.py`

Data structure tracking complete crisis information.

**Key Fields**:
- `quarter`: When crisis occurred
- `occurred`: Boolean flag
- `base_drawdown`: Base severity before beta scaling
- `losses_by_strategy`: Dict[strategy_id, loss_amount]
- `total_losses`: Sum of all strategy losses

**Properties**:
- `num_strategies_affected`: Count of impacted strategies
- `average_loss_per_strategy`: Mean loss across strategies

---

### `external_shock_parameters.py`

Centralized configuration with validation.

**Parameters**:
```python
# Crisis frequency
CRISIS_LAMBDA = 1/40  # One crisis every 40 quarters on average

# Crisis severity (normal distribution)
CRISIS_DRAWDOWN_MEAN = 20.0   # Average: 20% base drawdown
CRISIS_DRAWDOWN_STD = 5.0     # Std deviation: 5%

# Severity bounds (clip extreme outliers)
CRISIS_DRAWDOWN_MIN = 5.0     # Minimum: mild crisis
CRISIS_DRAWDOWN_MAX = 40.0    # Maximum: catastrophic crisis
```

---

## Integration Points

### With Strategy Lifecycle Component

**Input Dependencies** (External Shock reads from Strategy Lifecycle):

```python
# Apply crisis via existing infrastructure
losses = strategy_manager.apply_crisis_all(base_drawdown)
# Returns: Dict[strategy_id, dollar_loss]
```

**No modifications needed** to Strategy Lifecycle - `apply_crisis_all()` method already exists!

### Integration Pattern in Quarterly Simulation

```python
# AFTER strategy returns generation, BEFORE performance allocation

for quarter in range(num_quarters):
    # ... generate returns ...
    strategy_returns = strategy_manager.generate_returns(allocations)

    # Check for crisis
    crisis_event = external_shock_manager.check_and_apply_crisis(
        quarter=quarter,
        strategy_manager=strategy_manager
    )

    if crisis_event.occurred:
        # Crisis losses already applied to strategies via apply_crisis_all()
        # Subtract losses from strategy_returns for performance allocation
        for strategy_id, loss in crisis_event.losses_by_strategy.items():
            strategy_returns[strategy_id] -= loss

    # ... performance allocation uses crisis-adjusted returns ...
```

---

## Testing

### Unit Tests

Test core functionality in isolation:
- Exponential timer countdown
- Normal distribution sampling for severity
- Crisis event creation
- Statistics aggregation

### Integration Tests

Test component coupling:
- Full quarterly cycle with Strategy Lifecycle
- Multi-quarter simulation with multiple crises
- Crisis impact on Performance Allocation
- Parameter logging

---

## Usage Example

```python
from components.external_shock import ExternalShockManager
from components.strategy_lifecycle import StrategyManager

# Initialize components
strategy_manager = StrategyManager()
external_shock_manager = ExternalShockManager()

# Quarterly simulation loop
for quarter in range(80):
    # ... capital allocation, returns generation ...

    # Check for crisis
    crisis_event = external_shock_manager.check_and_apply_crisis(
        quarter=quarter,
        strategy_manager=strategy_manager
    )

    if crisis_event.occurred:
        print(f"Q{quarter}: CRISIS! Base: {crisis_event.base_drawdown:.1f}%, "
              f"Losses: ${crisis_event.total_losses:.1f}M")

# Get crisis statistics
stats = external_shock_manager.get_crisis_statistics()
print(f"Total crises: {stats['total_crises']}")
print(f"Average base drawdown: {stats['average_base_drawdown']:.1f}%")
print(f"Total losses: ${stats['total_losses']:.1f}M")
```

**Example Output**:
```
Q48: CRISIS! Base: 23.8%, Losses: $4.9M
Q66: CRISIS! Base: 16.7%, Losses: $1.4M

Total crises: 2
Average base drawdown: 20.3%
Total losses: $6.3M
```

---

## Key Design Decisions

### Exponential vs Fixed Timing

**Chosen**: Exponential distribution
- **Realistic**: Crises don't occur on fixed schedules
- **Variable**: Some decades crisis-free, others have multiple
- **Matches iteration_one**: Same approach as original model

### Normal Distribution for Severity

**Chosen**: Normal(μ=20%, σ=5%) clipped to [5%, 40%]
- **Realistic**: Most crises ~20%, rare extreme events
- **Tunable**: Easy to adjust mean/variance
- **Bounded**: Clips prevent unrealistic 50%+ drawdowns

### Beta-Scaled Impact

**Chosen**: `loss = base_drawdown × beta`
- **Differentiates strategies**: Defensive vs aggressive
- **Already implemented**: Uses existing `Strategy.beta` attribute
- **Realistic**: Higher market sensitivity = higher crisis losses

### No Recovery Mechanics

**Chosen**: Crisis is one-time permanent shock
- **Simple**: No gradual recovery modeling
- **Realistic**: Losses to cumulative returns are permanent
- **Can enhance later**: Add recovery dynamics if needed

---

## Component Dependencies

**Required**:
- Strategy Lifecycle Component (provides `apply_crisis_all()` method)
- NumPy (for normal distribution sampling)
- SciPy (for exponential distribution)

**Independent**:
- Performance Allocation (receives crisis-adjusted returns)
- Capital Allocation (no direct interaction)
- Author Collaboration (no direct interaction)
- Investor Flow (crisis doesn't trigger panic - can be enhanced later)

---

## Future Enhancements

### Crisis-Triggered Investor Panic

Integrate with Investor Flow Component:
```python
if crisis_event.occurred:
    redemption_multiplier = CRISIS_PANIC_FACTOR  # e.g., 3x normal redemptions
    investor_flow_manager.apply_panic_redemptions(multiplier)
```

### Multiple Crisis Types

Different flavors with different characteristics:
- Market crash (high beta impact)
- Liquidity crisis (impacts high-capacity strategies)
- Volatility spike (impacts low-volatility strategies)

### Tail Hedge Strategies (Negative Beta)

Allow strategies with beta < 0 that GAIN during crises:
- 95% normal strategies: beta ∈ [0.5, 2.0]
- 5% tail hedges: beta ∈ [-1.0, 0.0]

---

## Version History

- **v1.0.0** (2025-01): Initial implementation with exponential timing and normal severity

---

This component completes the 6-component architecture, enabling realistic crisis modeling with differentiated strategy impacts!
