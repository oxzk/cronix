# Cronix - 定时任务调度系统

基于 FastAPI 和 PostgreSQL 构建的轻量级、生产就绪的任务调度系统。支持 Cron 表达式调度，多种执行类型和通知渠道。

## ✨ 功能特性

- 🔐 **JWT 认证** - 支持双因素认证（2FA/TOTP）
- 📅 **Cron 调度** - 支持秒级精度的 6 字段 Cron 表达式
- 🚀 **多执行类型** - Shell、Python、Node.js
- 🔔 **多渠道通知** - Webhook、Telegram、钉钉
- 📊 **执行监控** - 任务执行历史和状态追踪
- ⏱️ **灵活配置** - 超时控制、失败重试、任务取消
- � **任容器化部署** - Docker 支持
- � *o*系统设置\*\* - 通知配置管理、用户设置

## 🚀 快速开始

### 使用 Docker

```bash
# 构建镜像
docker build -t cronix .

# 运行容器
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

3. **运行应用**

```bash
python main.py
```

应用将在 `http://localhost:8000` 启动

## ⚙️ 配置说明

`.env` 环境变量配置：

```env
DATABASE_URL=postgresql://user:password@localhost:5432/taskmanager
SECRET_KEY=your-secret-key-here-change-in-production
ACCESS_TOKEN_EXPIRE_HOURS=24
APP_NAME=Cronix
APP_PORT=8000
APP_DEBUG=False
```

## 📖 API 文档

### 身份认证

#### 用户登录

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "secure_password"
  }'
```

响应示例：

```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "token_type": "bearer"
}
```

#### 双因素认证登录

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "secure_password",
    "totp_code": "123456"
  }'
```

### 任务管理

#### 创建任务

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
    "notification_ids": [1, 2]
  }'
```

#### 获取任务列表

```bash
# 获取第一页（默认每页50条）
curl -X GET "http://localhost:8000/tasks/" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 指定页码和每页数量
curl -X GET "http://localhost:8000/tasks/?page=2&page_size=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

响应示例：
```json
{
  "items": [
    {
      "id": 1,
      "name": "每日备份",
      "description": "每天午夜备份数据库",
      "cron_expression": "0 0 0 * * *",
      "execution_type": "shell",
      "command": "pg_dump mydb > backup.sql",
      "is_active": true,
      "timeout": 300,
      "retry_count": 2,
      "retry_interval": 60,
      "notifications": null,
      "created_at": "2026-01-23T10:00:00Z",
      "updated_at": "2026-01-23T10:00:00Z"
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 50,
  "total_pages": 2
}
```

#### 获取任务详情

```bash
curl -X GET "http://localhost:8000/tasks/{task_id}" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 更新任务

```bash
curl -X PUT "http://localhost:8000/tasks/{task_id}" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": false
  }'
```

#### 删除任务

```bash
curl -X DELETE "http://localhost:8000/tasks/{task_id}" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 取消正在运行的任务

```bash
curl -X POST "http://localhost:8000/tasks/{task_id}/cancel" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 获取正在运行的任务列表

```bash
curl -X GET "http://localhost:8000/tasks/running/list" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 执行历史管理

#### 获取执行历史列表（支持筛选）

```bash
# 获取所有执行历史（第一页，默认每页50条）
curl -X GET "http://localhost:8000/executions/" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 指定页码和每页数量
curl -X GET "http://localhost:8000/executions/?page=2&page_size=20" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 按任务ID筛选
curl -X GET "http://localhost:8000/executions/?task_id=1" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 按状态筛选
curl -X GET "http://localhost:8000/executions/?status=success" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 组合筛选和分页
curl -X GET "http://localhost:8000/executions/?task_id=1&status=failed&page=1&page_size=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

响应示例：
```json
{
  "items": [
    {
      "id": 1,
      "task_id": 1,
      "started_at": "2026-01-23T10:00:00Z",
      "finished_at": "2026-01-23T10:00:05Z",
      "status": "success",
      "output": "Backup completed successfully",
      "error": null,
      "retry_attempt": 0
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 50,
  "total_pages": 3
}
```

#### 获取单个执行记录详情

```bash
curl -X GET "http://localhost:8000/executions/{execution_id}" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

响应示例：
```json
{
  "id": 1,
  "task_id": 1,
  "task": {
    "id": 1,
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
        "id": 1,
        "notify_type": "webhook",
        "config": {
          "url": "https://hooks.example.com/notify"
        },
        "created_at": "2026-01-23T10:00:00Z",
        "updated_at": "2026-01-23T10:00:00Z"
      }
    ],
    "created_at": "2026-01-23T10:00:00Z",
    "updated_at": "2026-01-23T10:00:00Z"
  },
  "started_at": "2026-01-23T10:00:00Z",
  "finished_at": "2026-01-23T10:00:05Z",
  "status": "success",
  "output": "Backup completed successfully",
  "error": null,
  "retry_attempt": 0
}
```

### 系统设置

#### 获取 2FA 配置信息

```bash
curl -X GET "http://localhost:8000/settings/2fa" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

响应示例：

```json
{
    "totp_secret_key": "JBSWY3DPEHPK3PXP",
    "totp_uri": "otpauth://totp/Cronix:admin?secret=JBSWY3DPEHPK3PXP&issuer=Cronix",
    "is_2fa_enabled": false
}
```

#### 更新用户设置

```bash
# 更新密码
curl -X PUT "http://localhost:8000/settings/user" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "password": "new_password"
  }'

# 启用 2FA
curl -X PUT "http://localhost:8000/settings/user" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "is_2fa_enabled": true,
    "totp_code": "123456"
  }'
```

#### 获取通知配置列表

```bash
curl -X GET "http://localhost:8000/settings/notifications" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

响应示例：

```json
{
    "webhook": {
        "id": 1,
        "url": "https://hooks.example.com/notify"
    },
    "telegram": {
        "id": 2,
        "bot_token": "123456:ABC-DEF...",
        "chat_id": "123456789"
    }
}
```

#### 更新通知配置

```bash
curl -X PUT "http://localhost:8000/settings/notifications/{notification_id}" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "notify_type": "webhook",
    "config": {
      "url": "https://new-webhook-url.com/endpoint"
    }
  }'
```

## ⏰ Cron 表达式格式

Cronix 使用 6 字段的 Cron 表达式（支持秒级精度）：

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

| 表达式           | 说明               |
| ---------------- | ------------------ |
| `0 * * * * *`    | 每分钟执行         |
| `0 0 * * * *`    | 每小时执行         |
| `0 0 0 * * *`    | 每天午夜执行       |
| `0 0 9 * * 1-5`  | 工作日上午9点执行  |
| `0 */15 * * * *` | 每15分钟执行       |
| `0 0 0 1 * *`    | 每月1号执行        |
| `0 30 2 * * 0`   | 每周日凌晨2:30执行 |
| `*/30 * * * * *` | 每30秒执行         |

## 🔧 执行类型

### Shell

直接执行 Shell 命令：

```json
{
    "execution_type": "shell",
    "command": "echo 'Hello World' && date"
}
```

### Python

运行 Python 代码（优先使用 `uv python run`，否则使用 `python`）：

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

## 🔔 通知配置

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

## 📋 任务配置参数

| 字段               | 类型    | 默认值 | 说明                        |
| ------------------ | ------- | ------ | --------------------------- |
| `name`             | string  | 必填   | 任务名称                    |
| `description`      | string  | null   | 任务描述                    |
| `cron_expression`  | string  | 必填   | 6字段 Cron 表达式           |
| `execution_type`   | enum    | 必填   | `shell`、`python` 或 `node` |
| `command`          | string  | 必填   | 要执行的命令                |
| `is_active`        | boolean | true   | 启用/禁用任务               |
| `timeout`          | integer | 300    | 执行超时时间（秒，1-3600）  |
| `retry_count`      | integer | 0      | 失败重试次数（0-5）         |
| `retry_interval`   | integer | 60     | 重试间隔（秒，1-600）       |
| `notification_ids` | array   | null   | 通知配置 ID 列表            |

## 📊 执行状态

任务执行可能处于以下状态之一：

- `pending` - 等待执行
- `running` - 正在执行
- `success` - 执行成功
- `failed` - 执行失败
- `timeout` - 执行超时
- `cancelled` - 已取消

## 🔍 执行历史查询参数

使用 `/executions/` 接口时支持以下查询参数：

| 参数 | 类型 | 说明 |
|------|------|------|
| `task_id` | integer | 按任务ID筛选 |
| `status` | enum | 按状态筛选（`pending`、`running`、`success`、`failed`、`timeout`、`cancelled`） |
| `page` | integer | 页码（从1开始，默认1） |
| `page_size` | integer | 每页数量（1-200，默认50） |

## 📄 分页响应格式

所有支持分页的接口返回统一的分页响应格式：

```json
{
  "items": [],           // 数据列表
  "total": 100,          // 总记录数
  "page": 1,             // 当前页码
  "page_size": 50,       // 每页数量
  "total_pages": 2       // 总页数
}
```

## 🏗️ 项目架构

```
cronix/
├── main.py                 # 应用入口
├── Dockerfile              # Docker 配置
├── requirements.txt        # Python 依赖
├── .env.example            # 环境变量示例
├── logs/                   # 日志目录
└── src/
    ├── __init__.py         # 版本信息
    ├── config.py           # 配置设置
    ├── databases/
    │   ├── db.py           # 数据库连接
    │   └── __init__.py
    ├── models/
    │   ├── schemas.py      # Pydantic 模型
    │   ├── tables.py       # SQLAlchemy 模型
    │   └── __init__.py
    ├── routes/
    │   ├── auth.py         # 认证接口
    │   ├── tasks.py        # 任务管理接口
    │   ├── executions.py   # 执行历史接口
    │   ├── settings.py     # 系统设置接口
    │   └── __init__.py
    ├── services/
    │   ├── auth.py         # JWT 认证服务
    │   ├── scheduler.py    # 任务调度器
    │   ├── notifiers.py    # 通知处理器
    │   └── __init__.py
    ├── middleware/
    │   ├── auth.py         # 认证中间件
    │   └── __init__.py
    └── utils/
        ├── logger.py       # 日志配置
        └── __init__.py
```

## 🛠️ 技术栈

- **FastAPI** (0.128.0) - 现代高性能 Web 框架
- **SQLAlchemy** (2.0.45) - 异步 ORM
- **PostgreSQL** - 关系型数据库
- **asyncpg** (0.30.0) - 异步 PostgreSQL 驱动
- **Croniter** (6.0.0) - Cron 表达式解析器
- **PyJWT** (2.10.1) - JWT 令牌认证
- **Bcrypt** (5.0.0) - 密码哈希
- **PyOTP** (2.9.0) - 双因素认证（TOTP）
- **Aiohttp** (3.11.11) - 异步 HTTP 客户端

## 🔒 安全特性

- JWT 令牌认证
- 双因素认证（2FA/TOTP）支持
- Bcrypt 密码哈希
- 认证中间件保护 API 端点
- 可配置的令牌过期时间

## 📝 日志

应用日志存储在 `logs/` 目录下，按日期命名：

- `logs/app_YYYYMMDD.log`

## 📄 许可证

MIT

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📮 联系方式

如有问题或建议，请通过 Issue 联系我们。
