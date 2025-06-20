FROM python:3.11.9-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends build-essential

# Python dependencies
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8004

# Start FastAPI app with uvicorn
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8004