#!/bin/sh

# ----------------------------
# Wait for DB to be ready
# ----------------------------
if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."
    while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
      sleep 0.5
    done
    echo "Postgres started"
fi

# ----------------------------
# Run migrations
# ----------------------------
echo "Apply database migrations"
python manage.py migrate

# ----------------------------
# Collect static (optional)
# ----------------------------
echo "Collect static files"
python manage.py collectstatic --noinput --clear

# ----------------------------
# Start Gunicorn
# ----------------------------
echo "Starting server"
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
