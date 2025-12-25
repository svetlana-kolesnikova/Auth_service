# ----------------------------
# Base image
# ----------------------------
FROM python:3.13-slim

# ----------------------------
# Environment
# ----------------------------
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings

# ----------------------------
# System dependencies
# ----------------------------
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ----------------------------
# Poetry
# ----------------------------
ENV POETRY_VERSION=2.1.4
RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"
RUN poetry config virtualenvs.create false

# ----------------------------
# Workdir
# ----------------------------
WORKDIR /app

# ----------------------------
# Install dependencies
# ----------------------------
COPY pyproject.toml poetry.lock* /app/
RUN poetry install --no-interaction --no-ansi

# ----------------------------
# Project files
# ----------------------------
COPY . /app/

# ----------------------------
# Collect static files
# ----------------------------
RUN python manage.py collectstatic --noinput --clear

# ----------------------------
# Entrypoint for migrations + run
# ----------------------------
COPY ./entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]
