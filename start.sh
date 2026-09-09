#!/bin/bash
cd "$(dirname "$0")"

echo "Starting AquaTrace backend..."
python3 -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

sleep 2

echo "Starting AquaTrace frontend..."
python3 -m streamlit run app.py

kill $BACKEND_PID 2>/dev/null
