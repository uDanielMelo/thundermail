#!/bin/sh
set -e

echo "=== STARTING ==="
echo "PORT: $PORT"
echo "DATABASE_URL: $DATABASE_URL"

echo "=== MIGRATE ==="
python manage.py migrate

echo "=== GUNICORN ==="
exec gunicorn core.wsgi --bind 0.0.0.0:$PORT --timeout 120 --log-level debug