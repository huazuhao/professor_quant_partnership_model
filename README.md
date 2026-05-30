# Professor Quant Partnership Model

This repository studies a new research-lab funding model made possible by the rapid improvement of LLM coding.

University labs in mathematics, statistics, optimization, simulation, computational modeling, and related STEM fields already have the talent systematic hedge funds rely on. The old bottleneck was implementation: turning a research idea into clean data, backtests, diagnostics, risk controls, deployment code, and monitoring usually took more engineering time than a short sabbatical or research leave could support.

LLM-assisted coding changes that. A 6- to 12-month sabbatical can now be enough for professors to help invent or improve systematic trading strategies. If validated strategies are traded, part of the profits can fund the contributing labs over the following years.

In the current simulation, this loop can start with $20M of initial capital and grow into a $1B+ fund. The median 10-year investor outcome is about 3x capital, 120 professor/lab groups receive funding, and five-year lab cumulative compensation is above $1M at the median.

![Professor-led quant research funding loop](assets/funding_loop.svg)

[Download the PDF overview](professor_quant_partnership_model_overview.pdf)

## The One-Minute Version

- Professors contribute the core research hedge funds need: math, statistics, optimization, modeling, simulation, and rigorous empirical testing.
- LLM coding makes it realistic to turn those ideas into testable trading systems during a 6- to 12-month sabbatical.
- The fund provides capital, data, execution infrastructure, monitoring, and continuity.
- Strategy gains or losses are applied to the fund immediately.
- Professor/lab payouts are made from eligible profits after investor loss recovery.
- Professor/lab payouts are split between performance-based rewards and a safety-net pool.
- The simulation suggests this could become a large, repeatable alternative funding model for university labs, with successful contributors receiving more than $1M in cumulative support over the following years.

## Current Simulated Economics

The simulation models the accounting in sequence: operating fee, strategy gains or losses, investor loss recovery, then professor/lab payouts from eligible profits.

Current baseline assumptions:

- Initial fund capital: `$20 million`
- Operating fee: `0.25% per quarter`
- Strategy gains or losses: applied to the fund immediately
- Investor recovery check: prior investor losses are repaired before professor/lab payouts
- Professor/lab payout pool: `20%` share of profits
- Performance payout: `50%` of the professor/lab payout pool
- Safety-net payout: `50%` of the professor/lab payout pool
- Safety-net guarantee: up to `$1M` cumulative support per eligible professor/lab
- Active professor research target: about one active strategy professor per `$45M` of AUM
- New strategy birth capacity: `$10M-$50M`
- Absolute capacity per strategy: `$100M`

## Current Simulation Results

The current baseline batch run uses `100` paths, `40` quarters, and seed `42`.

| Metric | Median / Current Baseline Result |
| --- | ---: |
| Initial fund capital | `$20 million` |
| Final fund size after 10 years | `$1.27 billion` median |
| Median 10-year investor value | `$100` grows to `$302.52` |
| Professor/lab groups receiving funding after 10 years | `120` median |
| Five-year cumulative professor/lab compensation | `$1.34 million` median |
| Five-year cumulative compensation, p75 | `$1.63 million` |
| Five-year cumulative compensation, p90 | `$2.00 million` |

These are simulation outputs, not forecasts. The purpose is to test whether the economic loop is internally coherent and whether the scale of the research-funding impact is large enough to justify deeper investigation.

## Simulation Charts

| Investor outcome | Professor/lab compensation |
| --- | --- |
| ![Investment value distribution](batch_plot1_investment_value_distribution.png) | ![Five-year compensation distribution](batch_plot2_5year_compensation_distribution.png) |

| Final fund size | Professor/lab groups receiving funding |
| --- | --- |
| ![Final fund size distribution](batch_plot3_final_aum_distribution.png) | ![Professor/lab groups receiving funding distribution](batch_plot5_paid_author_count_distribution.png) |

## What The Model Simulates

The simulation is built from several interacting components:

- `strategy_lifecycle`: strategy invention, decay, capacity limits, and capacity improvements
- `author_collaboration`: professor research cycles, strategy invention, strategy improvement, and ownership assignment
- `capital_allocation`: capital deployment across available strategies
- `performance_allocation`: operating fees, investor loss recovery, professor/lab payouts, and safety-net payouts
- `investor_flow`: subscriptions, withdrawals, AUM growth limits, and capacity-aware inflow acceptance
- `external_shock`: crisis events and market stress

The model separates three important strategy concepts:

- deployed capital: how much capital is currently allocated to a strategy
- current strategy capacity: how much capital the strategy can currently accept
- absolute strategy capacity: a hard ceiling no single strategy can exceed

It also separates two professor-contributor concepts:

- active sabbatical professors: currently available to invent or improve strategies
- safety-net professor contributors: cumulative contributors who may still be eligible for compensation

## Run The Simulation

Set up the environment:

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

Run one detailed simulation:

```bash
venv/bin/python run_single_simulation.py --quarters 40 --seed 40
```

Run the current batch simulation:

```bash
venv/bin/python run_batch_simulation.py --runs 100 --quarters 40 --seed 42
```

Run tests:

```bash
venv/bin/python -m unittest discover -s tests
```

## Repository Map

```text
.
|-- README.md
|-- UNIVERSITY_PARTNERSHIP_PROPOSAL.md
|-- run_single_simulation.py
|-- run_batch_simulation.py
|-- components/
|   |-- author_collaboration/
|   |-- capital_allocation/
|   |-- external_shock/
|   |-- investor_flow/
|   |-- performance_allocation/
|   `-- strategy_lifecycle/
|-- tests/
|-- assets/
`-- batch_plot*.png
```

## Important Caveat

This is an economic simulation and proposal model. It is not investment advice or a live trading system. The goal is to make the assumptions explicit, test the accounting logic, and estimate whether a professor-led quant research partnership could plausibly become a meaningful alternative funding source for university labs.
