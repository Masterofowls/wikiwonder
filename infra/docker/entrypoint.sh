#!/bin/bash
set -e

echo "Running migrations..."
/app/.venv/bin/python manage.py migrate --noinput

echo "Starting application..."
exec "$@"
