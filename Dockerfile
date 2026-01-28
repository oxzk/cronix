FROM node:22-slim

ENV PYTHONUNBUFFERED=1 \
    UV_PYTHON_PREFERENCE=only-managed \
    PATH="/app/.venv/bin:$HOME/.local/bin:$PATH"

WORKDIR /app

COPY . .

RUN apt update && apt install git wget curl ca-certificates -y \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && wget -qO- https://get.pnpm.io/install.sh | ENV="$HOME/.bashrc" SHELL="$(which bash)" bash - \
    && "$HOME/.local/bin/uv" python install 3.11 \
    && "$HOME/.local/bin/uv" sync --no-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

CMD ["sh", "-c", "fastapi run --proxy-headers --host 0.0.0.0 --port ${PORT:-8000}"]
