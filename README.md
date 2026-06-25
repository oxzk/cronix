# Cronix - 定时任务调度系统

基于 FastAPI 构建的轻量级任务调度系统。支持 Cron 表达式调度、命令执行、执行记录追踪和多种通知渠道。

## ✨ 功能特性

### 核心功能
- 📅 **Cron 调度** - 支持标准 5 字段 Cron 表达式
- 🚀 **命令执行** - 通过 Shell 执行任务命令
- 🔔 **智能通知** - 支持多种通知策略（从不/总是/仅失败）
- 📊 **执行监控** - 任务执行历史和状态追踪
- ⏱️ **灵活配置** - 超时控制、失败重试、任务取消
- 📈 **统计分析** - 任务和执行记录统计信息
- 🐳 **容器化部署** - Docker 支持，使用 uv 加速构建
- ⚙️ **系统设置** - 用户和通知配置管理

### 通知渠道
- **Webhook** - 自定义 HTTP 回调
- **Telegram** - Telegram Bot 通知
- **钉钉** - 钉钉机器人通知

### 通知策略
- **从不通知** - 不发送任何通知
- **总是通知** - 每次执行后都发送通知
- **仅失败通知** - 仅在任务失败、超时或取消时通知

## 🚀 快速开始

```bash
# 安装依赖（推荐使用 uv）
uv sync

# 启动服务
uvicorn cronix.main:app --reload
```

### 调度约束

- 当前调度器使用进程内状态管理运行中任务，请使用单进程、单 worker 部署。
- 不要使用多个 uvicorn worker 或多个应用实例同时运行调度器，否则同一任务可能被多个实例同时调度。
- 自动调度按计划时间推进 `next_run_time`：任务到期后先把下一次运行时间推进到未来时间，再启动本次执行；服务停顿后只执行一次到期任务，不补跑所有错过的历史计划点。
- 手动执行不会改变任务的 `next_run_time`。
- 取消任务会终止任务命令所在的子进程组，并把当前执行记录标记为 `cancelled`。

### 使用 Docker

```bash
# 构建镜像（使用 uv 加速）
docker build -t cronix .

# 运行容器
docker run -p 8000:8000 --env-file .env cronix
```

## 🌐 API 端点

### 任务管理
- `GET /api/tasks` - 获取任务列表（支持分页和过滤）
- `POST /api/tasks` - 创建任务
- `GET /api/tasks/{id}` - 获取任务详情
- `PUT /api/tasks/{id}` - 更新任务
- `DELETE /api/tasks/{id}` - 删除任务
- `POST /api/tasks/{id}/execute` - 手动执行任务
- `POST /api/tasks/{id}/cancel` - 取消运行中的任务
- `GET /api/tasks/running/list` - 获取运行中的任务

### 执行记录
- `GET /api/executions` - 获取执行记录列表
- `GET /api/executions/{id}` - 获取执行记录详情

### 认证
- `POST /api/auth/login` - 用户名密码登录
- `GET /api/auth/me` - 获取当前登录用户信息

### 系统设置
- `GET /api/settings/users` - 获取系统用户列表
- `POST /api/settings/users` - 创建系统用户
- `PUT /api/settings/users/{id}` - 更新系统用户
- `DELETE /api/settings/users/{id}` - 删除系统用户
- `GET /api/settings/notifications` - 获取通知配置列表
- `POST /api/settings/notifications` - 创建通知配置
- `PUT /api/settings/notifications/{id}` - 更新通知配置

### 统计信息
- `GET /api/stats/tasks/summary` - 获取任务统计

### 系统
- `GET /health` - 健康检查

## ⚙️ 配置说明

`.env` 环境变量配置：

| 配置项 | 说明 | 默认值 | 必填 |
|--------|------|--------|------|
| `DATABASE_URL` | 数据库连接字符串 | `mysql+aiomysql://user:password@localhost:3306/cronix` | ✅ |
| `APP_DEBUG` | 调试模式 | `False` | ❌ |


## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 开发规范
- 遵循 PEP 8 Python 代码规范
- 使用 TypeScript 进行前端开发
- 提交前运行测试和代码检查
- 编写清晰的提交信息

## 📄 许可证

MIT

## 📮 联系方式

如有问题或建议，请通过 Issue 联系我们。

---

**Cronix** - 让任务调度和脚本管理更简单 🚀
