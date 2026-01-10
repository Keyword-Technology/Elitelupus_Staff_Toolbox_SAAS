FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files from backend directory
COPY backend/ .

# Copy version file from root
COPY versions.ini /app/versions.ini

# Set permissions for entrypoint (now in /app/)
RUN chmod +x /app/entrypoint.sh

# Run the application
CMD ["/app/entrypoint.sh"]
