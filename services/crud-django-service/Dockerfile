# ---------- 1) Builder: use Poetry to export requirements ----------
FROM python:3.12-slim AS builder

# Avoid bytecode + ensure clean logs
ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1

# Install Poetry (and minimal tools)
RUN pip install --no-cache-dir "poetry==2.1.3"

WORKDIR /app

COPY pyproject.toml poetry.lock ./

# Export runtime requirements to a plain requirements.txt
RUN poetry self add poetry-plugin-export
RUN poetry export -f requirements.txt --without-hashes -o /app/requirements.txt


# ---------- 2) Final image: slim, fast, no Poetry ----------
FROM python:3.12-slim

# System config
ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  PIP_NO_CACHE_DIR=1 \
  DJANGO_SETTINGS_MODULE=config.settings \
  TZ=America/Adak

RUN apt-get update && apt-get install -y --no-install-recommends \
  tzdata \
  curl \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY --from=builder /app/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt && rm /tmp/requirements.txt

# manage.py is expected in /app/src/manage.py
COPY src /app/src
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
RUN mkdir -p /shared && chown -R appuser:appuser /shared
USER appuser

# Expose Django/Gunicorn port
EXPOSE 8000
WORKDIR /app/src

CMD ["gunicorn", "config.wsgi:application", \
  "--chdir", "/app/src", \
  "--bind", "0.0.0.0:8000", \
  "--workers", "3", "--timeout", "60", \
  "--access-logfile", "-", "--error-logfile", "-"]