#!/bin/bash
# Start script for FinSecure AI Platform

echo "Starting FinSecure AI Platform..."
echo ""

# Backend
echo "Starting Backend..."
cd "$(dirname "$0")/backend"
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "Backend started (PID: $BACKEND_PID)"
echo "Backend URL: http://localhost:8000"
echo ""

# Wait for backend to start
sleep 3

# Frontend
echo "Starting Frontend..."
cd "$(dirname "$0")/frontend"
npm run dev &
FRONTEND_PID=$!
echo "Frontend started (PID: $FRONTEND_PID)"
echo "Frontend URL: http://localhost:5173"
echo ""

echo "✅ Both servers are running!"
echo ""
echo "To stop servers, run:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "Or press Ctrl+C to stop this script"

wait





















