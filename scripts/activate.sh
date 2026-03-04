#!/bin/bash
PROJECT_DIR=~/Projects/ColdApproach-AI
cd "$PROJECT_DIR"

# Create venv if it doesn't exist
if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$PROJECT_DIR/venv"
fi

# Activate venv
source "$PROJECT_DIR/venv/bin/activate"

# Install dependencies
pip install -r "$PROJECT_DIR/requirements.txt" --quiet
echo "Venv activated and dependencies installed."
