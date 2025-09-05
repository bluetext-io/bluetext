FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --disable-pip-version-check -r requirements.txt

# Copy application source code
COPY src/ ./src/
COPY bin/ ./bin/

# Make run script executable
RUN chmod +x bin/run

# Create cache directory
RUN mkdir -p /root/.cache

# Set environment variables
ENV PYTHONPATH=/app/src
ENV ROOT=/app

# Expose any ports if needed (adjust as necessary)
# EXPOSE 8080

# Default command
CMD ["bin/run"]
