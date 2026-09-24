# --- Stage 1: build dependencies into a venv ---
FROM python:3.13-slim AS builder

WORKDIR /app

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt


# --- Stage 2: lean runtime image (no compilers/build tools/pip cache) ---
FROM python:3.13-slim

RUN useradd --create-home --uid 1000 appuser

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY app ./app

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN chown -R appuser:appuser /app
USER appuser

# Hosts like Render assign the listen port via $PORT; default to 8000 for
# local use (docker-compose, plain `docker run`).
ENV PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://localhost:' + os.environ['PORT'] + '/api/teams', timeout=2)" || exit 1

# Shell form so $PORT is expanded at runtime; `exec` keeps uvicorn as PID 1
# so it receives SIGTERM directly and shuts down cleanly.
CMD exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
