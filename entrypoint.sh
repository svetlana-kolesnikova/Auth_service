#!/bin/sh
set -e

# ----------------------------
# Wait for PostgreSQL
# ----------------------------
echo "Waiting for PostgreSQL at $POSTGRES_HOST:$POSTGRES_PORT..."
while ! nc -z "$POSTGRES_HOST" "$POSTGRES_PORT"; do
    sleep 0.5
done
echo "PostgreSQL is up"


# ----------------------------
# Wait for Redis
# ----------------------------
if [ "$REDIS_HOST" ]; then
    echo "Waiting for Redis at $REDIS_HOST:$REDIS_PORT..."
    while ! nc -z "$REDIS_HOST" "$REDIS_PORT"; do
        sleep 0.5
    done
    echo "Redis is up"
fi

# ----------------------------
# Apply migrations
# ----------------------------
echo "Applying database migrations..."
python manage.py migrate --noinput

# ----------------------------
# Collect static files
# ----------------------------
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# ----------------------------
# If first argument is 'test' or 'coverage', run it instead of Gunicorn
# ----------------------------
if [ "$1" = "test" ] || [ "$1" = "coverage" ]; then
    exec "$@"
else
    # ----------------------------
    # Start Gunicorn
    # ----------------------------
    echo "Starting Gunicorn..."
    exec gunicorn config.wsgi:application \
        --bind 0.0.0.0:8000 \
        --workers 3 \
        --log-level info
fi