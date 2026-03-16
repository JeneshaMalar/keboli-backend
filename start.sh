#!/bin/sh
echo "Running migrations..."
python -m alembic upgrade head

echo "Starting FastAPI Server..."
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000


wait