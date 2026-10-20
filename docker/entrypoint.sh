#!/bin/sh
# Runs every time the web container starts.
set -e

echo "Applying database migrations..."
python manage.py migrate --noinput

# Creates the starting pages on a fresh database; does nothing afterwards.
python manage.py setup_site

exec "$@"
