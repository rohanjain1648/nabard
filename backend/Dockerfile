FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml ./
COPY src ./src
RUN uv sync --no-dev

# Pre-generated, deterministic simulator output + trained model artifacts —
# committed to the repo, so the image is demo-ready with no build-time training step.
COPY data ./data
COPY models ./models

EXPOSE 8000
# Render (and similar PaaS) inject $PORT at runtime; fall back to 8000 for
# local `docker compose up`, which maps host 8000 -> container 8000.
CMD ["sh", "-c", "uv run uvicorn cashflow.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
