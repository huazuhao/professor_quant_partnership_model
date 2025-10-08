#!/usr/bin/env python3
"""
Demonstration of Performance Allocation Component.

Shows the complete integration with other components in a realistic
fund simulation scenario with comprehensive logging.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt

from components.performance_allocation import PerformanceAllocationManager, PerformanceAllocationParameters as PAP
from components.capital_allocation import CapitalAllocationManager
from components.strategy_lifecycle.strategy_manager import StrategyManager
from components.strategy_lifecycle.strategy_factory import StrategyFactory
from components.author_collaboration.author_collaboration_manager import AuthorCollaborationManager
from components.author_collaboration.author_factory import AuthorFactory
from components.author_collaboration.author_collaboration_parameters import AuthorCollaborationParameters as ACP
from components.investor_flow import InvestorFlowManager
from components.external_shock import ExternalShockManager
from simulation_logger import SimulationLogger, collect_all_parameters


def generate_simulation_plots(quarters, cumulative_authors, fund_aum, quarterly_flows, quarterly_returns, author_5yr_compensations, investment_values, author_manager, output_dir):
    """
    Generate 7 separate plots from simulation data.

    Args:
        quarters: List of quarter indices
        cumulative_authors: List of cumulative author counts
        fund_aum: List of fund AUM values
        quarterly_flows: List of quarterly investor flows
        quarterly_returns: List of quarterly returns (% before fees)
        author_5yr_compensations: List of lifetime compensations at 5-year mark
        investment_values: List of $100 investment values over time
        author_manager: AuthorCollaborationManager instance
        output_dir: Directory to save plots

    Returns:
        List of paths to saved plot files
    """
    import os

    plot_paths = []

    # Plot 1: Cumulative Authors Over Time (Line)
    fig1, ax1 = plt.subplots(figsize=(10, 6))
    ax1.plot(quarters, cumulative_authors, linewidth=2, color='#2E86AB', marker='o', markersize=4)
    ax1.set_xlabel('Quarter', fontsize=12)
    ax1.set_ylabel('Cumulative Authors Ever Hired', fontsize=12)
    ax1.set_title('Total Authors in Program Over Time', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    plt.tight_layout()
    plot1_path = os.path.join(output_dir, 'plot1_cumulative_authors.png')
    plt.savefig(plot1_path, dpi=300, bbox_inches='tight')
    plt.close()
    plot_paths.append(plot1_path)

    # Plot 2: Author Compensation Distribution (Histogram)
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    all_authors = author_manager.get_all_authors()
    compensations = []
    for author in all_authors:
        total_comp = author.get_lifetime_payments()
        if total_comp > 0:  # Only include authors who received compensation
            compensations.append(total_comp)

    if compensations:
        ax2.hist(compensations, bins=30, color='#A23B72', alpha=0.7, edgecolor='black')
        ax2.set_xlabel('Lifetime Compensation ($M)', fontsize=12)
        ax2.set_ylabel('Number of Authors', fontsize=12)
        ax2.set_title('Author Compensation Distribution', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='y')
    else:
        ax2.text(0.5, 0.5, 'No compensation data', ha='center', va='center', transform=ax2.transAxes)
        ax2.set_title('Author Compensation Distribution', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plot2_path = os.path.join(output_dir, 'plot2_compensation_distribution.png')
    plt.savefig(plot2_path, dpi=300, bbox_inches='tight')
    plt.close()
    plot_paths.append(plot2_path)

    # Plot 3: Fund AUM Over Time (Line)
    fig3, ax3 = plt.subplots(figsize=(10, 6))
    ax3.plot(quarters, fund_aum, linewidth=2, color='#F18F01', marker='o', markersize=4)
    ax3.set_xlabel('Quarter', fontsize=12)
    ax3.set_ylabel('Fund AUM ($M)', fontsize=12)
    ax3.set_title('Fund Assets Under Management', fontsize=14, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    plt.tight_layout()
    plot3_path = os.path.join(output_dir, 'plot3_fund_aum.png')
    plt.savefig(plot3_path, dpi=300, bbox_inches='tight')
    plt.close()
    plot_paths.append(plot3_path)

    # Plot 4: Quarterly Investor Flows (Bar)
    fig4, ax4 = plt.subplots(figsize=(10, 6))
    colors = ['#06A77D' if flow >= 0 else '#D62246' for flow in quarterly_flows]
    ax4.bar(quarters, quarterly_flows, color=colors, alpha=0.7, edgecolor='black', linewidth=0.5)
    ax4.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    ax4.set_xlabel('Quarter', fontsize=12)
    ax4.set_ylabel('Net Flow ($M)', fontsize=12)
    ax4.set_title('Quarterly Investor Inflows/Outflows', fontsize=14, fontweight='bold')
    ax4.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plot4_path = os.path.join(output_dir, 'plot4_investor_flows.png')
    plt.savefig(plot4_path, dpi=300, bbox_inches='tight')
    plt.close()
    plot_paths.append(plot4_path)

    # Plot 5: Quarterly Fund Returns (Bar)
    fig5, ax5 = plt.subplots(figsize=(10, 6))
    colors = ['#27ae60' if ret >= 0 else '#e74c3c' for ret in quarterly_returns]
    ax5.bar(quarters, quarterly_returns, color=colors, alpha=0.7, edgecolor='black', linewidth=0.5)
    ax5.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    ax5.set_xlabel('Quarter', fontsize=12)
    ax5.set_ylabel('Return (%)', fontsize=12)
    ax5.set_title('Quarterly Fund Returns (Before Fees)', fontsize=14, fontweight='bold')
    ax5.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plot5_path = os.path.join(output_dir, 'plot5_quarterly_returns.png')
    plt.savefig(plot5_path, dpi=300, bbox_inches='tight')
    plt.close()
    plot_paths.append(plot5_path)

    # Plot 6: 5-Year Author Compensation Snapshot (Histogram)
    fig6, ax6 = plt.subplots(figsize=(10, 6))
    if author_5yr_compensations:
        ax6.hist(author_5yr_compensations, bins=25, color='#8E44AD', alpha=0.7, edgecolor='black', linewidth=0.8)
        mean_comp = sum(author_5yr_compensations) / len(author_5yr_compensations)
        ax6.axvline(x=mean_comp, color='red', linestyle='--', linewidth=2,
                    label=f'Mean: ${mean_comp:.2f}M')
        ax6.set_xlabel('Lifetime Compensation at 5-Year Mark ($M)', fontsize=12)
        ax6.set_ylabel('Number of Authors', fontsize=12)
        ax6.set_title(f'Compensated Author Earnings at 5-Year Anniversary\n(n={len(author_5yr_compensations)} authors who received payments)',
                      fontsize=14, fontweight='bold')
        ax6.legend(fontsize=11)
        ax6.grid(True, alpha=0.3, axis='y')
    else:
        ax6.text(0.5, 0.5, 'No compensated authors reached 5-year mark', ha='center', va='center',
                 transform=ax6.transAxes, fontsize=12)
        ax6.set_title('Compensated Author Earnings at 5-Year Anniversary', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plot6_path = os.path.join(output_dir, 'plot6_5year_compensation.png')
    plt.savefig(plot6_path, dpi=300, bbox_inches='tight')
    plt.close()
    plot_paths.append(plot6_path)

    # Plot 7: $100 Investment Value Over Time (Line)
    # Note: investment_values includes Q0, so create quarters list with Q0
    fig7, ax7 = plt.subplots(figsize=(12, 7))

    # Determine color based on final value
    final_value = investment_values[-1]
    line_color = '#27ae60' if final_value >= 100 else '#e74c3c'

    # Create quarters list including Q0
    investment_quarters = [0] + quarters[:len(investment_values)-1]
    ax7.plot(investment_quarters, investment_values, linewidth=2.5, color=line_color, marker='o', markersize=5)
    ax7.axhline(y=100, color='black', linestyle='--', linewidth=1.5, alpha=0.7, label='Break-even ($100)')

    # Fill area to show gain/loss
    ax7.fill_between(investment_quarters, 100, investment_values,
                     where=[v >= 100 for v in investment_values],
                     color='#27ae60', alpha=0.2, label='Gain')
    ax7.fill_between(investment_quarters, 100, investment_values,
                     where=[v < 100 for v in investment_values],
                     color='#e74c3c', alpha=0.2, label='Loss')

    # Calculate metrics
    total_return = ((final_value - 100) / 100) * 100
    num_years = (len(investment_values) - 1) / 4  # Subtract Q0
    annualized_return = ((final_value / 100) ** (1 / num_years) - 1) * 100 if num_years > 0 else 0

    # Add text box with metrics
    metrics_text = f'Final Value: ${final_value:.2f}\n'
    metrics_text += f'Total Return: {total_return:+.1f}%\n'
    if num_years >= 1:
        metrics_text += f'Annualized: {annualized_return:+.1f}%'

    ax7.text(0.02, 0.98, metrics_text, transform=ax7.transAxes,
             fontsize=11, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    ax7.set_xlabel('Quarter', fontsize=12)
    ax7.set_ylabel('Investment Value ($)', fontsize=12)
    ax7.set_title('$100 Investment Growth Over Time (Net of All Fees)', fontsize=14, fontweight='bold')
    ax7.legend(fontsize=11, loc='lower right')
    ax7.grid(True, alpha=0.3)
    plt.tight_layout()
    plot7_path = os.path.join(output_dir, 'plot7_investment_value.png')
    plt.savefig(plot7_path, dpi=300, bbox_inches='tight')
    plt.close()
    plot_paths.append(plot7_path)

    return plot_paths


def run_simulation_core(num_quarters: int = 5, initial_authors: int = None, random_seed: int = 42, silent: bool = False):
    """
    Core simulation logic without plotting or logging.

    Args:
        num_quarters: Number of quarters to simulate
        initial_authors: Initial author count (default: uses ACP.INITIAL_AUTHOR_COUNT)
        random_seed: Random seed for reproducibility
        silent: If True, suppress all console output

    Returns:
        dict with keys:
            - final_investment_value: Final value of $100 investment
            - author_5yr_compensations: List of compensations at 5-year mark
            - final_aum: Final fund AUM
            - total_authors: Total authors ever hired
            - investment_values: Full list of investment values over time
    """
    import random
    import numpy as np

    # Use parameter default if not specified
    if initial_authors is None:
        initial_authors = ACP.INITIAL_AUTHOR_COUNT

    # Set random seed for reproducibility
    random.seed(random_seed)
    np.random.seed(random_seed)

    # Data tracking
    author_5yr_compensations = []
    investment_values = [100.0]

    if not silent:
        print(f"🔄 Running simulation: {num_quarters} quarters, seed={random_seed}")

    # Initialize all components
    author_manager = AuthorCollaborationManager()
    strategy_manager = StrategyManager()
    capital_manager = CapitalAllocationManager(strategy_manager)
    performance_manager = PerformanceAllocationManager(
        strategy_manager=strategy_manager,
        author_manager=author_manager,
        initial_aum=PAP.FUND_INITIAL_AUM
    )
    investor_flow_manager = InvestorFlowManager()
    external_shock_manager = ExternalShockManager()

    # Create initial authors
    initial_author_pool = AuthorFactory.create_test_author_pool(initial_authors, hire_quarter=0)
    for author in initial_author_pool:
        author_manager.add_author(author)

    # Create seed strategy
    if initial_authors > 0:
        seed_strategy = StrategyFactory.create_new_strategy(
            authors=initial_author_pool,
            quarter=0,
            strategy_id="seed_strategy"
        )
        seed_strategy.active_capacity = seed_strategy.max_capacity
        strategy_manager.add_strategy(seed_strategy)

    # Run simulation
    for quarter in range(1, num_quarters + 1):
        current_aum = performance_manager.get_fund_aum()

        # Phase 1: Author collaboration
        activities, author_stats = author_manager.process_quarterly_collaboration_cycle(
            quarter=quarter,
            strategy_manager=strategy_manager,
            current_aum=current_aum
        )

        # Phase 2: Strategy decay
        if quarter > 1:
            strategy_manager.apply_quarterly_decay_all()

        # Phase 3: Capital allocation
        available_capital = performance_manager.get_fund_aum()
        allocation_result = capital_manager.allocate_capital(
            available_capital=available_capital,
            quarter=quarter
        )

        # Phase 4: Generate returns
        current_allocations = capital_manager.get_current_allocations()
        strategy_returns = {}
        if current_allocations:
            strategy_returns = strategy_manager.generate_returns(current_allocations)

        # Phase 4.5: External shock
        crisis_event = external_shock_manager.check_and_apply_crisis(
            quarter=quarter,
            strategy_manager=strategy_manager
        )

        if crisis_event.occurred:
            for strategy_id, loss in crisis_event.losses_by_strategy.items():
                strategy_returns[strategy_id] -= loss

        # Phase 5: Performance allocation
        performance_result = performance_manager.process_quarterly_allocation(
            strategy_returns=strategy_returns,
            quarter=quarter
        )

        # Track $100 investment NAV return (before investor flows)
        nav_return = (performance_result.fund_aum_end - current_aum) / current_aum if current_aum > 0 else 0.0
        new_investment_value = investment_values[-1] * (1 + nav_return)
        investment_values.append(new_investment_value)

        # Phase 6: Investor flows
        flow_event = investor_flow_manager.process_quarterly_flows(
            current_aum=performance_manager.get_fund_aum(),
            quarterly_return=performance_manager.get_quarterly_return_percentage(quarter),
            quarter=quarter
        )

        # Update AUM with investor flows
        performance_manager.update_aum(flow_event.net_flow_final)

        # Check for 5-year anniversaries
        for author in author_manager.get_all_authors():
            tenure = quarter - author.hire_quarter
            if tenure == 20:
                lifetime_comp = author.get_lifetime_payments()
                if lifetime_comp > 0:
                    author_5yr_compensations.append(lifetime_comp)

    # Calculate paid authors count (authors who received any compensation)
    all_authors = author_manager.get_all_authors()
    paid_authors_count = sum(1 for author in all_authors if author.get_lifetime_payments() > 0)

    # Return results
    return {
        'final_investment_value': investment_values[-1],
        'author_5yr_compensations': author_5yr_compensations,
        'num_5yr_authors': len(author_5yr_compensations),  # Count of 5-year authors
        'final_aum': performance_manager.get_fund_aum(),
        'total_authors': len(all_authors),
        'paid_authors': paid_authors_count,
        'investment_values': investment_values
    }


def run_demo(use_logging: bool = True, num_quarters: int = 5, initial_authors: int = None, random_seed: int = 42):
    """
    Run demonstration of Performance Allocation Component with full output and plots.

    Args:
        use_logging: Enable file logging (default: True)
        num_quarters: Number of quarters to simulate (default: 5)
        initial_authors: Initial author count (default: uses ACP.INITIAL_AUTHOR_COUNT)
        random_seed: Random seed for reproducibility (default: 42)
    """
    import random
    import numpy as np

    # Use parameter default if not specified
    if initial_authors is None:
        initial_authors = ACP.INITIAL_AUTHOR_COUNT

    # Set random seed for reproducibility
    random.seed(random_seed)
    np.random.seed(random_seed)

    # Setup logging if enabled
    logger = None
    if use_logging:
        logger = SimulationLogger(
            base_log_dir="simulation_runs",
            run_name="demo_performance_allocation"
        )
        logger.start_logging()

        # Collect and log all parameters
        all_params = collect_all_parameters()
        all_params['SIM.NUM_QUARTERS'] = num_quarters
        all_params['SIM.INITIAL_AUTHORS'] = initial_authors
        all_params['SIM.RANDOM_SEED'] = random_seed
        logger.log_parameters(all_params)

    # Data tracking for plots
    quarters_list = []
    cumulative_authors_list = []
    fund_aum_list = []
    quarterly_flows_list = []
    quarterly_returns_list = []
    author_5yr_compensations = []  # Lifetime compensation at 5-year mark
    investment_values = [100.0]  # Track $100 investment value (starts at Q0 = $100)

    print("🏦 Hedgedemia Fund Performance Allocation Demonstration")
    print("=" * 60)

    # Initialize all components
    print("\n📊 Initializing Components...")
    author_manager = AuthorCollaborationManager()
    strategy_manager = StrategyManager()
    capital_manager = CapitalAllocationManager(strategy_manager)
    performance_manager = PerformanceAllocationManager(
        strategy_manager=strategy_manager,
        author_manager=author_manager,
        initial_aum=PAP.FUND_INITIAL_AUM
    )
    investor_flow_manager = InvestorFlowManager()
    external_shock_manager = ExternalShockManager()

    print(f"   Initial Fund AUM: ${performance_manager.get_fund_aum():.1f}M")
    print(f"   Management Fee Rate: {PAP.MANAGEMENT_FEE_RATE}%")
    print(f"   Performance Allocation: {PAP.PERFORMANCE_ALLOCATION * 100}%")
    print(f"   Safety Net Guarantee: ${PAP.AUTHOR_GUARANTEED_RETURN}M")

    # Create initial authors
    print("\n👥 Creating Author Pool...")
    initial_author_pool = AuthorFactory.create_test_author_pool(initial_authors, hire_quarter=0)
    for author in initial_author_pool:
        author_manager.add_author(author)
    print(f"   Created {len(initial_author_pool)} authors")

    # Create seed strategy to bootstrap the fund
    if initial_authors > 0:
        print("\n🌱 Creating Seed Strategy...")
        seed_strategy = StrategyFactory.create_new_strategy(
            authors=initial_author_pool,
            quarter=0,
            strategy_id="seed_strategy"
        )

        # Set active capacity to max (fully deployable immediately)
        seed_strategy.active_capacity = seed_strategy.max_capacity

        # Add to strategy manager
        strategy_manager.add_strategy(seed_strategy)

        # Log seed strategy details
        expected_return = seed_strategy.get_expected_return()
        print(f"   Strategy ID: {seed_strategy.strategy_id}")
        print(f"   Distribution: {seed_strategy.distribution_type}")
        print(f"   Expected Return: {expected_return:.2f}%")
        print(f"   Capacity: ${seed_strategy.max_capacity:.1f}M")
        print(f"   Beta: {seed_strategy.beta:.2f}")
        print(f"   Ownership: {len(initial_author_pool)} authors ({100/len(initial_author_pool):.1f}% each)")

    # Run multi-quarter simulation
    print("\n🔄 Running Multi-Quarter Fund Simulation...")
    print("-" * 60)

    for quarter in range(1, num_quarters + 1):
        print(f"\n📅 Quarter {quarter}")
        current_aum = performance_manager.get_fund_aum()
        current_authors = len(author_manager.get_active_authors())
        print(f"   Starting AUM: ${current_aum:.1f}M | Authors: {current_authors}")

        # Phase 1: Author collaboration (pass current AUM for hiring decisions)
        activities, author_stats = author_manager.process_quarterly_collaboration_cycle(
            quarter=quarter,
            strategy_manager=strategy_manager,
            current_aum=current_aum
        )

        print(f"   📝 Author group activities: {len(activities)}")
        print(f"      👥 Authors: +{author_stats['authors_hired']} hired, -{author_stats['authors_retired']} retired")
        print(f"      📈 Strategies: {author_stats['strategies_created']} created, "
              f"{author_stats['capacity_improvements']} capacity ↑, {author_stats['return_improvements']} return ↑")
        print(f"      📊 Improvable: {author_stats['strategies_improvable_capacity']} capacity, "
              f"{author_stats['strategies_improvable_return']} return")

        # Phase 2: Strategy decay
        if quarter > 1:
            strategy_manager.apply_quarterly_decay_all()

        # Phase 3: Capital allocation
        available_capital = performance_manager.get_fund_aum()
        allocation_result = capital_manager.allocate_capital(
            available_capital=available_capital,
            quarter=quarter
        )
        print(f"   💰 Capital allocated: ${allocation_result.total_deployed_capital:.1f}M")
        print(f"   📈 Active strategies: {allocation_result.strategy_count}")

        # Phase 4: Generate returns
        current_allocations = capital_manager.get_current_allocations()
        strategy_returns = {}
        if current_allocations:
            strategy_returns = strategy_manager.generate_returns(current_allocations)
            total_returns = sum(strategy_returns.values())
            print(f"   💵 Total returns: ${total_returns:.1f}M")

        # Phase 4.5: External Shock (Crisis Check)
        crisis_event = external_shock_manager.check_and_apply_crisis(
            quarter=quarter,
            strategy_manager=strategy_manager
        )

        if crisis_event.occurred:
            # Crisis losses already applied to strategies via apply_crisis_all()
            # Subtract losses from strategy_returns
            for strategy_id, loss in crisis_event.losses_by_strategy.items():
                strategy_returns[strategy_id] -= loss

            print(f"   ⚠️  CRISIS! Base drawdown: {crisis_event.base_drawdown:.1f}%, Total losses: ${crisis_event.total_losses:.1f}M")

        # Phase 5: Performance allocation
        performance_result = performance_manager.process_quarterly_allocation(
            strategy_returns=strategy_returns,
            quarter=quarter
        )

        # Display results
        print(f"\n   💰 Fees & Profit Distribution:")
        print(f"      📋 Management Fee (charged quarterly):")
        print(f"         🏦 0.25% of ${current_aum:.1f}M AUM = ${performance_result.management_fee_charged:.2f}M")

        print(f"\n      📊 Performance Returns:")
        print(f"         💵 Total strategy returns: ${performance_result.total_strategy_returns:.1f}M")

        if performance_result.high_water_mark_met:
            print(f"         ✅ High water mark met! Distributable: ${performance_result.distributable_profits:.1f}M")

            print(f"\n      📈 Profit Distribution (quarterly):")
            print(f"         💼 Fund retention (80%): ${performance_result.fund_retention:.1f}M")

            print(f"\n         👨‍💼 Performance Pool (16% of profits): ${performance_result.author_performance_total:.1f}M")
            if performance_result.total_authors_receiving_performance > 0:
                avg_perf = performance_result.author_performance_total / performance_result.total_authors_receiving_performance
                print(f"            └─ {performance_result.total_authors_receiving_performance} authors with profitable strategies (avg ${avg_perf:.3f}M)")

            print(f"\n         🛡️  Safety Net Pool (4% of profits): ${performance_result.safety_net_total:.1f}M")
            if performance_result.total_authors_receiving_safety_net > 0:
                avg_safety = performance_result.safety_net_total / performance_result.total_authors_receiving_safety_net
                print(f"            └─ {performance_result.total_authors_receiving_safety_net} enrolled authors below $4M guarantee (avg ${avg_safety:.3f}M)")

                # Show the gap if it exists
                gap = performance_result.total_authors_receiving_safety_net - performance_result.total_authors_receiving_performance
                if gap > 0:
                    print(f"            └─ ({gap} authors receive only safety net - no profitable strategies)")
        else:
            print(f"         ❌ Below high water mark (Loss account: ${performance_manager.get_cumulative_loss_account():.1f}M)")

        print(f"   📊 AUM after performance allocation: ${performance_result.fund_aum_end:.1f}M")

        # Track $100 investment NAV return (before investor flows)
        # NAV return = (AUM after fees - AUM before) / AUM before
        nav_return = (performance_result.fund_aum_end - current_aum) / current_aum if current_aum > 0 else 0.0
        new_investment_value = investment_values[-1] * (1 + nav_return)
        investment_values.append(new_investment_value)

        # Phase 6: Investor flows (based on trailing performance)
        flow_event = investor_flow_manager.process_quarterly_flows(
            current_aum=performance_manager.get_fund_aum(),
            quarterly_return=performance_manager.get_quarterly_return_percentage(quarter),
            quarter=quarter
        )

        # Display investor flow results
        if flow_event.net_flow_final > 0:
            print(f"   💰 Investor inflow: ${flow_event.net_flow_final:.2f}M ({flow_event.flow_as_pct_of_aum:.1%} of AUM)")
        elif flow_event.net_flow_final < 0:
            print(f"   💸 Investor outflow: ${abs(flow_event.net_flow_final):.2f}M ({abs(flow_event.flow_as_pct_of_aum):.1%} of AUM)")
        else:
            print(f"   ➡️  No net investor flows")

        print(f"      Trailing 4Q return: {flow_event.trailing_4q_total_return:.1%}")
        print(f"      Flow regime: {flow_event.regime_type}")
        print(f"      AUM multiplier: {flow_event.aum_multiplier:.2f}x")
        if flow_event.any_constraint_applied:
            print(f"      Constraints applied: {flow_event.get_constraint_summary()}")

        # Update AUM with investor flows
        performance_manager.update_aum(flow_event.net_flow_final)

        print(f"   📊 Final AUM (after flows): ${performance_manager.get_fund_aum():.1f}M")

        # Check for authors reaching 5-year (20 quarter) anniversary
        for author in author_manager.get_all_authors():
            tenure = quarter - author.hire_quarter
            if tenure == 20:  # Exactly 5 years
                lifetime_comp = author.get_lifetime_payments()
                # Only include authors who received compensation (contributed and got paid)
                if lifetime_comp > 0:
                    author_5yr_compensations.append(lifetime_comp)
                    print(f"   🎉 {author.author_id} reached 5-year mark! Lifetime comp: ${lifetime_comp:.2f}M")

        # Calculate quarterly return before fees (as percentage)
        quarterly_return_pct = (performance_result.total_strategy_returns / current_aum) * 100 if current_aum > 0 else 0.0

        # Collect data for plots
        quarters_list.append(quarter)
        cumulative_authors_list.append(len(author_manager.get_all_authors()))  # All authors ever hired
        fund_aum_list.append(performance_manager.get_fund_aum())
        quarterly_flows_list.append(flow_event.net_flow_final)
        quarterly_returns_list.append(quarterly_return_pct)

    # Final statistics
    print("\n📈 Final Fund Statistics")
    print("-" * 60)

    final_aum = performance_manager.get_fund_aum()
    total_strategies = len(strategy_manager.get_all_strategies())
    active_strategies = len(strategy_manager.get_active_strategies())

    print(f"Final AUM: ${final_aum:.1f}M")
    print(f"AUM Growth: {((final_aum / PAP.FUND_INITIAL_AUM) - 1) * 100:+.1f}%")
    print(f"Total Strategies Created: {total_strategies}")
    print(f"Active Strategies: {active_strategies}")

    # Performance allocation statistics
    efficiency_stats = performance_manager.get_allocation_efficiency_stats()
    print(f"Quarters Above High Water Mark: {efficiency_stats['quarters_above_hwm']}/{efficiency_stats['quarters_tracked']}")
    print(f"Average Allocation Efficiency: {efficiency_stats['average_efficiency']:.1%}")
    print(f"Total Profits Distributed to Authors: ${efficiency_stats['total_profits_distributed']:.1f}M")

    # Author compensation statistics
    all_authors = author_manager.get_all_authors()
    total_authors = len(all_authors)
    active_authors = len(author_manager.get_active_authors())

    if total_authors > 0:
        # Calculate lifetime compensation directly from Author objects
        authors_with_payments = [a for a in all_authors if a.get_lifetime_payments() > 0]

        if authors_with_payments:
            lifetime_payments = [a.get_lifetime_payments() for a in authors_with_payments]
            avg_lifetime_comp = sum(lifetime_payments) / len(lifetime_payments)
            min_lifetime_comp = min(lifetime_payments)
            max_lifetime_comp = max(lifetime_payments)
            authors_with_comp = len(authors_with_payments)
        else:
            avg_lifetime_comp = 0.0
            min_lifetime_comp = 0.0
            max_lifetime_comp = 0.0
            authors_with_comp = 0

        print(f"\n👥 Author Statistics:")
        print(f"   Total Authors (including retired): {total_authors}")
        print(f"   Active Authors: {active_authors}")
        print(f"   Authors with Compensation: {authors_with_comp}")
        print(f"   Average Lifetime Compensation: ${avg_lifetime_comp:.2f}M")
        print(f"   Min Lifetime Compensation: ${min_lifetime_comp:.2f}M")
        print(f"   Max Lifetime Compensation: ${max_lifetime_comp:.2f}M")

    # Investor flow statistics
    flow_stats = investor_flow_manager.get_flow_efficiency_stats()
    print(f"\n💵 Investor Flow Statistics:")
    print(f"   Total Quarters Tracked: {flow_stats['total_quarters']}")
    print(f"   Total Net Flows: ${flow_stats['total_net_flows']:+.1f}M")
    print(f"   Average Flow Rate: {flow_stats['avg_flow_pct']:+.2%} of AUM")
    print(f"   Regime Constraints Applied: {flow_stats['regime_constraint_count']}/{flow_stats['total_quarters']} quarters ({flow_stats['regime_constraint_rate']:.1%})")
    print(f"   Magnitude Caps Applied: {flow_stats['magnitude_cap_count']}/{flow_stats['total_quarters']} quarters ({flow_stats['magnitude_cap_rate']:.1%})")

    # Crisis statistics
    crisis_stats = external_shock_manager.get_crisis_statistics()
    print(f"\n⚠️  Crisis Events: {crisis_stats['total_crises']}")
    if crisis_stats['total_crises'] > 0:
        print(f"   Total Crisis Losses: ${crisis_stats['total_losses']:.1f}M")
        print(f"   Average Base Drawdown: {crisis_stats['average_base_drawdown']:.1f}%")
        print(f"   Min/Max Drawdown: {crisis_stats['min_base_drawdown']:.1f}% / {crisis_stats['max_base_drawdown']:.1f}%")

    print("\n🎉 Fund Simulation completed successfully!")
    print("\nKey Features Demonstrated:")
    print(f"✅ Management fee collection ({PAP.MANAGEMENT_FEE_RATE}% quarterly)")
    print("✅ High water mark accounting")
    fund_pct = PAP.get_fund_retention_rate() * 100
    perf_pct = PAP.get_author_performance_rate() * 100
    safety_pct = PAP.PERFORMANCE_ALLOCATION * PAP.AUTHOR_SAFETY_NET_RATIO * 100
    print(f"✅ Three-way profit distribution ({fund_pct:.0f}% fund, {perf_pct:.0f}% performance, {safety_pct:.0f}% safety net)")
    print("✅ Author performance allocation based on strategy ownership")
    print("✅ Safety net program for contributing authors")
    print("✅ Investor flows based on trailing 4Q performance with AUM-based scaling")
    print("✅ External shock modeling with beta-scaled crisis impacts")
    print("✅ Integration across all components")

    # Generate plots
    print("\n📊 Generating plots...")

    plot_filepaths = generate_simulation_plots(
        quarters_list,
        cumulative_authors_list,
        fund_aum_list,
        quarterly_flows_list,
        quarterly_returns_list,
        author_5yr_compensations,
        investment_values,
        author_manager,
        logger.run_dir if logger else "."
    )
    print(f"   Generated {len(plot_filepaths)} plots:")
    for i, filepath in enumerate(plot_filepaths, 1):
        print(f"      Plot {i}: {filepath}")

    if author_5yr_compensations:
        print(f"\n🎉 5-Year Anniversary Statistics:")
        print(f"   Authors who reached 5-year mark: {len(author_5yr_compensations)}")
        print(f"   Mean compensation at 5 years: ${sum(author_5yr_compensations)/len(author_5yr_compensations):.2f}M")
        print(f"   Min/Max: ${min(author_5yr_compensations):.2f}M / ${max(author_5yr_compensations):.2f}M")

    # Investor performance statistics
    print(f"\n💰 $100 Investment Performance:")
    final_investment_value = investment_values[-1]
    total_return_pct = ((final_investment_value - 100) / 100) * 100
    num_years = num_quarters / 4
    annualized_return_pct = ((final_investment_value / 100) ** (1 / num_years) - 1) * 100 if num_years > 0 else 0
    print(f"   Initial investment: $100.00")
    print(f"   Final value: ${final_investment_value:.2f}")
    print(f"   Total return: {total_return_pct:+.1f}%")
    if num_years >= 1:
        print(f"   Annualized return: {annualized_return_pct:+.1f}%")

    # Close logger
    if logger:
        logger.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Hedgedemia Fund Simulation Demo")
    parser.add_argument("--no-logging", action="store_true", help="Disable file logging")
    parser.add_argument("--quarters", type=int, default=5, help="Number of quarters to simulate (default: 5)")
    parser.add_argument("--authors", type=int, default=None, help=f"Initial number of authors (default: {ACP.INITIAL_AUTHOR_COUNT} from parameters)")
    parser.add_argument("--seed", type=int, default=40, help="Random seed for reproducibility (default: 42)")

    args = parser.parse_args()

    run_demo(
        use_logging=not args.no_logging,
        num_quarters=args.quarters,
        initial_authors=args.authors,
        random_seed=args.seed
    )