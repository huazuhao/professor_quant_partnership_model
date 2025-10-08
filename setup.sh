#!/bin/bash

# Setup script for Hedgedemia Business Model - Version 2025 September

echo "=========================================="
echo "Setting up Hedgedemia Business Model"
echo "=========================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create dedicated Jupyter kernel
echo "Setting up Jupyter kernel..."
python -m ipykernel install --user --name=hedgedemia_business_model --display-name="Hedgedemia Business Model"

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "To activate the environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "To run tests, use:"
echo "  python tests/test_strategy_lifecycle.py"
echo ""
echo "To run Jupyter notebooks:"
echo "  jupyter notebook --port 6600"
echo ""
echo "  Note: Runs on dedicated port 6600"
echo "  URL: http://localhost:6600/"
echo "  Kernel: Select 'Hedgedemia Business Model' when creating/running notebooks"
echo ""
echo "Component analysis notebooks:"
echo "  • components/author_collaboration/author_lifecycle_analysis.ipynb"
echo ""
echo "Project structure:"
echo "  components/"
echo "    ├── strategy_lifecycle/     # Strategy management"
echo "    ├── author_outcome/         # Author research & contributions"
echo "    ├── capital_allocation/     # Capital deployment"
echo "    ├── performance_allocation/ # Profit distribution"
echo "    ├── external_shock/         # Crisis events"
echo "    ├── investor_flow/          # Capital in/outflows"
echo "    └── author_collaboration/   # Multi-author dynamics"
echo ""