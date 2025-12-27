#!/bin/bash
set -e

# Set up the environment
shopt -s nullglob

# Django startup
python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec gunicorn routerfleet.wsgi:application --bind 0.0.0.0:8001 --workers 2 --threads 2 --timeout 90 --log-level info --capture-output --access-logfile - --error-logfile -