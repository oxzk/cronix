# cronix

单机的定时任务管理工具。集中管理 Shell 任务与脚本, 查看执行记录和日志, 配置消息通知, 并监控常用服务的可用状态。

## 环境要求

- `>= Python 3.12+`
- `>= Node.js 22+`

## 快速开始

首次启动会创建管理员账号 `admin`, 并在日志中打印一次随机初始密码, 登录后请立即修改。

### Docker Compose

```bash
cp .env.example .env
# 编辑 .env, 至少修改 JWT__SECRET(不少于 32 字符)
docker compose up -d --build
docker compose logs -f app   # 查看初始密码
```

打开 http://127.0.0.1:8000 。

### Docker 运行

```bash
docker network create cronix

docker run -d --name cronix-db --network cronix \
  -e POSTGRES_USER=cronix \
  -e POSTGRES_PASSWORD=cronix \
  -e POSTGRES_DB=cronix \
  -v cronix-pg:/var/lib/postgresql/data \
  postgres:17

docker run -d --name cronix --network cronix \
  -p 8000:8000 \
  -e JWT__SECRET='替换为不少于32位的随机字符串' \
  -e DATABASE__URL='postgresql+asyncpg://cronix:cronix@cronix-db:5432/cronix' \
  -v cronix-data:/workspace/data \
  ghcr.io/oxzk/cronix:latest

docker logs -f cronix   # 查看初始密码
```

### 源码运行

```bash
cp .env.example .env
# 编辑 .env, 配置 DATABASE__URL 与 JWT__SECRET

uv sync --locked
uv run alembic upgrade head

cd web && npm install && npm run build && cd ..
uv run uvicorn app.main:app --port 8000
```

打开 http://127.0.0.1:8000 。
