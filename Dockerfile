FROM node:20-slim as frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./

RUN npm install

COPY frontend/src ./src
COPY frontend/index.html ./
COPY frontend/vite.config.js ./

RUN npm run build

FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
COPY uv.lock* ./

RUN pip install --no-cache-dir uv \
    && uv sync --frozen --no-install-project

COPY . .

COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

WORKDIR /app/civic-watchdog

EXPOSE 7860

CMD ["sh", "-c", "uv run uvicorn server:app --host 0.0.0.0 --port ${PORT:-7860}"]

