# Dockerfile for FastAPI FileReader Service
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .

# Create non-root user for security
RUN useradd -m -u 1000 fastapi && chown -R fastapi:fastapi /app
USER fastapi

# Expose port (Render will use $PORT)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT:-8000}/docs')" || exit 1

# Run the application
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}

