# ==============================================================================
# Dockerfile for AI Startup Co-Founder Team Backend (FastAPI API & Worker)
# ==============================================================================

FROM python:3.11-slim

# Prevent Python from writing .pyc files & enable unbuffered stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install system dependencies (including Cairo/Pango for PDF/WeasyPrint rendering)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# Copy application source code
COPY backend /app/backend
COPY prompts /app/prompts
COPY evals /app/evals
COPY alembic.ini /app/alembic.ini

# Create exports directory
RUN mkdir -p /app/exports

EXPOSE 8000

# Default command runs database migrations then starts FastAPI server
CMD ["sh", "-c", "alembic -c /app/alembic.ini upgrade head && uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"]
