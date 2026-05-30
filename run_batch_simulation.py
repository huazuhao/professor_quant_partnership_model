#!/usr/bin/env python3
"""
Batch Simulation Runner - Monte Carlo Analysis

Runs multiple simulations (default: 100) to analyze distribution of outcomes:
- Final investment values ($100 initial investment)
- 5-year author compensation distributions
- Final fund AUM values
- Total author counts at end of simulation

All runs use the same base configuration but different random seeds for reproducibility.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Tuple, TextIO
from datetime import datetime

from run_single_simulation import run_simulation_core


class TeeOutput:
    """
    Simple tee-style output that writes to both console and file simultaneously.
    """

    def __init__(self, console: TextIO, file: TextIO):
        self.console = console
        self.file = file

    def write(self, message: str):
        """Write message to both console and file."""
        self.console.write(message)
        self.file.write(message)
        self.console.flush()
        self.file.flush()

    def flush(self):
        """Flush both streams."""
        self.console.flush()
        self.file.flush()

    def isatty(self):
        """Return console's tty status."""
        return self.console.isatty()


def run_batch_simulations(num_runs: int = 100, num_quarters: int = 40, base_seed: int = 42):
    """
    Run multiple simulations and aggregate results.

    Args:
        num_runs: Number of simulation runs (default: 100)
        num_quarters: Quarters per simulation (default: 40 = 10 years)
        base_seed: Base random seed for reproducibility

    Returns:
        Tuple of (final_investment_values, all_5yr_compensations, final_aums, total_authors_list, paid_authors_list)
    """
    print(f"🚀 Starting Batch Simulation")
    print(f"=" * 70)
    print(f"Configuration:")
    print(f"  Number of runs: {num_runs}")
    print(f"  Quarters per run: {num_quarters} ({num_quarters/4:.1f} years)")
    print(f"  Base seed: {base_seed}")
    print(f"\n{'='*70}\n")

    final_investment_values = []
    all_5yr_compensations = []
    final_aums = []
    total_authors_list = []
    paid_authors_list = []

    for run_idx in range(num_runs):
        # Each run gets unique but reproducible seed
        run_seed = base_seed + run_idx

        # Run single simulation silently
        result = run_simulation_core(
            num_quarters=num_quarters,
            random_seed=run_seed,
            silent=True  # No console output per run
        )

        # Collect results
        final_investment_values.append(result['final_investment_value'])
        all_5yr_compensations.extend(result['author_5yr_compensations'])
        final_aums.append(result['final_aum'])
        total_authors_list.append(result['total_authors'])
        paid_authors_list.append(result['paid_authors'])

        # Progress indicator
        if (run_idx + 1) % 10 == 0:
            print(f"✓ Completed {run_idx + 1}/{num_runs} simulations...")

    print(f"\n{'='*70}")
    print(f"✅ All {num_runs} simulations completed!\n")

    return final_investment_values, all_5yr_compensations, final_aums, total_authors_list, paid_authors_list


def generate_batch_plots(final_investment_values: List[float], all_5yr_compensations: List[float],
                         final_aums: List[float], total_authors_list: List[int], paid_authors_list: List[int],
                         output_dir: str = "."):
    """
    Generate histogram plots from batch simulation results.

    Args:
        final_investment_values: List of final $100 investment values
        all_5yr_compensations: List of all 5-year compensation values
        final_aums: List of final fund AUM values
        total_authors_list: List of total author counts per simulation
        paid_authors_list: List of paid author counts per simulation
        output_dir: Directory to save plots
    """
    import os

    plot_paths = []

    # Plot 1: Investment Value Distribution
    fig1, ax1 = plt.subplots(figsize=(12, 7))

    n, bins, patches = ax1.hist(final_investment_values, bins=30, color='#3498db',
                                 alpha=0.7, edgecolor='black', linewidth=0.8)

    # Color bars based on gain/loss
    for i, patch in enumerate(patches):
        if bins[i] < 100:
            patch.set_facecolor('#e74c3c')  # Red for loss
        else:
            patch.set_facecolor('#27ae60')  # Green for gain

    # Statistics
    mean_val = np.mean(final_investment_values)
    median_val = np.median(final_investment_values)
    std_val = np.std(final_investment_values)
    p10 = np.percentile(final_investment_values, 10)
    p25 = np.percentile(final_investment_values, 25)
    p75 = np.percentile(final_investment_values, 75)
    p90 = np.percentile(final_investment_values, 90)

    # Add reference lines
    ax1.axvline(x=100, color='black', linestyle=':', linewidth=2,
                label='Break-even ($100)', alpha=0.7)
    ax1.axvline(x=mean_val, color='red', linestyle='--', linewidth=2,
                label=f'Mean: ${mean_val:.2f}')
    ax1.axvline(x=median_val, color='orange', linestyle='--', linewidth=2,
                label=f'Median: ${median_val:.2f}')

    # Statistics box
    stats_text = f'Statistics (n={len(final_investment_values)}):\n'
    stats_text += f'Mean: ${mean_val:.2f}\n'
    stats_text += f'Median: ${median_val:.2f}\n'
    stats_text += f'Std Dev: ${std_val:.2f}\n'
    stats_text += f'Min/Max: ${min(final_investment_values):.2f} / ${max(final_investment_values):.2f}\n'
    stats_text += f'\nPercentiles:\n'
    stats_text += f'10th: ${p10:.2f}\n'
    stats_text += f'25th: ${p25:.2f}\n'
    stats_text += f'75th: ${p75:.2f}\n'
    stats_text += f'90th: ${p90:.2f}'

    ax1.text(0.98, 0.98, stats_text, transform=ax1.transAxes,
             fontsize=10, verticalalignment='top', horizontalalignment='right',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9))

    ax1.set_xlabel('Final Investment Value ($)', fontsize=12)
    ax1.set_ylabel('Number of Simulations', fontsize=12)
    ax1.set_title(f'Distribution of Final $100 Investment Values\n({len(final_investment_values)} simulations, 40 quarters each)',
                  fontsize=14, fontweight='bold')
    ax1.legend(fontsize=11, loc='upper left')
    ax1.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plot1_path = os.path.join(output_dir, 'batch_plot1_investment_value_distribution.png')
    plt.savefig(plot1_path, dpi=300, bbox_inches='tight')
    plt.close()
    plot_paths.append(plot1_path)

    # Plot 2: 5-Year Compensation Distribution
    fig2, ax2 = plt.subplots(figsize=(12, 7))

    if all_5yr_compensations:
        ax2.hist(all_5yr_compensations, bins=40, color='#9b59b6', alpha=0.7,
                 edgecolor='black', linewidth=0.8)

        # Statistics
        mean_comp = np.mean(all_5yr_compensations)
        median_comp = np.median(all_5yr_compensations)
        std_comp = np.std(all_5yr_compensations)
        p10_comp = np.percentile(all_5yr_compensations, 10)
        p25_comp = np.percentile(all_5yr_compensations, 25)
        p75_comp = np.percentile(all_5yr_compensations, 75)
        p90_comp = np.percentile(all_5yr_compensations, 90)

        # Add reference lines
        ax2.axvline(x=mean_comp, color='red', linestyle='--', linewidth=2,
                    label=f'Mean: ${mean_comp:.2f}M')
        ax2.axvline(x=median_comp, color='orange', linestyle='--', linewidth=2,
                    label=f'Median: ${median_comp:.2f}M')

        # Statistics box
        stats_text = f'Statistics (n={len(all_5yr_compensations)}):\n'
        stats_text += f'Mean: ${mean_comp:.2f}M\n'
        stats_text += f'Median: ${median_comp:.2f}M\n'
        stats_text += f'Std Dev: ${std_comp:.2f}M\n'
        stats_text += f'Min/Max: ${min(all_5yr_compensations):.2f}M / ${max(all_5yr_compensations):.2f}M\n'
        stats_text += f'\nPercentiles:\n'
        stats_text += f'10th: ${p10_comp:.2f}M\n'
        stats_text += f'25th: ${p25_comp:.2f}M\n'
        stats_text += f'75th: ${p75_comp:.2f}M\n'
        stats_text += f'90th: ${p90_comp:.2f}M'

        ax2.text(0.98, 0.98, stats_text, transform=ax2.transAxes,
                 fontsize=10, verticalalignment='top', horizontalalignment='right',
                 bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9))

        ax2.set_xlabel('Lifetime Compensation at 5-Year Mark ($M)', fontsize=12)
        ax2.set_ylabel('Number of Authors', fontsize=12)
        ax2.set_title(f'Distribution of 5-Year Author Compensations\n({len(all_5yr_compensations)} authors across all simulations)',
                      fontsize=14, fontweight='bold')
        ax2.legend(fontsize=11, loc='upper left')
        ax2.grid(True, alpha=0.3, axis='y')
    else:
        ax2.text(0.5, 0.5, 'No 5-year compensation data', ha='center', va='center',
                 transform=ax2.transAxes, fontsize=12)
        ax2.set_title('Distribution of 5-Year Author Compensations', fontsize=14, fontweight='bold')

    plt.tight_layout()
    plot2_path = os.path.join(output_dir, 'batch_plot2_5year_compensation_distribution.png')
    plt.savefig(plot2_path, dpi=300, bbox_inches='tight')
    plt.close()
    plot_paths.append(plot2_path)

    # Plot 3: Final Fund AUM Distribution
    fig3, ax3 = plt.subplots(figsize=(12, 7))

    ax3.hist(final_aums, bins=30, color='#f39c12', alpha=0.7, edgecolor='black', linewidth=0.8)

    # Statistics
    mean_aum = np.mean(final_aums)
    median_aum = np.median(final_aums)
    std_aum = np.std(final_aums)
    p10_aum = np.percentile(final_aums, 10)
    p25_aum = np.percentile(final_aums, 25)
    p75_aum = np.percentile(final_aums, 75)
    p90_aum = np.percentile(final_aums, 90)

    # Add reference lines
    ax3.axvline(x=mean_aum, color='red', linestyle='--', linewidth=2,
                label=f'Mean: ${mean_aum:.1f}M')
    ax3.axvline(x=median_aum, color='orange', linestyle='--', linewidth=2,
                label=f'Median: ${median_aum:.1f}M')

    # Statistics box
    stats_text = f'Statistics (n={len(final_aums)}):\n'
    stats_text += f'Mean: ${mean_aum:.1f}M\n'
    stats_text += f'Median: ${median_aum:.1f}M\n'
    stats_text += f'Std Dev: ${std_aum:.1f}M\n'
    stats_text += f'Min/Max: ${min(final_aums):.1f}M / ${max(final_aums):.1f}M\n'
    stats_text += f'\nPercentiles:\n'
    stats_text += f'10th: ${p10_aum:.1f}M\n'
    stats_text += f'25th: ${p25_aum:.1f}M\n'
    stats_text += f'75th: ${p75_aum:.1f}M\n'
    stats_text += f'90th: ${p90_aum:.1f}M'

    ax3.text(0.98, 0.98, stats_text, transform=ax3.transAxes,
             fontsize=10, verticalalignment='top', horizontalalignment='right',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9))

    ax3.set_xlabel('Final Fund AUM ($M)', fontsize=12)
    ax3.set_ylabel('Number of Simulations', fontsize=12)
    ax3.set_title(f'Distribution of Final Fund AUM\n({len(final_aums)} simulations, 40 quarters each)',
                  fontsize=14, fontweight='bold')
    ax3.legend(fontsize=11, loc='upper left')
    ax3.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plot3_path = os.path.join(output_dir, 'batch_plot3_final_aum_distribution.png')
    plt.savefig(plot3_path, dpi=300, bbox_inches='tight')
    plt.close()
    plot_paths.append(plot3_path)

    # Plot 4: Total Author Count Distribution
    fig4, ax4 = plt.subplots(figsize=(12, 7))

    # Use integer bins for count data
    max_authors = max(total_authors_list) if total_authors_list else 0
    min_authors = min(total_authors_list) if total_authors_list else 0
    bins = range(min_authors, max_authors + 2)  # +2 to include the max value

    ax4.hist(total_authors_list, bins=bins, color='#e67e22', alpha=0.7,
             edgecolor='black', linewidth=0.8, align='left')

    # Statistics
    mean_authors = np.mean(total_authors_list)
    median_authors = np.median(total_authors_list)
    std_authors = np.std(total_authors_list)
    p10_authors = np.percentile(total_authors_list, 10)
    p25_authors = np.percentile(total_authors_list, 25)
    p75_authors = np.percentile(total_authors_list, 75)
    p90_authors = np.percentile(total_authors_list, 90)

    # Add reference lines
    ax4.axvline(x=mean_authors, color='red', linestyle='--', linewidth=2,
                label=f'Mean: {mean_authors:.1f}')
    ax4.axvline(x=median_authors, color='orange', linestyle='--', linewidth=2,
                label=f'Median: {median_authors:.1f}')

    # Statistics box
    stats_text = f'Statistics (n={len(total_authors_list)}):\n'
    stats_text += f'Mean: {mean_authors:.1f}\n'
    stats_text += f'Median: {median_authors:.1f}\n'
    stats_text += f'Std Dev: {std_authors:.1f}\n'
    stats_text += f'Min/Max: {min(total_authors_list)} / {max(total_authors_list)}\n'
    stats_text += f'\nPercentiles:\n'
    stats_text += f'10th: {p10_authors:.1f}\n'
    stats_text += f'25th: {p25_authors:.1f}\n'
    stats_text += f'75th: {p75_authors:.1f}\n'
    stats_text += f'90th: {p90_authors:.1f}'

    ax4.text(0.98, 0.98, stats_text, transform=ax4.transAxes,
             fontsize=10, verticalalignment='top', horizontalalignment='right',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9))

    ax4.set_xlabel('Total Authors at End of Simulation', fontsize=12)
    ax4.set_ylabel('Number of Simulations', fontsize=12)
    ax4.set_title(f'Distribution of Total Author Counts\n({len(total_authors_list)} simulations)',
                  fontsize=14, fontweight='bold')
    ax4.legend(fontsize=11, loc='upper left')
    ax4.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plot4_path = os.path.join(output_dir, 'batch_plot4_total_author_count_distribution.png')
    plt.savefig(plot4_path, dpi=300, bbox_inches='tight')
    plt.close()
    plot_paths.append(plot4_path)

    # Plot 5: Professor/lab funding count distribution
    fig5, ax5 = plt.subplots(figsize=(12, 7))

    # Use integer bins for count data
    max_paid_authors = max(paid_authors_list) if paid_authors_list else 0
    min_paid_authors = min(paid_authors_list) if paid_authors_list else 0
    bins_paid = range(min_paid_authors, max_paid_authors + 2)  # +2 to include the max value

    ax5.hist(paid_authors_list, bins=bins_paid, color='#16a085', alpha=0.7,
             edgecolor='black', linewidth=0.8, align='left')

    # Statistics
    mean_paid_authors = np.mean(paid_authors_list)
    median_paid_authors = np.median(paid_authors_list)
    std_paid_authors = np.std(paid_authors_list)
    p10_paid_authors = np.percentile(paid_authors_list, 10)
    p25_paid_authors = np.percentile(paid_authors_list, 25)
    p75_paid_authors = np.percentile(paid_authors_list, 75)
    p90_paid_authors = np.percentile(paid_authors_list, 90)

    # Add reference lines
    ax5.axvline(x=mean_paid_authors, color='red', linestyle='--', linewidth=2,
                label=f'Mean: {mean_paid_authors:.1f}')
    ax5.axvline(x=median_paid_authors, color='orange', linestyle='--', linewidth=2,
                label=f'Median: {median_paid_authors:.1f}')

    # Statistics box
    stats_text_paid = f'Statistics (n={len(paid_authors_list)}):\n'
    stats_text_paid += f'Mean: {mean_paid_authors:.1f}\n'
    stats_text_paid += f'Median: {median_paid_authors:.1f}\n'
    stats_text_paid += f'Std Dev: {std_paid_authors:.1f}\n'
    stats_text_paid += f'Min/Max: {min(paid_authors_list)} / {max(paid_authors_list)}\n'
    stats_text_paid += f'\nPercentiles:\n'
    stats_text_paid += f'10th: {p10_paid_authors:.1f}\n'
    stats_text_paid += f'25th: {p25_paid_authors:.1f}\n'
    stats_text_paid += f'75th: {p75_paid_authors:.1f}\n'
    stats_text_paid += f'90th: {p90_paid_authors:.1f}'

    ax5.text(0.98, 0.98, stats_text_paid, transform=ax5.transAxes,
             fontsize=10, verticalalignment='top', horizontalalignment='right',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9))

    ax5.set_xlabel('Professor/Lab Groups Receiving Funding at End of Simulation', fontsize=12)
    ax5.set_ylabel('Number of Simulations', fontsize=12)
    ax5.set_title(f'Distribution of Professor/Lab Groups Receiving Funding\n({len(paid_authors_list)} simulations)',
                  fontsize=14, fontweight='bold')
    ax5.legend(fontsize=11, loc='upper left')
    ax5.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plot5_path = os.path.join(output_dir, 'batch_plot5_paid_author_count_distribution.png')
    plt.savefig(plot5_path, dpi=300, bbox_inches='tight')
    plt.close()
    plot_paths.append(plot5_path)

    return plot_paths


def print_statistics(final_investment_values: List[float], all_5yr_compensations: List[float],
                     final_aums: List[float], total_authors_list: List[int], paid_authors_list: List[int],
                     num_runs: int):
    """
    Print summary statistics from batch simulation.

    Args:
        final_investment_values: List of final investment values
        all_5yr_compensations: List of 5-year compensations
        final_aums: List of final fund AUM values
        total_authors_list: List of total author counts per simulation
        paid_authors_list: List of paid author counts per simulation
        num_runs: Number of simulation runs
    """
    print(f"📊 Batch Simulation Results")
    print(f"=" * 70)

    # Investment value statistics
    print(f"\n💰 Investment Value Distribution ($100 initial investment):")
    print(f"   Simulations: {len(final_investment_values)}")
    print(f"   Mean: ${np.mean(final_investment_values):.2f}")
    print(f"   Median: ${np.median(final_investment_values):.2f}")
    print(f"   Std Dev: ${np.std(final_investment_values):.2f}")
    print(f"   Min/Max: ${min(final_investment_values):.2f} / ${max(final_investment_values):.2f}")

    print(f"\n   Percentiles:")
    print(f"     10th: ${np.percentile(final_investment_values, 10):.2f}")
    print(f"     25th: ${np.percentile(final_investment_values, 25):.2f}")
    print(f"     50th: ${np.percentile(final_investment_values, 50):.2f}")
    print(f"     75th: ${np.percentile(final_investment_values, 75):.2f}")
    print(f"     90th: ${np.percentile(final_investment_values, 90):.2f}")

    # Calculate total returns
    mean_return = ((np.mean(final_investment_values) - 100) / 100) * 100
    median_return = ((np.median(final_investment_values) - 100) / 100) * 100
    print(f"\n   Returns:")
    print(f"     Mean total return: {mean_return:+.1f}%")
    print(f"     Median total return: {median_return:+.1f}%")

    # Final AUM statistics
    print(f"\n💼 Final Fund AUM Distribution:")
    print(f"   Simulations: {len(final_aums)}")
    print(f"   Mean: ${np.mean(final_aums):.1f}M")
    print(f"   Median: ${np.median(final_aums):.1f}M")
    print(f"   Std Dev: ${np.std(final_aums):.1f}M")
    print(f"   Min/Max: ${min(final_aums):.1f}M / ${max(final_aums):.1f}M")

    print(f"\n   Percentiles:")
    print(f"     10th: ${np.percentile(final_aums, 10):.1f}M")
    print(f"     25th: ${np.percentile(final_aums, 25):.1f}M")
    print(f"     50th: ${np.percentile(final_aums, 50):.1f}M")
    print(f"     75th: ${np.percentile(final_aums, 75):.1f}M")
    print(f"     90th: ${np.percentile(final_aums, 90):.1f}M")

    # 5-year compensation statistics
    if all_5yr_compensations:
        print(f"\n👥 5-Year Author Compensation Distribution:")
        print(f"   Total authors at 5-year mark: {len(all_5yr_compensations)} (across {num_runs} simulations)")
        print(f"   Avg authors per simulation: {len(all_5yr_compensations)/num_runs:.1f}")
        print(f"   Mean compensation: ${np.mean(all_5yr_compensations):.2f}M")
        print(f"   Median compensation: ${np.median(all_5yr_compensations):.2f}M")
        print(f"   Std Dev: ${np.std(all_5yr_compensations):.2f}M")
        print(f"   Min/Max: ${min(all_5yr_compensations):.2f}M / ${max(all_5yr_compensations):.2f}M")

        print(f"\n   Percentiles:")
        print(f"     10th: ${np.percentile(all_5yr_compensations, 10):.2f}M")
        print(f"     25th: ${np.percentile(all_5yr_compensations, 25):.2f}M")
        print(f"     50th: ${np.percentile(all_5yr_compensations, 50):.2f}M")
        print(f"     75th: ${np.percentile(all_5yr_compensations, 75):.2f}M")
        print(f"     90th: ${np.percentile(all_5yr_compensations, 90):.2f}M")
    else:
        print(f"\n👥 5-Year Author Compensation Distribution:")
        print(f"   No authors reached 5-year mark in any simulation")

    # Total author count statistics
    print(f"\n🎓 Total Author Count Distribution:")
    print(f"   Simulations: {len(total_authors_list)}")
    print(f"   Mean: {np.mean(total_authors_list):.1f}")
    print(f"   Median: {np.median(total_authors_list):.1f}")
    print(f"   Std Dev: {np.std(total_authors_list):.1f}")
    print(f"   Min/Max: {min(total_authors_list)} / {max(total_authors_list)}")

    print(f"\n   Percentiles:")
    print(f"     10th: {np.percentile(total_authors_list, 10):.1f}")
    print(f"     25th: {np.percentile(total_authors_list, 25):.1f}")
    print(f"     50th: {np.percentile(total_authors_list, 50):.1f}")
    print(f"     75th: {np.percentile(total_authors_list, 75):.1f}")
    print(f"     90th: {np.percentile(total_authors_list, 90):.1f}")

    # Paid author count statistics
    print(f"\n💰 Paid Author Count Distribution (Authors Who Received Compensation):")
    print(f"   Simulations: {len(paid_authors_list)}")
    print(f"   Mean: {np.mean(paid_authors_list):.1f}")
    print(f"   Median: {np.median(paid_authors_list):.1f}")
    print(f"   Std Dev: {np.std(paid_authors_list):.1f}")
    print(f"   Min/Max: {min(paid_authors_list)} / {max(paid_authors_list)}")

    print(f"\n   Percentiles:")
    print(f"     10th: {np.percentile(paid_authors_list, 10):.1f}")
    print(f"     25th: {np.percentile(paid_authors_list, 25):.1f}")
    print(f"     50th: {np.percentile(paid_authors_list, 50):.1f}")
    print(f"     75th: {np.percentile(paid_authors_list, 75):.1f}")
    print(f"     90th: {np.percentile(paid_authors_list, 90):.1f}")

    # Payment rate statistics
    mean_total = np.mean(total_authors_list)
    mean_paid = np.mean(paid_authors_list)
    payment_rate = (mean_paid / mean_total * 100) if mean_total > 0 else 0
    print(f"\n   Payment Rate: {payment_rate:.1f}% of authors received compensation")


def main(num_runs: int = 100, num_quarters: int = 40, base_seed: int = 42):
    """
    Main entry point for batch simulation.

    Args:
        num_runs: Number of simulations to run
        num_quarters: Quarters per simulation
        base_seed: Base random seed
    """
    # Create timestamped log file in current directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"batch_simulation_{timestamp}.log"
    log_file = open(log_filename, 'w', encoding='utf-8')

    # Save original stdout
    original_stdout = sys.stdout

    # Redirect stdout to tee (both console and file)
    tee = TeeOutput(original_stdout, log_file)
    sys.stdout = tee

    try:
        # Run batch simulations
        final_investment_values, all_5yr_compensations, final_aums, total_authors_list, paid_authors_list = run_batch_simulations(
            num_runs=num_runs,
            num_quarters=num_quarters,
            base_seed=base_seed
        )

        # Print statistics
        print_statistics(final_investment_values, all_5yr_compensations, final_aums, total_authors_list, paid_authors_list, num_runs)

        # Generate plots
        print(f"\n📈 Generating plots...")
        plot_paths = generate_batch_plots(final_investment_values, all_5yr_compensations, final_aums, total_authors_list, paid_authors_list)

        print(f"\n✅ Generated {len(plot_paths)} plots:")
        for i, path in enumerate(plot_paths, 1):
            print(f"   Plot {i}: {path}")

        print(f"\n🎉 Batch simulation analysis complete!")

    finally:
        # Restore stdout and close log file
        sys.stdout = original_stdout
        log_file.close()

        # Print log file location (to console only, after restoring stdout)
        print(f"\n📄 Console output saved to: {log_filename}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Batch Hedgedemia Fund Simulation (Monte Carlo)")
    parser.add_argument("--runs", type=int, default=100, help="Number of simulation runs (default: 100)")
    parser.add_argument("--quarters", type=int, default=40, help="Quarters per simulation (default: 40 = 10 years)")
    parser.add_argument("--seed", type=int, default=42, help="Base random seed for reproducibility (default: 42)")

    args = parser.parse_args()

    main(
        num_runs=args.runs,
        num_quarters=args.quarters,
        base_seed=args.seed
    )
