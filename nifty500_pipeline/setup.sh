#!/bin/bash
# NIFTY 500 Pipeline - Unix/Mac Setup Script
# ===========================================
# This script sets up the Python environment and installs dependencies.

echo "========================================================================"
echo "NIFTY 500 DATA PIPELINE - SETUP"
echo "========================================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed."
    echo ""
    echo "Please install Python 3.8+ from:"
    echo "  - Mac: brew install python3"
    echo "  - Linux: sudo apt install python3 python3-venv python3-pip"
    echo ""
    exit 1
fi

echo "[1/5] Python found:"
python3 --version
echo ""

# Create virtual environment
echo "[2/5] Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists. Skipping creation."
else
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to create virtual environment."
        exit 1
    fi
    echo "Virtual environment created successfully."
fi
echo ""

# Activate virtual environment
echo "[3/5] Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to activate virtual environment."
    exit 1
fi
echo ""

# Upgrade pip
echo "[4/5] Upgrading pip..."
python -m pip install --upgrade pip --quiet
echo "Pip upgraded successfully."
echo ""

# Install dependencies
echo "[5/5] Installing dependencies..."
pip install -r requirements.txt --quiet
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install dependencies."
    exit 1
fi
echo "Dependencies installed successfully."
echo ""

echo "========================================================================"
echo "SETUP COMPLETED SUCCESSFULLY!"
echo "========================================================================"
echo ""
echo "Next steps:"
echo "  1. Activate the virtual environment: source venv/bin/activate"
echo "  2. Run the pipeline: python main.py"
echo "  3. To deactivate virtual environment later: deactivate"
echo ""
echo "For more information, see README.md"
echo "========================================================================"
echo ""
