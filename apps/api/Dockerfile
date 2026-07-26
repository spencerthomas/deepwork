# Deep Work API container for hosted deployment (Railway, etc.).
# Build context is apps/api. The server binds 0.0.0.0:$PORT; the platform
# injects $PORT. All credentials and the access key are read from the
# environment at runtime and are never baked into the image.
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEEPWORK_HOST=0.0.0.0 \
    PORT=8000

WORKDIR /app

# uv for fast, reproducible installs.
RUN pip install --no-cache-dir uv==0.9.7

# Install dependencies first for layer caching, then the package itself.
COPY pyproject.toml README.md ./
COPY src ./src
RUN uv pip install --system --no-cache .

EXPOSE 8000

# deepwork-api reads PORT and DEEPWORK_HOST from the environment.
CMD ["deepwork-api"]
