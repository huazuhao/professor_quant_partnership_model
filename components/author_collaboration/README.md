# Author Collaboration

This package coordinates how research authors join the fund, choose activities, and convert collaboration into strategy inventions or improvements. It includes:

- An `Author` dataclass that tracks each researcher’s lifecycle, decisions, and contribution history.
- A `GroupActivity` record used to log every collaborative attempt and its outcome.
- An `AuthorCollaborationManager` that runs the quarterly cycle, forms groups, and routes successes to the strategy lifecycle component.
- An `AuthorFactory` for generating randomized or explicit author rosters for simulations and tests.
- Central `AuthorCollaborationParameters` that tune probabilities, durations, group sizes, and hiring rules.

---

## Modules

- `author.py`: Author and group activity data models plus contribution bookkeeping helpers.
- `author_collaboration_manager.py`: Orchestrates quarterly collaboration flow, group formation, outcomes, and hiring.
- `author_factory.py`: Utilities to create authors with randomized, explicit, or scenario-specific traits.
- `author_collaboration_parameters.py`: Tunable constants for collaboration dynamics with validation on import.
- `__init__.py`: Convenience exports for the component surface area.

---

## Business Logic Overview

- **Author lifecycle**: Each Author is hired with 2–4 quarters of research time, fixed invention/improvement biases, and automatically retires once that clock expires.
- **Quarterly decision funnel**: `process_quarterly_collaboration_cycle` advances every author, gathers available talent, and splits them into improvement or invention pools based on remaining time and personal probabilities.
- **Improvement workflow**: Improvement groups draw 1–3 members, choose return or capacity work, target strategies using type-specific weights, and on a win call `strategy_manager.process_improvements` to push upgrades into live strategies. One-quarter authors get first priority for scarce improvement slots; if preferred slots are saturated, flexible authors redirect into invention and last-quarter authors can receive overflow improvement assignments.
- **Invention pipeline**: Eligible authors lock into two-quarter invention groups; the manager carries them forward, resolves success probabilities later, and successful groups spawn new strategies via `StrategyFactory`.
- **Hiring feedback loop**: The manager estimates the active sabbatical bench needed for current AUM and adds new authors when active research supply is below target.
- **Contribution accounting**: Every attempt—successful or not—records `GroupActivity` entries and per-author contribution logs that downstream performance allocation can consume.

---

## Authors & Activities (`author.py`)

Selected fields
- `author_id`, `name`, `hire_quarter`: Identity and onboarding data.
- `remaining_research_quarters`, `total_research_quarters_spent`: Lifecycle tracking.
- `current_activity_state`: `'available'`, `'inventing_quarter_1'`, or `'retired'`.
- `invention_probability`, `improvement_probability`: Fixed per-author decision biases sampled at hire.
- Contribution history: `strategies_created`, `strategies_improved`, `lifetime_success_count`, `quarterly_contributions`.

Lifecycle helpers
- `advance_quarter()` decrements remaining research time, tallies quarters worked, and triggers `retire()` when time expires.
- `is_available_for_activity()` and `can_attempt_invention()` gate which actions an author may take in the current quarter.
- `start_invention_process(group_id)` and `complete_invention_process()` manage two-quarter invention state.

Contribution tracking
- `record_successful_contribution(...)` and `record_failed_contribution(...)` log outcomes, capture group composition, and keep shareable contribution summaries.
- `get_contribution_summary()` packages author-level data for performance allocation consumers.

Group activity records
- `GroupActivity` instances store group membership, activity type (`'improvement'`, `'invention_start'`, `'invention_complete'`), outcome, and any strategy identifiers involved.
- `calculate_group_success_probability(author_probabilities)` averages member probabilities and caches them alongside individual inputs.
- Helpers `is_invention_activity()`, `is_improvement_activity()`, `is_pending()`, and `get_summary()` support downstream reporting.

---

## Collaboration Manager (`author_collaboration_manager.py`)

Core registries
- Maintains `authors`, `authors_by_id`, `quarterly_group_activities`, and `active_invention_groups` for lookup and state continuity.

Quarterly cycle
- `process_quarterly_collaboration_cycle(quarter, strategy_manager)` executes six phases: advance all authors, resolve ongoing inventions, collect fresh decisions, run improvements, launch new inventions, and evaluate hiring.
- Returns a list of `GroupActivity` objects summarizing everything that happened in the quarter.

Decision logic
- `_collect_author_decisions()` splits available authors into improvement vs invention candidates based on remaining time and personal probabilities.
- `_form_improvement_groups()` / `_form_invention_groups()` assemble randomized groups of 1–3 members (bounded by parameter settings).

Improvements
- `_form_prioritized_improvement_groups()` separates one-quarter authors from flexible authors so researchers who cannot start a two-quarter invention process receive improvement-slot priority.
- `_assign_strategies_to_groups()` picks return vs capacity work, then assigns targets with a maximum of two improvement groups per strategy per quarter.
- Capacity work favors high-return strategies with room below the absolute capacity cap; return work favors positive-return strategies with room below the return cap.
- `_redirect_no_target_improvements_to_invention()` recycles no-target improvement demand into invention candidates when authors still have at least two quarters left.
- `_choose_overflow_improvement_target()` breaks the preferred per-strategy group cap only for authors who cannot invent and would otherwise have no activity.
- `_execute_improvement_groups()` computes group success odds (average of member improvement probabilities) and calls `strategy_manager.process_improvements(...)`.
- Successes tag the upgraded strategy, store improvement type, and mark every author’s contribution log; failures still record participation for auditing.

Invention handling
- `_start_invention_groups()` registers groups for the two-quarter invention process and locks author state.
- `_complete_ongoing_inventions()` resolves second-quarter groups, computes success using averaged invention probabilities, and on success builds a brand-new strategy via `StrategyFactory.create_new_strategy(...)` before registering it with the passed `strategy_manager`.

Hiring & reporting
- `_evaluate_author_hiring()` inspects `strategy_manager.get_portfolio_metrics()` and hires new authors (via `AuthorFactory.create_new_author`) once total capacity crosses the configured threshold.
- Reporting helpers return contributor lists (`get_strategy_contributors()`), per-author contribution summaries, full snapshots (`get_all_author_summaries()`), and per-quarter activity breakdowns (`get_quarterly_activity_summary()`).

---

## Author Factory (`author_factory.py`)

Creation utilities
- `create_new_author(...)` seeds randomized research duration plus invention/improvement probabilities within configured bounds.
- `create_author_with_explicit_params(...)` validates inputs and builds deterministic fixtures for testing.
- Scenario helpers produce pools with shared hire quarters, controlled probabilities, or fixed remaining time (`create_test_author_pool`, `create_author_with_specific_probabilities`, `create_authors_with_remaining_time`).

Analytics
- `get_author_stats_summary(authors)` computes aggregate counts, average remaining research time, and mean probabilities to reason about a roster at a glance.

---

## Parameters (`author_collaboration_parameters.py`)

Research duration
- `AUTHOR_RESEARCH_DURATION_MIN/MAX` define the 2–4 quarter research cycle sampled at hire.

Decision probabilities
- `AUTHOR_INVENTION_PROBABILITY_MIN/MAX` and `AUTHOR_IMPROVEMENT_PROBABILITY_MIN/MAX` bound the random draws for each author’s tendencies.

Group formation & success
- `GROUP_SIZE_MIN/MAX` enforce 1–3 member teams; group success always averages member probabilities.

Improvement knobs
- `PROB_OF_IMPROVE_RETURN` vs `PROB_OF_IMPROVE_CAPACITY` sets how successful groups choose improvement type. The current model uses a 50% return / 50% capacity split; `IMPROVEMENT_QUARTERS_REQUIRED` keeps improvements single-quarter.
- `MAX_IMPROVEMENT_GROUPS_PER_STRATEGY_PER_QUARTER` caps independent same-quarter research groups assigned to one strategy.

Invention knobs
- `INVENTION_QUARTERS_REQUIRED`, `INVENTION_MIN_REMAINING_QUARTERS`, and `INVENTION_GROUP_ID_PREFIX` manage two-quarter invention workflows.

Hiring & safety net
- `AUM_PER_AUTHOR` sets the target AUM coverage per active sabbatical researcher. The current model targets $45M per active author.
- `AUTHOR_HIRE_THRESHOLD_AUM` gates AUM-based hiring above the minimum active author count.
- Safety-net eligibility remains cumulative across active and retired contributors; safety-net authors do not count as active research capacity for new hiring.
- `AUTHOR_GUARANTEED_RETURN` captures the universal minimum payout logic used by downstream performance allocation.

Validation
- `validate_parameters()` enforces ranges (probabilities, durations, group sizes) and runs automatically at import so misconfigurations raise early.

---

## Workflow (Quarterly Collaboration Loop)

1) Hire or seed authors through `AuthorFactory` and register them with `AuthorCollaborationManager`.
2) Provide a `StrategyManager` instance (with any existing strategies) to supply improvement targets and receive new inventions.
3) Call `process_quarterly_collaboration_cycle(quarter, strategy_manager)` each quarter to advance author clocks and execute collaborative actions.
4) Review returned `GroupActivity` objects or `get_quarterly_activity_summary(quarter)` for reporting.
5) Feed contributor data (`get_strategy_contributors()`, `get_all_author_summaries()`) into performance allocation or compensation logic.

---

## Minimal Example

```python
from hedgedemia_business_model.version_2025_september.components.author_collaboration import (
    AuthorFactory, AuthorCollaborationManager
)
from hedgedemia_business_model.version_2025_september.components.strategy_lifecycle import (
    StrategyFactory, StrategyManager
)

# Seed collaboration component
collab = AuthorCollaborationManager()
for author in AuthorFactory.create_test_author_pool(num_authors=3, hire_quarter=0):
    collab.add_author(author)

# Provide at least one strategy so improvements have a target
strategy_manager = StrategyManager()
seed_strategy = StrategyFactory.create_new_strategy(collab.get_active_authors(), quarter=0)
strategy_manager.add_strategy(seed_strategy)

# Run a quarterly cycle
activities = collab.process_quarterly_collaboration_cycle(quarter=0, strategy_manager=strategy_manager)
summary = collab.get_quarterly_activity_summary(0)
print(len(activities), "activities")
print(summary)
```

---

## Notes and Edge Cases

- Authors automatically retire when their sampled research duration ends; reactivation is not currently supported.
- Invention attempts always last two quarters—authors are unavailable during the interim quarter.
- Improvement attempts prefer open strategy slots; no-target authors who can still support a two-quarter invention are redirected into invention, while last-quarter authors can use overflow improvement assignments that ignore the preferred per-strategy slot cap.
- Group success odds are simple averages of member probabilities; no diminishing returns or leadership modifiers are applied yet.
- Improvement groups are not merged together; same-strategy assignment is limited by the quarterly group-slot cap.
- Hiring logic is intentionally lightweight and keys off current fund AUM, with strategy capacity available as a fallback when AUM is not provided.
- Contribution logs intentionally record both successes and failures so downstream allocation can credit effort as needed.
