#!/usr/bin/env bash
set -e

# Run migrations
python /app/src/manage.py makemigrations

# Run migrations
python /app/src/manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Create superuser if it doesn't exist
python <<'PY'
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from django.contrib.auth import get_user_model

User = get_user_model()
u = os.environ.get('DJANGO_SUPERUSER_USERNAME')
e = os.environ.get('DJANGO_SUPERUSER_EMAIL')
p = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

if not User.objects.filter(username=u).exists():
    User.objects.create_superuser(username=u, email=e, password=p)
    print(f'Created superuser {u}')
else:
    print(f'Superuser {u} already exists; skipping')
PY

# Start Gunicorn
gunicorn config.wsgi:application --chdir /app/src \
    --bind 0.0.0.0:8000 --workers 3 --timeout 60 \
    --access-logfile - --error-logfile -
