#!/bin/bash
PROJECT_DIR=~/Projects/ColdApproach-AI
cd "$PROJECT_DIR"

source "$PROJECT_DIR/venv/bin/activate"

# Start backend
echo "Starting backend on http://localhost:8000"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Start frontend
echo "Starting frontend on http://localhost:3000"
cd "$PROJECT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!

cd "$PROJECT_DIR"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
echo ""
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "Press Ctrl+C to stop both."
wait
