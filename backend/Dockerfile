# syntax=docker/dockerfile:1
FROM python:3.13-slim

WORKDIR /app

# Copy metadata + source before install: the Hatchling wheel build needs app/ present.
COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir .

EXPOSE 8000

# Liveness healthcheck (compose gates the frontend on this). /health needs no deps.
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=5 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health').status==200 else 1)"

# Stateless ASGI server (AD-9). Config comes from env vars (AD-8).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
