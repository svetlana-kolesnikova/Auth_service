# ----------------------------
# Base image
# ----------------------------
FROM python:3.13-slim

# ----------------------------
# Environment variables
# ----------------------------
ENV PYTHONUNBUFFERED=1 \
    POETRY_VERSION=2.1.4 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false

# ----------------------------
# Install system dependencies
# ----------------------------
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    git \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# ----------------------------
# Install Poetry
# ----------------------------
RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

# ----------------------------
# Set working directory
# ----------------------------
WORKDIR /app

# ----------------------------
# Copy project files
# ----------------------------
COPY pyproject.toml poetry.lock* /app/

# ----------------------------
# Install Python dependencies
# ----------------------------
RUN poetry install --no-interaction --no-ansi

# ----------------------------
# Copy project source code
# ----------------------------
COPY . /app/

# ----------------------------
# Create directories for static and media files
# ----------------------------
RUN mkdir -p /app/static /app/media

# ----------------------------
# Make entrypoint executable
# ----------------------------
RUN chmod +x /app/entrypoint.sh

# ----------------------------
# Expose port
# ----------------------------
EXPOSE 8000

# ----------------------------
# Entrypoint
# ----------------------------
ENTRYPOINT ["/app/entrypoint.sh"]
