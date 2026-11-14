# syntax=docker/dockerfile:1

# ---- 前端构建 ----
FROM node:22-alpine AS web
WORKDIR /web
COPY web/package.json web/package-lock.json* ./
RUN npm install
COPY web/ ./
RUN npm run build

# ---- 运行时 ----
FROM oxzk/debian

# 任务/脚本子进程可直接使用项目 venv 的 python，以及 uv pip install
ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON=3.12 \
    VIRTUAL_ENV="/workspace/.venv" \
    PATH="/workspace/.venv/bin:/root/.local/bin:${PATH}" \
    PORT=8000

# uv 由官方脚本安装到 /root/.local/bin(镜像内无 Python, 由 uv 托管下载)
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh

WORKDIR /workspace

# 依赖层: 只拷贝清单, 源码变更不触发重装
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# 源码层
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
COPY --from=web /web/dist ./web/dist

EXPOSE 8000
# 迁移建表后启动; 监听端口由 PORT 环境变量控制(默认 8000)
CMD ["sh", "-c", "uv run --no-sync alembic upgrade head && exec uv run --no-sync uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
