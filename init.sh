#!/bin/bash
set -e

# Set up the environment
shopt -s nullglob

# Django startup
python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec gunicorn routerfleet.wsgi:application \
  --bind 0.0.0.0:8001 \
  --worker-class sync \
  --workers 5 \
  --timeout 300 \
  --graceful-timeout 30 \
  --max-requests 1000 \
  --max-requests-jitter 200 \
  --log-level info \
  --capture-output \
  --access-logfile - \
  --error-logfile -