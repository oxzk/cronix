# Cronix - 定时任务调度系统

基于 FastAPI 和 PostgreSQL 构建的轻量级、生产就绪的任务调度系统。支持 Cron 表达式调度，多种执行类型和通知渠道。

## 功能特性

- 🔐 JWT 认证，7天令牌有效期
- 📅 基于 Cron 的任务调度（支持秒级6字段格式）
- 🚀 多种执行类型：Shell、Python、Node.js
- 🔔 多渠道通知：Webhook、Telegram、钉钉
- 📊 任务执行历史和监控
- ⏱️ 可配置的超时和重试机制
- 🛑 支持任务取消
- 🐳 Docker 部署

## 快速开始

### 使用 Docker

```bash
docker build -t cronix .
docker run -p 8000:8000 --env-file .env cronix
```

### 本地开发

1. **安装依赖**
```bash
pip install -r requirements.txt
```

2. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件配置你的设置
```

34. **运行应用**
```bash
python main.py
```

应用将在 `http://localhost:8000` 启动

## 配置说明

`.env` 环境变量配置：

```env
DATABASE_URL=postgresql://user:password@localhost:5432/taskmanager
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_HOURS=168
APP_NAME=Cronix
APP_PORT=8000
APP_DEBUG=False
```

## API 使用

### 身份认证

**注册用户**
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "secure_password"}'
```

**用户登录**
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "secure_password"}'
```

响应示例：
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### 任务管理

**创建任务**
```bash
curl -X POST "http://localhost:8000/tasks/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "每日备份",
    "description": "每天午夜备份数据库",
    "cron_expression": "0 0 0 * * *",
    "execution_type": "shell",
    "command": "pg_dump mydb > backup.sql",
    "is_active": true,
    "timeout": 300,
    "retry_count": 2,
    "retry_interval": 60,
    "notifications": [
      {
        "notify_type": "webhook",
        "config": {"url": "https://hooks.example.com/notify"}
      }
    ]
  }'
```

**获取任务列表**
```bash
curl -X GET "http://localhost:8000/tasks/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**获取任务详情**
```bash
curl -X GET "http://localhost:8000/tasks/{task_id}" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**更新任务**
```bash
curl -X PUT "http://localhost:8000/tasks/{task_id}" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'
```

**删除任务**
```bash
curl -X DELETE "http://localhost:8000/tasks/{task_id}" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**获取任务执行历史**
```bash
curl -X GET "http://localhost:8000/tasks/{task_id}/executions" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**取消正在运行的任务**
```bash
curl -X POST "http://localhost:8000/tasks/{task_id}/cancel" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**获取正在运行的任务列表**
```bash
curl -X GET "http://localhost:8000/tasks/running/list" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Cron 表达式格式

Cronix 使用 6 字段的 Cron 表达式：

```
┌───────────── 秒 (0-59)
│ ┌───────────── 分钟 (0-59)
│ │ ┌───────────── 小时 (0-23)
│ │ │ ┌───────────── 日期 (1-31)
│ │ │ │ ┌───────────── 月份 (1-12)
│ │ │ │ │ ┌───────────── 星期 (0-6, 0=星期日)
│ │ │ │ │ │
* * * * * *
```

### 常用示例

| 表达式 | 说明 |
|--------|------|
| `0 * * * * *` | 每分钟执行 |
| `0 0 * * * *` | 每小时执行 |
| `0 0 0 * * *` | 每天午夜执行 |
| `0 0 9 * * 1-5` | 工作日上午9点执行 |
| `0 */15 * * * *` | 每15分钟执行 |
| `0 0 0 1 * *` | 每月1号执行 |
| `0 30 2 * * 0` | 每周日凌晨2:30执行 |

## 执行类型

### Shell
直接执行 Shell 命令：
```json
{
  "execution_type": "shell",
  "command": "echo 'Hello World' && date"
}
```

### Python
运行 Python 代码（如果可用会使用 `uv python run`，否则使用 `python`）：
```json
{
  "execution_type": "python",
  "command": "import datetime\nprint(f'当前时间: {datetime.datetime.now()}')"
}
```

### Node.js
使用 Node.js 执行 JavaScript：
```json
{
  "execution_type": "node",
  "command": "console.log('Hello from Node.js');"
}
```

## 通知配置

### Webhook
```json
{
  "notify_type": "webhook",
  "config": {
    "url": "https://your-webhook-url.com/endpoint"
  }
}
```

### Telegram
```json
{
  "notify_type": "telegram",
  "config": {
    "bot_token": "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
    "chat_id": "123456789"
  }
}
```

### 钉钉
```json
{
  "notify_type": "dingtalk",
  "config": {
    "webhook_url": "https://oapi.dingtalk.com/robot/send?access_token=xxx",
    "secret": "SECxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
  }
}
```

## 任务配置参数

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `name` | string | 必填 | 任务名称 |
| `description` | string | null | 任务描述 |
| `cron_expression` | string | 必填 | 6字段 Cron 表达式 |
| `execution_type` | enum | 必填 | `shell`、`python` 或 `node` |
| `command` | string | 必填 | 要执行的命令 |
| `is_active` | boolean | true | 启用/禁用任务 |
| `timeout` | integer | 300 | 执行超时时间（秒，1-3600） |
| `retry_count` | integer | 0 | 失败重试次数（0-5） |
| `retry_interval` | integer | 60 | 重试间隔（秒，1-600） |
| `notifications` | array | null | 通知配置列表 |

## 项目架构

```
cronix/
├── main.py                 # 应用入口
├── src/
│   ├── config.py          # 配置设置
│   ├── databases/
│   │   └── db.py          # 数据库连接
│   ├── models/
│   │   ├── schemas.py     # Pydantic 模型
│   │   └── tables.py      # SQLAlchemy 模型
│   ├── routes/
│   │   ├── auth.py        # 认证接口
│   │   └── tasks.py       # 任务管理接口
│   ├── services/
│   │   ├── auth.py        # JWT 认证服务
│   │   ├── scheduler.py   # 任务调度器
│   │   └── notifiers.py   # 通知处理器
│   ├── middleware/
│   │   └── auth.py        # 认证中间件
│   └── utils/
│       └── logger.py      # 日志配置
```

## 技术栈

- **FastAPI** - 现代 Web 框架
- **SQLAlchemy** - 异步 ORM
- **PostgreSQL** - 数据库
- **Croniter** - Cron 表达式解析器
- **JWT** - 基于令牌的认证
- **Bcrypt** - 密码哈希
- **Aiohttp** - 异步 HTTP 客户端

## 许可证

MIT
