#!/bin/bash
# Start the ThaiLawOnline Chatbot backend
set -e

# Trap signals for graceful shutdown
trap 'kill $(jobs -p) 2>/dev/null; exit 0' SIGINT SIGTERM

echo "Starting ThaiLawOnline Chatbot API on port 8001..."
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001 --workers 2 &

wait
