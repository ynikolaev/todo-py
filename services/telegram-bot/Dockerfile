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
  TZ=America/Adak

WORKDIR /app

COPY --from=builder /app/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt && rm /tmp/requirements.txt

COPY . /app

EXPOSE 8080
CMD ["python","main.py"]