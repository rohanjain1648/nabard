FROM python:3.11-slim

WORKDIR /app

# lightgbm's compiled extension needs libgomp (OpenMP) at runtime; python:3.11-slim
# doesn't ship it, so `import lightgbm` crashes with "libgomp.so.1: cannot open
# shared object file" without this.
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

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
