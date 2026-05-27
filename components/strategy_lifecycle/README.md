# Strategy Lifecycle

This package models how trading strategies are created, evolve over quarters, and contribute to a portfolio. It includes:

- A `Strategy` dataclass with return distribution, capacity, natural decay, improvements, crisis drawdown, and tracking.
- A `StrategyFactory` to create strategies with randomized parameters or explicit inputs.
- A `StrategyManager` to hold many strategies, generate returns, apply lifecycle updates, handle crises, and compute portfolio metrics.
- Centralized `StrategyParameters` to tune all behaviors without editing logic.

---

## Modules

- `strategy.py`: Strategy lifecycle and behavior for a single strategy.
- `strategy_factory.py`: Helpers for creating strategies (randomized or explicit).
- `strategy_manager.py`: Orchestration across many strategies and portfolio utilities.
- `strategy_parameters.py`: Constants that configure distributions, capacity, lifecycle, and risk.
- `__init__.py`: Convenience re‑exports for simpler imports.

---

## Business Logic Overview

- **Strategy lifecycle**: Each Strategy starts with sampled return, risk, and capacity traits, then naturally decays every quarter until improvements or poor performance deactivate it.
- **Capital deployment**: Active capacity represents dollars at work; returns and crisis losses scale directly with this figure to mirror real portfolio exposure management.
- **Improvement gating**: Return and capacity upgrades are probabilistic, capped by `StrategyParameters`, and logged with timestamps so other components can throttle repeated boosts.
- **Portfolio orchestration**: StrategyManager centralizes add/remove flows, advances quarters, aggregates gains, and exposes metrics other components (e.g., hiring, allocation) rely on.
- **Risk shock handling**: Crisis simulations feed a base drawdown that the manager fans out by each strategy’s beta to stress-test the book without touching structural capacity.
- **Feedback loops**: Portfolio metrics—counts, capacity, expected return, beta—form the signals that upstream modules (author hiring, capital allocation) use to adjust staffing and funding.

---

## Strategy (`strategy.py`)

Selected fields
- `strategy_id: str`: Unique identifier (factory uses UUID if you don’t supply one).
- `authors: List`: Author identifiers or domain objects.
- `ownership_splits: Dict`: Mapping author → share (factory uses equal split).
- `quarter_created: int`: Quarter index at creation.
- Return distribution: `distribution_type: {'t','uniform'}`, `distribution_loc: float`, `distribution_scale: float`.
- Capacity: `max_capacity: float` (millions), `active_capacity: float` (clamped to `max_capacity`).
- Risk: `beta: float` (market sensitivity used to scale crisis losses).
- Status/metrics: `is_active: bool`, `quarters_since_creation: int`, `last_improvement_quarter: int`, `total_improvements: int`,
  `cumulative_returns: float` (dollars), `quarterly_returns: List[float]` (decimals, e.g., 0.02 for +2%).

Initialization
- `__post_init__` builds a SciPy distribution (`t` or `uniform`) using the configured `loc` and `scale`.
- `get_expected_return()` and `get_return_volatility()` read the distribution’s mean and std (percent units).

Lifecycle mechanics
- Natural decay (`apply_natural_decay`):
  - If active and expected return > 0: decrease `distribution_loc` by `expected_return × STRATEGY_RETURN_DECAY_RATE`.
  - Rebuild the distribution; if expected return drops below `STRATEGY_MIN_ACTIVE_RETURN`, mark inactive.
- Improvements:
  - Returns (`improve_returns(quarter)`): If active and below `STRATEGY_MAX_EXPECTED_RETURN`, increase `distribution_loc` by `|expected_return| × STRATEGY_RETURN_IMPROVEMENT_FACTOR`, then cap at `STRATEGY_MAX_EXPECTED_RETURN`. Updates improvement counters.
- Capacity (`improve_capacity(quarter)`): If active and below `STRATEGY_MAX_CAPACITY_ABSOLUTE`, add an absolute deployable-capital increment sampled from `STRATEGY_CAPACITY_IMPROVEMENT_FACTOR_MIN/MAX`, then clamp to `STRATEGY_MAX_CAPACITY_ABSOLUTE`. Updates improvement counters.

Performance
- `generate_quarterly_return(allocated_capital)`:
  - If active and `allocated_capital > 0`: sample a return percent from the distribution, convert to decimal, compute `$PnL = allocated_capital × return_decimal`.
  - Appends the decimal return to `quarterly_returns` and accumulates `cumulative_returns` in dollars.
- `apply_crisis_drawdown(base_drawdown)`:
  - If active and `active_capacity > 0`: loss percent `= base_drawdown × beta`; dollar loss `= active_capacity × (loss% / 100)`. Deduct from `cumulative_returns`.

Utilities
- `set_active_capacity(capacity)`: Sets `active_capacity` but never above `max_capacity`.
- `advance_quarter()`: Increments `quarters_since_creation`.

Units and conventions
- Distribution mean and std are percents; quarterly returns stored on the strategy are decimals.
- Capacity units are in “millions” consistently across code and examples.

---

## Factory (`strategy_factory.py`)

Randomized creation: `create_new_strategy(authors, quarter, strategy_id=None)`
- Equal ownership splits across provided `authors`.
- Chooses distribution type using `STRATEGY_T_DISTRIBUTION_PROB` (t‑distribution is favored by default).
- Samples distribution parameters within the configured bounds.
- Samples `max_capacity` within `[STRATEGY_INITIAL_CAPACITY_MIN, STRATEGY_INITIAL_CAPACITY_MAX]`.
- Samples `beta` within `[STRATEGY_BETA_MIN, STRATEGY_BETA_MAX]`.
- Accepts only if initial expected return > 0; otherwise retries with fresh parameters.

Explicit creation: `create_strategy_with_params(...)`
- Build a `Strategy` with precise parameters (useful for tests/fixtures).

---

## Manager (`strategy_manager.py`)

Collections and lookup
- Maintains `strategies: List[Strategy]` and `strategies_by_id: Dict[str, Strategy]`.
- `add_strategy` registers the strategy and enables O(1) id lookup.
- `get_strategy_by_id` returns a strategy or `None`.
- `get_active_strategies` filters active strategies with positive expected returns.
- `get_all_strategies` returns every strategy regardless of status.

Quarterly operations
- `generate_returns(capital_allocations) → Dict[str, float]`:
  - For each `strategy_id: allocated_capital`, calls the strategy’s `generate_quarterly_return` to produce a dollar PnL.
- `apply_quarterly_decay_all()`:
  - For each active strategy, applies natural decay and advances the quarter.
- `process_improvements([(strategy_id, improvement_type, quarter), ...]) → Dict[str, bool]`:
  - Supports `improvement_type in {'return','capacity'}`; returns success flags per id.

Crisis handling
- `apply_crisis_all(base_drawdown) → Dict[str, float]`:
  - For each active strategy with non‑zero `active_capacity`, applies a beta‑scaled drawdown and returns dollar losses per id.

Portfolio metrics
- `get_portfolio_metrics() → Dict` returns:
  - `num_active_strategies`: count of currently active strategies with positive expected returns
  - `total_capacity`: sum of `max_capacity` across active strategies
  - `total_active_capacity`: sum of `active_capacity` across active strategies
  - `avg_expected_return`: mean of expected returns (percent) across active strategies
  - `avg_beta`: average beta across active strategies
  - `capacity_utilization`: `total_active_capacity / total_capacity` (0 if denominator is 0)

---

## Parameters (`strategy_parameters.py`)

Return distributions (quarterly, percent units)
- Choice probabilities: `STRATEGY_T_DISTRIBUTION_PROB`, `STRATEGY_UNIFORM_DISTRIBUTION_PROB` (the latter is informational; selection uses the t‑prob).
- Student‑t: `T_DISTRIBUTION_LOC_MIN/MAX`, `T_DISTRIBUTION_SCALE_MIN/MAX`, `T_DISTRIBUTION_DEGREES_OF_FREEDOM` (fat tails).
- Uniform: `UNIFORM_DISTRIBUTION_LOC_MIN/MAX` (lower bound range), `UNIFORM_DISTRIBUTION_SCALE_MIN/MAX` (width range).

Capacity
- Initial range: `STRATEGY_INITIAL_CAPACITY_MIN/MAX` (`$10M-$50M`).
- Hard cap: `STRATEGY_MAX_CAPACITY_ABSOLUTE` (`$100M`).

Lifecycle and improvements
- Decay: `STRATEGY_RETURN_DECAY_RATE` and inactive threshold `STRATEGY_MIN_ACTIVE_RETURN`.
- Return improvement: `STRATEGY_RETURN_IMPROVEMENT_FACTOR` and cap `STRATEGY_MAX_EXPECTED_RETURN`.
- Capacity improvement: `STRATEGY_CAPACITY_IMPROVEMENT_FACTOR_MIN/MAX` (`+$10M` to `+$50M`).

Risk profile
- Beta range: `STRATEGY_BETA_MIN/MAX`.

---

## Workflow (Quarterly Simulation)

1) Create strategies via the factory (random or explicit params).
2) Add them to `StrategyManager`.
3) Set `active_capacity` per strategy (never exceeds `max_capacity`).
4) For each quarter:
   - Generate returns from your allocations via `generate_returns`.
   - Apply decay and advance time via `apply_quarterly_decay_all`.
   - Optionally call `process_improvements` with targeted return/capacity upgrades.
   - Optionally call `apply_crisis_all` to simulate drawdowns.
   - Inspect `get_portfolio_metrics` for portfolio‑level summary.

---

## Minimal Example

```python
from hedgedemia_business_model.version_2025_september.components.strategy_lifecycle import (
    StrategyFactory, StrategyManager
)

authors = ["alice", "bob"]
q = 0
s1 = StrategyFactory.create_new_strategy(authors, q)
s2 = StrategyFactory.create_new_strategy(authors, q)

m = StrategyManager()
m.add_strategy(s1)
m.add_strategy(s2)

s1.set_active_capacity(10)
s2.set_active_capacity(15)
alloc = {s1.strategy_id: s1.active_capacity, s2.strategy_id: s2.active_capacity}

pnl = m.generate_returns(alloc)
m.apply_quarterly_decay_all()
m.process_improvements([(s1.strategy_id, 'return', q+1), (s2.strategy_id, 'capacity', q+1)])
losses = m.apply_crisis_all(base_drawdown=10.0)
metrics = m.get_portfolio_metrics()
print(metrics)
```

---

## Notes and Edge Cases

- Factory retries: Creation keeps sampling until the initial expected return is positive.
- Units: Strategy return stats are percents; stored quarterly returns are decimals; PnL/cumulative totals are dollars.
- Inactivity: Strategies turn inactive when expected return falls below `STRATEGY_MIN_ACTIVE_RETURN`. Reactivation logic is not implemented.
- Crisis scope: Crisis impacts PnL only; it does not change capacities.
