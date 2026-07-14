FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml ./
COPY src ./src
RUN uv sync --no-dev

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "cashflow.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
