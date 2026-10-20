# ---- Build stage: compile Python packages (mysqlclient needs a compiler) ----
FROM python:3.13-slim AS build

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential pkg-config libmariadb-dev \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r /tmp/requirements.txt


# ---- Runtime stage ----
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=aitherios.settings

RUN apt-get update \
 && apt-get install -y --no-install-recommends libmariadb3 gettext \
 && rm -rf /var/lib/apt/lists/* \
 && useradd --create-home --uid 1000 app

COPY --from=build /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

WORKDIR /app
COPY --chown=app:app . /app

# Build-time steps need a throwaway key; the real one comes from .env at run time.
RUN DJANGO_SECRET_KEY=build-only python manage.py compilemessages \
 && DJANGO_SECRET_KEY=build-only python manage.py collectstatic --noinput \
 && mkdir -p /app/media && chown -R app:app /app/media /app/staticfiles \
 && chmod +x /app/docker/entrypoint.sh

USER app
EXPOSE 8000

ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["gunicorn", "aitherios.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60", "--access-logfile", "-"]
