#!/bin/bash

# Start FastAPI backend in background
uvicorn main:app --host 0.0.0.0 --port 8000 &

# Start Chainlit on port 8001
chainlit run chainlit_app/app.py --host 0.0.0.0 --port 8001
