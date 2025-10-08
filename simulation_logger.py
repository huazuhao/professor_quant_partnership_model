"""
Simulation Logger for Hedgedemia Fund Simulation

Provides comprehensive logging infrastructure with:
- Timestamped run folders
- Console + file logging with tee functionality
- Parameter snapshot at simulation start
- Structured output organization
- Easy extension for future components (External Shock, etc.)
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, TextIO
import logging


class SimulationLogger:
    """
    Main logger for fund simulation runs.

    Creates timestamped run folders with:
    - simulation.log: Complete execution log
    - parameters.txt: All simulation parameters
    - (future) charts, CSVs, etc.
    """

    def __init__(self, base_log_dir: str = "simulation_runs", run_name: Optional[str] = None):
        """
        Initialize simulation logger.

        Args:
            base_log_dir: Base directory for all simulation runs
            run_name: Optional custom run name (defaults to timestamp)
        """
        self.base_log_dir = Path(base_log_dir)
        self.base_log_dir.mkdir(exist_ok=True)

        # Create timestamped run folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if run_name:
            folder_name = f"{run_name}_{timestamp}"
        else:
            folder_name = f"run_{timestamp}"

        self.run_dir = self.base_log_dir / folder_name
        self.run_dir.mkdir(exist_ok=True)

        # Setup log files
        self.log_file_path = self.run_dir / "simulation.log"
        self.param_file_path = self.run_dir / "parameters.txt"

        # Open log file
        self.log_file = open(self.log_file_path, 'w', encoding='utf-8')

        # Store original stdout/stderr for restoration
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

        # Create tee wrapper for simultaneous console + file output
        self.tee_stdout = TeeOutput(sys.stdout, self.log_file)

        # Setup Python logging
        self._setup_python_logging()

        # Track if currently redirected
        self.is_redirected = False

    def _setup_python_logging(self):
        """Setup Python logging module for library integration."""
        self.logger = logging.getLogger('hedgedemia_simulation')
        self.logger.setLevel(logging.INFO)

        # File handler
        file_handler = logging.FileHandler(self.log_file_path)
        file_handler.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def start_logging(self):
        """Start redirecting print statements to both console and file."""
        if not self.is_redirected:
            sys.stdout = self.tee_stdout
            self.is_redirected = True

    def stop_logging(self):
        """Stop redirection and restore original stdout."""
        if self.is_redirected:
            sys.stdout = self.original_stdout
            self.is_redirected = False

    def log_parameters(self, param_dict: dict):
        """
        Log all simulation parameters to parameters.txt.

        Args:
            param_dict: Dictionary of all parameters used in simulation
        """
        with open(self.param_file_path, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("HEDGEDEMIA FUND SIMULATION PARAMETERS\n")
            f.write(f"Run Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Run Directory: {self.run_dir}\n")
            f.write("=" * 70 + "\n\n")

            # Group parameters by component
            component_params = {
                'Author Collaboration': [],
                'Strategy Lifecycle': [],
                'Capital Allocation': [],
                'Performance Allocation': [],
                'Investor Flow': [],
                'Simulation Control': [],
                'Other': []
            }

            # Categorize parameters
            for key, value in param_dict.items():
                if 'AUTHOR' in key or 'GROUP' in key or 'INVENTION' in key or 'IMPROVEMENT' in key:
                    component_params['Author Collaboration'].append((key, value))
                elif 'STRATEGY' in key:
                    component_params['Strategy Lifecycle'].append((key, value))
                elif 'CAPITAL' in key or 'ALLOCATION' in key:
                    component_params['Capital Allocation'].append((key, value))
                elif 'PERFORMANCE' in key or 'MANAGEMENT_FEE' in key or 'SAFETY_NET' in key:
                    component_params['Performance Allocation'].append((key, value))
                elif 'FLOW' in key or 'INVESTOR' in key:
                    component_params['Investor Flow'].append((key, value))
                elif 'QUARTERS' in key or 'INITIAL' in key or 'SEED' in key:
                    component_params['Simulation Control'].append((key, value))
                else:
                    component_params['Other'].append((key, value))

            # Write parameters by component
            for component, params in component_params.items():
                if params:  # Only write if component has parameters
                    f.write(f"\n{'─' * 70}\n")
                    f.write(f"{component.upper()}\n")
                    f.write(f"{'─' * 70}\n\n")

                    # Find longest key for alignment
                    max_key_len = max(len(k) for k, v in params)

                    for key, value in sorted(params):
                        f.write(f"  {key:<{max_key_len}} = {value}\n")

            f.write(f"\n{'=' * 70}\n")
            f.write(f"Total parameters logged: {len(param_dict)}\n")
            f.write(f"{'=' * 70}\n")

    def get_run_directory(self) -> Path:
        """Get the current run directory path."""
        return self.run_dir

    def close(self):
        """Close log file and restore stdout."""
        self.stop_logging()
        if self.log_file and not self.log_file.closed:
            self.log_file.close()

        print(f"\n📁 Simulation logs saved to: {self.run_dir}")
        print(f"   • Execution log: {self.log_file_path.name}")
        print(f"   • Parameters: {self.param_file_path.name}")

    def __enter__(self):
        """Context manager entry."""
        self.start_logging()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class TeeOutput:
    """
    Tee-style output that writes to both console and file simultaneously.
    """

    def __init__(self, console: TextIO, file: TextIO):
        """
        Initialize tee output.

        Args:
            console: Console output stream (usually sys.stdout)
            file: File output stream
        """
        self.console = console
        self.file = file

    def write(self, message: str):
        """Write message to both console and file."""
        self.console.write(message)
        self.file.write(message)
        # Flush both to ensure immediate output
        self.console.flush()
        self.file.flush()

    def flush(self):
        """Flush both streams."""
        self.console.flush()
        self.file.flush()

    def isatty(self):
        """Return console's tty status."""
        return self.console.isatty()


def collect_all_parameters() -> dict:
    """
    Collect all simulation parameters from all components.

    Returns:
        Dictionary with all parameters
    """
    params = {}

    # Import all parameter classes
    try:
        from components.author_collaboration import AuthorCollaborationParameters as ACP
        from components.strategy_lifecycle import StrategyParameters as SP
        from components.performance_allocation import PerformanceAllocationParameters as PAP
        from components.investor_flow import InvestorFlowParameters as IFP
        from components.external_shock import ExternalShockParameters as ESP

        # Author Collaboration Parameters
        for attr in dir(ACP):
            if attr.isupper() and not attr.startswith('_'):
                params[f"ACP.{attr}"] = getattr(ACP, attr)

        # Strategy Lifecycle Parameters
        for attr in dir(SP):
            if attr.isupper() and not attr.startswith('_'):
                params[f"SP.{attr}"] = getattr(SP, attr)

        # Performance Allocation Parameters
        for attr in dir(PAP):
            if attr.isupper() and not attr.startswith('_'):
                params[f"PAP.{attr}"] = getattr(PAP, attr)

        # Investor Flow Parameters
        for attr in dir(IFP):
            if attr.isupper() and not attr.startswith('_'):
                params[f"IFP.{attr}"] = getattr(IFP, attr)

        # External Shock Parameters
        for attr in dir(ESP):
            if attr.isupper() and not attr.startswith('_'):
                params[f"ESP.{attr}"] = getattr(ESP, attr)

    except ImportError as e:
        print(f"⚠️  Warning: Could not import all parameter modules: {e}")

    return params


if __name__ == "__main__":
    # Test the logger
    print("Testing SimulationLogger...")

    with SimulationLogger(run_name="test") as logger:
        # Collect and log parameters
        params = collect_all_parameters()
        logger.log_parameters(params)

        # Test output
        print("=" * 60)
        print("This output goes to both console AND log file!")
        print("=" * 60)
        print("Testing multi-line output:")
        print("  Line 1")
        print("  Line 2")
        print("  Line 3")

    print("\n✅ Logger test complete!")
