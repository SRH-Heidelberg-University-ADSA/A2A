#!/bin/bash

# Cloud Run usually provides a PORT environment variable (defaults to 8080)
API_PORT=${PORT:-8080}

echo "🌾 Starting Krishi-Intel A2A Backend (FastAPI) on port $API_PORT..."

# 'exec' replaces the shell with the uvicorn process, which is best practice for Docker
exec uvicorn Fast_api:app --host 0.0.0.0 --port $API_PORT