# Investor Flow Component

This component handles quarterly capital inflows and outflows based on fund performance using a continuous linear Gaussian model with regime-dependent constraints.

## Overview

The Investor Flow Component implements a sophisticated model where investor behavior responds realistically to fund performance:
- **Good performance** → Capital inflows (investors attracted)
- **Poor performance** → Capital outflows (investors redeem)
- **Neutral performance** → Mixed flows with noise

Unlike iteration_one's simple probabilistic model, this component uses a **continuous linear Gaussian model** that smoothly maps performance to flows while enforcing regime-consistent behavior.

---

## Business Logic Overview

### Core Flow Model

**Linear Performance Mapping with AUM-Based Scaling**:
```
μ_flow = α × R_4Q × m(AUM) × AUM

where:
  α = sensitivity parameter (0.5 by default)
  R_4Q = trailing 4-quarter compounded return
  m(AUM) = AUM-based multiplier (10x for small funds, 1x for large funds)
  AUM = current fund assets under management
```

**AUM Multiplier**: Smaller funds experience higher flow volatility as a percentage of AUM. The multiplier linearly interpolates between:
- **Small funds** ($10M or less): multiplier = 10x
- **Large funds** ($1B or more): multiplier = 1x
- **Medium funds**: linear interpolation

**Scaled Mean Cap**: The mean cap scales with the AUM multiplier to allow higher volatility for small funds:
- Base mean cap: ±5% of AUM
- Small fund ($10M): scaled cap = ±50% of AUM (5% × 10x)
- Large fund ($1B): scaled cap = ±5% of AUM (5% × 1x)

**Gaussian Sampling**:
```
Net_Flow ~ N(μ_flow, σ_flow)

where:
  σ_flow = volatility × AUM (10% by default)
```

**Two-Layer Clipping**:
1. **Layer 1 - Regime Sign Constraint**: Force flow sign to match performance
   - Positive returns → no outflows allowed (flows ≥ 0)
   - Negative returns → no inflows allowed (flows ≤ 0)
   - Near-zero returns → bidirectional flows allowed

2. **Layer 2 - Magnitude Caps**: Hard limits on flow size
   - Maximum inflow: 100% of AUM per quarter (fund can double)
   - Maximum outflow: 50% of AUM per quarter (fund can halve)

---

## Modules

- `investor_flow_manager.py`: Main flow orchestrator implementing the algorithm
- `flow_event.py`: Data structure tracking flow outcomes with full transparency
- `investor_flow_parameters.py`: Tunable constants with validation
- `__init__.py`: Component interface exports

---

## Files

### `investor_flow_manager.py`

Main orchestrator class that processes quarterly flows.

**Key Methods**:
- `process_quarterly_flows(current_aum, quarterly_return, quarter)`: Main entry point
- `get_flow_event(quarter)`: Retrieve specific quarter's flow event
- `get_flow_efficiency_stats()`: Aggregate statistics across all quarters

**Algorithm Steps**:
1. Update return history with this quarter's return
2. Calculate trailing 4Q compounded performance
3. Determine regime (positive/negative/zero)
4. Calculate Gaussian parameters (μ, σ)
5. Sample from Gaussian distribution
6. Apply Layer 1: Regime sign constraint
7. Apply Layer 2: Magnitude caps
8. Return FlowEvent with complete details

---

### `flow_event.py`

Comprehensive data structure tracking flow calculation stages.

**Key Fields**:
- `trailing_4q_returns`: Last 4 quarterly returns
- `mean_flow_dollars`, `std_flow_dollars`: Distribution parameters
- `net_flow_sampled`: Raw Gaussian sample
- `net_flow_after_sign_constraint`: After Layer 1
- `net_flow_final`: After Layer 2 (final value)
- `regime_type`: "positive", "negative", or "zero"
- `regime_constraint_applied`, `magnitude_cap_applied`: Flags

**Properties**:
- `flow_as_pct_of_aum`: Final flow as % of AUM
- `aum_growth_rate`: AUM growth from flows
- `any_constraint_applied`: Whether clipping occurred

---

### `investor_flow_parameters.py`

Centralized configuration with validation.

**Parameters**:
```python
PERFORMANCE_LOOKBACK_QUARTERS = 4    # Trailing return window
FLOW_SENSITIVITY_ALPHA = 0.5         # Performance → flow sensitivity
MAX_MEAN_FLOW_PCT = 0.05             # ±5% AUM max mean

# AUM-based sensitivity scaling
AUM_MULTIPLIER_ENABLED = True        # Enable AUM-based multiplier
AUM_MULTIPLIER_MIN_AUM = 10.0        # $10M → high multiplier
AUM_MULTIPLIER_MAX_AUM = 1000.0      # $1B → multiplier = 1
AUM_MULTIPLIER_AT_MIN_AUM = 10.0     # 10x for small funds
AUM_MULTIPLIER_AT_MAX_AUM = 1.0      # 1x for large funds

FLOW_VOLATILITY_PCT = 0.10           # 10% AUM std dev
ENFORCE_REGIME_SIGN = True           # Enable regime constraints
ZERO_RETURN_TOLERANCE = 0.001        # ±0.1% is "zero"
MAX_INFLOW_PCT = 1.0                 # 100% AUM max inflow (fund can double)
MAX_OUTFLOW_PCT = 0.5                # 50% AUM max outflow (fund can halve)
```

---

## Integration Points

### With Performance Allocation Component

**Input Dependencies** (Investor Flow reads from Performance Allocation):

```python
# Get current AUM before flows
current_aum = performance_manager.get_fund_aum()

# Get this quarter's return for history tracking
quarterly_return = performance_manager.get_quarterly_return_percentage(quarter)

# Alternative: Get trailing returns directly
trailing_returns = performance_manager.get_trailing_returns(quarter, quarters=4)
```

**Output Dependencies** (Investor Flow writes to Performance Allocation):

```python
# Update AUM with net flows
performance_manager.update_aum(flow_event.net_flow_final)
```

### Integration Pattern in Quarterly Simulation

```python
# MID-QUARTER: After Performance Allocation, before Capital Allocation

# Step 1: Get current state from Performance Allocation
current_aum = performance_manager.get_fund_aum()
quarterly_return = performance_manager.get_quarterly_return_percentage(quarter)

# Step 2: Process investor flows
flow_event = investor_flow_manager.process_quarterly_flows(
    current_aum=current_aum,
    quarterly_return=quarterly_return,
    quarter=quarter
)

# Step 3: Update AUM for next capital allocation
performance_manager.update_aum(flow_event.net_flow_final)

# Step 4: Capital Allocation uses updated AUM
updated_aum = performance_manager.get_fund_aum()
capital_manager.allocate_capital(updated_aum, quarter + 1)
```

---

## Testing

### Unit Tests

Test core functionality in isolation:
- Parameter validation
- Regime determination logic
- Linear mapping calculations
- Gaussian sampling
- Two-layer clipping (sign + magnitude)
- FlowEvent data structure

### Integration Tests

Test component coupling:
- Full quarterly cycle with Performance Allocation
- Multi-quarter simulation with flow history
- AUM propagation to Capital Allocation
- Edge cases (zero AUM, extreme returns, etc.)

---

## Usage Example

```python
from components.investor_flow import InvestorFlowManager
from components.performance_allocation import PerformanceAllocationManager
from components.capital_allocation import CapitalAllocationManager
from components.strategy_lifecycle import StrategyManager

# Initialize components
strategy_manager = StrategyManager()
capital_manager = CapitalAllocationManager(strategy_manager)
performance_manager = PerformanceAllocationManager(
    strategy_manager=strategy_manager,
    initial_aum=10.0  # $10M
)
investor_flow_manager = InvestorFlowManager()

# Quarterly simulation loop
for quarter in range(20):
    # START OF QUARTER: Generate returns
    allocations = capital_manager.get_current_allocations()
    strategy_returns = strategy_manager.generate_returns(allocations)

    # Process performance allocation
    perf_summary = performance_manager.process_quarterly_allocation(
        strategy_returns=strategy_returns,
        quarter=quarter
    )

    # MID-QUARTER: Process investor flows
    flow_event = investor_flow_manager.process_quarterly_flows(
        current_aum=performance_manager.get_fund_aum(),
        quarterly_return=performance_manager.get_quarterly_return_percentage(quarter),
        quarter=quarter
    )

    # Update AUM with flows
    performance_manager.update_aum(flow_event.net_flow_final)

    # END OF QUARTER: Allocate capital for next quarter
    updated_aum = performance_manager.get_fund_aum()
    capital_manager.allocate_capital(updated_aum, quarter + 1)

    # Print flow summary
    print(f"Q{quarter}: Return={flow_event.trailing_4q_total_return:.1%}, "
          f"Flow=${flow_event.net_flow_final:.1f}M ({flow_event.regime_type}), "
          f"AUM=${flow_event.aum_after_flow:.1f}M")
```

**Example Output**:
```
Q0: Return=0.0%, Flow=$0.0M (zero), AUM=$10.0M
Q1: Return=3.2%, Flow=$2.1M (positive), AUM=$12.3M
Q2: Return=5.8%, Flow=$5.7M (positive), AUM=$19.1M
Q3: Return=-2.1%, Flow=-$1.8M (negative), AUM=$16.4M
Q4: Return=4.5%, Flow=$3.2M (positive), AUM=$21.5M
```

---

## Mathematical Details

### Trailing Performance Calculation

Compounded return over last 4 quarters:
```
R_4Q = (1 + r_{t-3})(1 + r_{t-2})(1 + r_{t-1})(1 + r_t) - 1
```

Example:
```
Q t-3: +3% → 0.03
Q t-2: +5% → 0.05
Q t-1: -2% → -0.02
Q t:   +4% → 0.04

R_4Q = (1.03)(1.05)(0.98)(1.04) - 1 = 0.1039 = 10.39%
```

### Distribution Parameters

**AUM Multiplier**:
```
if AUM >= AUM_MULTIPLIER_MAX_AUM:
    m(AUM) = AUM_MULTIPLIER_AT_MAX_AUM  # 1.0 for large funds

elif AUM <= AUM_MULTIPLIER_MIN_AUM:
    m(AUM) = AUM_MULTIPLIER_AT_MIN_AUM  # 10.0 for small funds

else:
    # Linear interpolation
    m(AUM) = AUM_MULTIPLIER_AT_MIN_AUM +
             (AUM - AUM_MULTIPLIER_MIN_AUM) × slope

    where slope = (AUM_MULTIPLIER_AT_MAX_AUM - AUM_MULTIPLIER_AT_MIN_AUM) /
                  (AUM_MULTIPLIER_MAX_AUM - AUM_MULTIPLIER_MIN_AUM)
```

**Mean flow**:
```
μ_pct_raw = FLOW_SENSITIVITY_ALPHA × R_4Q × m(AUM)

# Scaled mean cap (scales with AUM multiplier)
scaled_cap = MAX_MEAN_FLOW_PCT × m(AUM)
μ_pct = clip(μ_pct_raw, -scaled_cap, +scaled_cap)

μ_dollars = μ_pct × AUM

# Example for small fund ($10M, m=10x, R_4Q=20%):
# μ_pct_raw = 0.5 × 0.20 × 10 = 1.0 (100%)
# scaled_cap = 0.05 × 10 = 0.5 (50%)
# μ_pct = clip(1.0, -0.5, 0.5) = 0.5 (50%)
```

**Standard deviation** (constant):
```
σ_pct = FLOW_VOLATILITY_PCT
σ_dollars = σ_pct × AUM
```

### Regime Sign Constraint (Layer 1)

```python
if R_4Q > ZERO_RETURN_TOLERANCE:
    # Positive regime: force non-negative
    flow = max(flow_sampled, 0)
elif R_4Q < -ZERO_RETURN_TOLERANCE:
    # Negative regime: force non-positive
    flow = min(flow_sampled, 0)
else:
    # Zero regime: allow either sign
    flow = flow_sampled
```

### Magnitude Caps (Layer 2)

```python
max_inflow = MAX_INFLOW_PCT × AUM   # 100% of AUM
max_outflow = MAX_OUTFLOW_PCT × AUM  # 50% of AUM
flow_final = clip(flow, -max_outflow, +max_inflow)

# Small fund can double in one quarter (100% inflow)
# Small fund can halve in one quarter (50% outflow)
```

---

## Key Design Decisions

### Continuous Linear Model

**Advantages**:
- Smooth response to performance (no discontinuous jumps)
- Intuitive parameters (sensitivity α, volatility σ)
- Automatic sign matching (positive returns → positive mean)

**vs. Discrete Step Function**:
- iteration_one used discrete sentiment states with Bernoulli trials
- Linear model is smoother and easier to calibrate

### Regime-Dependent Constraints

**Rationale**: Prevents unrealistic behavior
- Positive performance shouldn't trigger investor panic
- Negative performance shouldn't attract new capital
- Zero-tolerance parameter handles edge cases near 0% return

### Two-Layer Clipping

**Layer 1** (sign) ensures directional consistency
**Layer 2** (magnitude) prevents extreme flows

This separation provides transparency and modularity.

### AUM-Based Sensitivity Scaling

**Rationale**: Reflects realistic fund dynamics
- Small funds: More volatile flows as % of AUM (easier to double or halve)
- Large funds: More stable flows as % of AUM (harder to move the needle)
- Linear interpolation provides smooth transition as funds grow

**Scaled Caps**: Both the mean cap and multiplier scale together
- Small fund ($10M): Mean can reach ±50% (5% × 10x), magnitude caps at 100%/-50%
- Large fund ($1B): Mean capped at ±5% (5% × 1x), magnitude caps still 100%/-50%
- This allows small funds to experience extreme flows while capping large funds

**Economic Interpretation**:
- $10M fund with +20% return and α=0.5 → up to 50% expected flow (capped at 50%)
- $1B fund with +20% return and α=0.5 → up to 10% expected flow (capped at 5%)
- This mirrors real-world investor behavior and fund capacity constraints

---

## Component Dependencies

**Required**:
- Performance Allocation Component (provides AUM and returns)
- NumPy (for Gaussian sampling and clipping)

**Optional**:
- External Shock Component (future enhancement for crisis-aware flows)

**Independent**:
- Capital Allocation (reads AUM indirectly via Performance Allocation)
- Strategy Lifecycle (no direct interaction)
- Author Collaboration (parallel component)

---

## Future Enhancements

### Crisis-Aware Flows

Integrate with External Shock Component:
```python
if crisis_occurred_recently:
    redemption_multiplier = CRISIS_PANIC_FACTOR
    mean_flow *= redemption_multiplier
```

### Performance-Scaled Volatility

Dynamic volatility based on regime:
```python
if regime == "negative":
    std_flow *= PANIC_VOLATILITY_MULTIPLIER  # More chaos during downturns
```

### AUM-Scaled Flow Amounts (IMPLEMENTED)

✅ **Now implemented** as AUM-based sensitivity multiplier. Smaller funds experience higher flow volatility as a percentage of AUM, while larger funds have more stable flows.

---

## Version History

- **v1.0.0** (2025-01): Initial implementation with linear Gaussian model and regime constraints

---

This component completes the capital flow cycle, enabling realistic fund growth and contraction dynamics based on performance.
