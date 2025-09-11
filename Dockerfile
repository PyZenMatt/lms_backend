### Backend Dockerfile (multi-stage)
FROM python:3.11-slim as builder
ARG PIP_NO_CACHE_DIR=true
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
  && rm -rf /var/lib/apt/lists/*

# Copy requirements and install into a wheel dir to leverage cache
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

### Final image
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN useradd --create-home --uid 1000 appuser
WORKDIR /app

# Copy installed packages from builder image
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copy source
COPY . /app

# Static files
RUN mkdir -p /app/staticfiles /app/media && chown -R appuser:appuser /app

USER appuser

ENV PATH="/home/appuser/.local/bin:$PATH"

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
FROM python:3.11-slim

# Basic environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps required for some Python packages (psycopg2, wheel)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gettext \
 && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Ensure staticfiles dir exists and collect static files at build time
RUN mkdir -p /app/staticfiles
# Collect static using base settings (avoid production-time env checks like STRIPE_SECRET_KEY)
# This runs at image build time and should not require production secrets.
RUN DJANGO_SETTINGS_MODULE=schoolplatform.settings.base python manage.py collectstatic --noinput || true

# Entrypoint will run migrations at container start (tolerant to DB not ready)
COPY ./scripts/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 8000

ENV PORT=8000

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
# Use shell form so ${PORT:-8000} is expanded by the shell at runtime
CMD gunicorn schoolplatform.wsgi:application --workers=3 --threads=2 --timeout=120 -b 0.0.0.0:${PORT:-8000}
