# Cronix - 定时任务调度与脚本管理系统

基于 FastAPI 和 React 构建的轻量级、生产就绪的任务调度与脚本管理系统。支持 Cron 表达式调度、脚本管理、依赖安装和多种通知渠道。

## ✨ 功能特性

### 核心功能
- 🔐 **JWT 认证** - 支持双因素认证（2FA/TOTP）
- 📅 **Cron 调度** - 支持标准 5 字段 Cron 表达式
- 🚀 **多执行类型** - Shell、Python、Node.js
- 📝 **脚本管理** - 在线创建、编辑、运行脚本
- 📦 **依赖管理** - Python (uv) 和 Node.js (pnpm) 依赖安装
- 🔔 **智能通知** - 支持多种通知策略（从不/总是/仅失败）
- 📊 **执行监控** - 任务执行历史和状态追踪
- ⏱️ **灵活配置** - 超时控制、失败重试、任务取消
- 📈 **统计分析** - 任务和脚本统计信息
- 🐳 **容器化部署** - Docker 支持，使用 uv 加速构建
- ⚙️ **系统设置** - 通知配置管理、用户设置
- 🎨 **现代化 UI** - 基于 React + Radix UI 的管理界面

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
uv pip install -r requirements.txt

# 或使用传统 pip
pip3 install -r requirements.txt

# 启动服务
python3 main.py
```

### 使用 Docker

```bash
# 构建镜像（使用 uv 加速）
docker build -t cronix .

# 运行容器
docker run -p 8000:8000 --env-file .env cronix
```

## 🌐 API 端点

### 认证
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/logout` - 用户登出
- `GET /api/auth/me` - 获取当前用户信息
- `POST /api/auth/2fa/enable` - 启用 2FA
- `POST /api/auth/2fa/disable` - 禁用 2FA

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

### 脚本管理
- `GET /api/scripts` - 获取脚本树结构
- `GET /api/scripts/{path}` - 获取脚本内容
- `POST /api/scripts` - 创建脚本
- `PUT /api/scripts/{path}` - 更新脚本
- `DELETE /api/scripts/{path}` - 删除脚本
- `POST /api/scripts/{path}/run` - 运行脚本

### 依赖管理
- `GET /api/dependencies` - 获取依赖列表（支持分页和过滤）
- `POST /api/dependencies` - 安装依赖

### 系统设置
- `GET /api/settings/notifications` - 获取通知配置列表
- `POST /api/settings/notifications` - 创建通知配置
- `PUT /api/settings/notifications/{id}` - 更新通知配置
- `DELETE /api/settings/notifications/{id}` - 删除通知配置

### 统计信息
- `GET /api/stats/tasks/summary` - 获取任务统计

### 系统
- `GET /health` - 健康检查
- `GET /info` - 系统信息

## ⚙️ 配置说明

`.env` 环境变量配置：

| 配置项 | 说明 | 默认值 | 必填 |
|--------|------|--------|------|
| `DATABASE_URL` | 数据库连接字符串 | `postgresql://user:password@localhost/cronix` | ✅ |
| `SECRET_KEY` | JWT 密钥（生产环境必须修改） | - | ✅ |
| `ACCESS_TOKEN_EXPIRE_HOURS` | 访问令牌过期时间（小时） | `24` | ❌ |
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
