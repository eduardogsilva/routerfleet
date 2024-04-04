#!/bin/bash
set -e

# Set up the environment
shopt -s nullglob

# Django startup
python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec python manage.py runserver 0.0.0.0:8001