FROM node:22-slim AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend ./
RUN npm run build

FROM python:3.11-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.11.19 /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

COPY pyproject.toml uv.lock README.md /app/
RUN uv sync --locked --no-dev --no-install-project

COPY src /app/src
COPY --from=frontend-builder /app/frontend/dist /app/public

RUN uv sync --locked --no-dev

EXPOSE 8000

CMD ["uvicorn", "cronix.main:app", "--host", "0.0.0.0", "--port", "8000"]
