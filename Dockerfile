FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
COPY uv.lock* ./

RUN pip install --no-cache-dir uv \
    && uv sync --frozen --no-install-project

COPY . .

WORKDIR /app/civic-watchdog

EXPOSE 7860

CMD ["sh", "-c", "uv run uvicorn server:app --host 0.0.0.0 --port ${PORT:-7860}"]
