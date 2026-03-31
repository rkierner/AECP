FROM python:3.11-slim

WORKDIR /app

# Upgrade pip/setuptools first — python:3.11-slim ships with an older pip
# that can't resolve pyproject.toml builds reliably
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install dependencies first for better layer caching
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy application code
COPY app/ ./app/
COPY policies/ ./policies/

EXPOSE 8080

# Run with a single worker for simplicity; scale horizontally in production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
