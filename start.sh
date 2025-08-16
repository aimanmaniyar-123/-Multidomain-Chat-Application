#!/bin/bash
# Start FastAPI backend in background
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &

# Wait for backend to start
sleep 10

# Start Chainlit on Render's assigned port
chainlit run chainlit/app.py --host 0.0.0.0 --port $PORT
