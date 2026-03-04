#!/bin/bash
PROJECT_DIR=~/Projects/ColdApproach-AI
cd "$PROJECT_DIR"

source "$PROJECT_DIR/venv/bin/activate"

echo "Starting server on http://localhost:8000"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
