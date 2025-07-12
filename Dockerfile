# Use Python 3.12 slim image for smaller size
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY config/requirements.txt .
COPY config/requirements-dev.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p /app/logs /app/data/cache /app/data/static

# Copy application code
COPY . .

# Create non-root user for security
RUN groupadd -r choynews && useradd -r -g choynews choynews

# Set proper permissions
RUN chown -R choynews:choynews /app && \
    chmod +x /app/bin/choynews

# Switch to non-root user
USER choynews

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from utils.config import Config; Config().validate()" || exit 1

# Expose port (if needed for metrics/monitoring)
EXPOSE 8080

# Default command
CMD ["/app/bin/choynews", "--service", "both"]
