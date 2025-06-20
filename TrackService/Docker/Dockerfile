FROM python:3.11.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
# The EXPOSE instruction documents the port, but it must be published when running the container (e.g., `docker run -p 8003:8003`).
EXPOSE 8003

# Start FastAPI app with uvicorn
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8003